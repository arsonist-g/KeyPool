"""Key 选择器（加权随机）测试。"""
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.core.models import Key
from app.core.key_selector import (
    calculate_effective_weight,
    select_key,
    mark_key_failed,
    mark_key_exhausted,
    mark_key_invalid,
)


@pytest.fixture()
def selector_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    yield db
    db.close()
    engine.dispose()


class TestEffectiveWeight:
    def test_new_key_full_weight(self):
        key = Key(weight=2.0, total_requests=0, failed_requests=0)
        assert calculate_effective_weight(key) == 2.0

    def test_half_error_rate(self):
        key = Key(weight=2.0, total_requests=10, failed_requests=5)
        assert calculate_effective_weight(key) == 1.0

    def test_with_quota_factor(self):
        key = Key(weight=2.0, total_requests=0, failed_requests=0)
        assert calculate_effective_weight(key, quota_factor=0.5) == 1.0

    def test_all_failed(self):
        key = Key(weight=1.0, total_requests=10, failed_requests=10)
        assert calculate_effective_weight(key) == 0.0


class TestSelectKey:
    def _seed_keys(self, db, platform="tavily", count=3):
        keys = []
        for i in range(count):
            k = Key(platform=platform, api_key=f"key-{i}", weight=1.0)
            db.add(k)
            keys.append(k)
        db.commit()
        return keys

    @patch("app.core.key_selector.asyncio.get_event_loop")
    def test_select_from_active_keys(self, mock_loop, selector_db):
        mock_loop.side_effect = RuntimeError("no loop")
        self._seed_keys(selector_db)
        key = select_key(selector_db, "tavily")
        assert key is not None
        assert key.platform == "tavily"
        assert key.total_requests == 1

    @patch("app.core.key_selector.asyncio.get_event_loop")
    def test_select_returns_none_when_no_keys(self, mock_loop, selector_db):
        mock_loop.side_effect = RuntimeError("no loop")
        key = select_key(selector_db, "tavily")
        assert key is None

    @patch("app.core.key_selector.asyncio.get_event_loop")
    def test_select_skips_non_active_keys(self, mock_loop, selector_db):
        mock_loop.side_effect = RuntimeError("no loop")
        keys = self._seed_keys(selector_db)
        keys[0].status = "disabled"
        keys[1].status = "exhausted"
        selector_db.commit()
        selected = select_key(selector_db, "tavily")
        assert selected is not None
        assert selected.id == keys[2].id

    @patch("app.core.key_selector.asyncio.get_event_loop")
    def test_weighted_selection_distribution(self, mock_loop, selector_db):
        """高权重 key 应该被选中更多次。"""
        mock_loop.side_effect = RuntimeError("no loop")
        k1 = Key(platform="tavily", api_key="heavy", weight=10.0)
        k2 = Key(platform="tavily", api_key="light", weight=0.1)
        selector_db.add_all([k1, k2])
        selector_db.commit()

        counts = {k1.id: 0, k2.id: 0}
        for _ in range(100):
            selected = select_key(selector_db, "tavily")
            counts[selected.id] += 1

        assert counts[k1.id] > counts[k2.id]

    @patch("app.core.key_selector.asyncio.get_event_loop")
    def test_minimum_weight_floor(self, mock_loop, selector_db):
        """即使权重计算为 0，最低 floor 0.01 保证 key 仍有机会被选中。"""
        mock_loop.side_effect = RuntimeError("no loop")
        k = Key(platform="tavily", api_key="all-failed", weight=1.0,
                total_requests=100, failed_requests=100)
        selector_db.add(k)
        selector_db.commit()
        selected = select_key(selector_db, "tavily")
        assert selected is not None


class TestMarkKeyState:
    def _create_key(self, db):
        k = Key(platform="tavily", api_key="state-test", weight=1.0)
        db.add(k)
        db.commit()
        return k

    def test_mark_failed(self, selector_db):
        k = self._create_key(selector_db)
        mark_key_failed(selector_db, k)
        assert k.failed_requests == 1

    def test_mark_exhausted(self, selector_db):
        k = self._create_key(selector_db)
        mark_key_exhausted(selector_db, k)
        assert k.status == "exhausted"

    def test_mark_invalid(self, selector_db):
        k = self._create_key(selector_db)
        mark_key_invalid(selector_db, k)
        assert k.status == "disabled"
