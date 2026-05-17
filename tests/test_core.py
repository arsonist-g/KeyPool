"""Proxy 选择器和 Session 管理器测试。"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.core.models import Key, Proxy, Session
from app.core.proxy_selector import select_proxy, select_next_proxy, build_proxy_url
from app.core.session_manager import create_session, touch_session, close_session, get_active_session


@pytest.fixture()
def core_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    engine.dispose()


class TestProxySelector:
    def _seed_proxies(self, db, count=3):
        proxies = []
        for i in range(count):
            p = Proxy(protocol="http", host=f"proxy-{i}.test", port=8080 + i)
            db.add(p)
            proxies.append(p)
        db.commit()
        return proxies

    def test_select_proxy_none_when_empty(self, core_db):
        assert select_proxy(core_db) is None

    def test_select_proxy_round_robin(self, core_db):
        import app.core.proxy_selector as ps
        ps._last_proxy_index = -1

        proxies = self._seed_proxies(core_db)
        selected = [select_proxy(core_db) for _ in range(6)]
        hosts = [p.host for p in selected]
        assert hosts == [
            "proxy-0.test", "proxy-1.test", "proxy-2.test",
            "proxy-0.test", "proxy-1.test", "proxy-2.test",
        ]

    def test_select_proxy_skips_disabled(self, core_db):
        import app.core.proxy_selector as ps
        ps._last_proxy_index = -1

        proxies = self._seed_proxies(core_db)
        proxies[1].status = "disabled"
        core_db.commit()
        selected = select_proxy(core_db)
        assert selected.host in ("proxy-0.test", "proxy-2.test")

    def test_select_next_proxy_excludes_id(self, core_db):
        proxies = self._seed_proxies(core_db)
        for _ in range(20):
            p = select_next_proxy(core_db, exclude_id=proxies[0].id)
            assert p.id != proxies[0].id


class TestBuildProxyUrl:
    def test_without_auth(self, core_db):
        p = Proxy(protocol="http", host="example.com", port=8080)
        assert build_proxy_url(p) == "http://example.com:8080"

    def test_with_auth(self, core_db):
        p = Proxy(protocol="socks5", host="example.com", port=1080,
                  username="user", password="pass")
        assert build_proxy_url(p) == "socks5://user:pass@example.com:1080"


class TestSessionManager:
    def _create_key(self, db):
        k = Key(platform="tavily", api_key="session-test-key", weight=1.0)
        db.add(k)
        db.commit()
        return k

    def test_create_session(self, core_db):
        key = self._create_key(core_db)
        session = create_session(core_db, "tavily", key.id)
        assert session.platform == "tavily"
        assert session.key_id == key.id
        assert session.status == "active"
        assert len(session.id) == 32

    def test_touch_session(self, core_db):
        key = self._create_key(core_db)
        session = create_session(core_db, "tavily", key.id)
        old_time = session.last_active_at
        import time
        time.sleep(0.01)
        touch_session(core_db, session.id)
        core_db.refresh(session)
        assert session.last_active_at >= old_time

    def test_close_session(self, core_db):
        key = self._create_key(core_db)
        session = create_session(core_db, "tavily", key.id)
        close_session(core_db, session.id)
        core_db.refresh(session)
        assert session.status == "closed"

    def test_get_active_session(self, core_db):
        key = self._create_key(core_db)
        session = create_session(core_db, "tavily", key.id)
        found = get_active_session(core_db, session.id)
        assert found is not None
        assert found.id == session.id

    def test_get_active_session_not_found_after_close(self, core_db):
        key = self._create_key(core_db)
        session = create_session(core_db, "tavily", key.id)
        close_session(core_db, session.id)
        found = get_active_session(core_db, session.id)
        assert found is None
