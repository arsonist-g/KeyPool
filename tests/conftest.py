"""
KeyPool 测试基础设施。
使用内存 SQLite 数据库，每个测试函数独立隔离。
"""
import os
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

os.environ.setdefault("KEYPOOL_TEST", "1")

TEST_ADMIN_KEY = "test-admin-key"


@pytest.fixture()
def db_engine():
    """创建内存数据库引擎（StaticPool 确保所有连接共享同一个数据库）。"""
    from app.core.db import Base
    from app.core.models import Key, Proxy, Session, ProjectToken  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """每个测试使用独立的数据库 session。"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_engine, db_session):
    """FastAPI TestClient，使用测试数据库和固定 admin_key。"""
    from app.core.db import get_db
    from app.config import AppConfig, PlatformConfig
    import app.core.db as db_module
    import app.config as config_module

    test_config = AppConfig(
        host="0.0.0.0",
        port=8000,
        admin_key=TEST_ADMIN_KEY,
        database=":memory:",
        retry_limit=3,
        platforms={
            "tavily": PlatformConfig(enabled=True, upstream_base_url="https://mcp.tavily.com"),
            "context7": PlatformConfig(enabled=True, upstream_base_url="https://mcp.context7.com"),
            "exa": PlatformConfig(enabled=True, upstream_base_url="https://mcp.exa.ai"),
        },
    )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    old_engine = db_module._engine
    old_session_local = db_module._SessionLocal
    old_config = config_module._config

    db_module._engine = db_engine
    db_module._SessionLocal = TestingSessionLocal
    config_module._config = test_config

    try:
        with patch("app.config.load_config", return_value=test_config):
            with patch("app.core.auth.get_config", return_value=test_config):
                from app.main import create_app
                app = create_app()
                app.dependency_overrides[get_db] = override_get_db
                with TestClient(app) as c:
                    yield c
    finally:
        db_module._engine = old_engine
        db_module._SessionLocal = old_session_local
        config_module._config = old_config
