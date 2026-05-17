import asyncio
import logging
from datetime import datetime, UTC

from app.core.db import get_session_local
from app.core.models import Key
from app.platforms import REGISTERED_PLUGINS

logger = logging.getLogger(__name__)

_plugin_map = {p.name: p for p in REGISTERED_PLUGINS}

REFRESH_DELAY_SECONDS = 30 * 60


class QuotaRefreshScheduler:
    """事件驱动的余额刷新调度器。

    key 被使用时调用 schedule_refresh，30 分钟后执行一次性刷新。
    如果该 key 已有待执行任务则跳过（保留最早的调度时间）。
    """

    def __init__(self):
        self._pending: dict[int, asyncio.Task] = {}

    def schedule_refresh(self, key_id: int, platform: str, api_key: str) -> None:
        if key_id in self._pending and not self._pending[key_id].done():
            return
        task = asyncio.create_task(self._delayed_refresh(key_id, platform, api_key))
        self._pending[key_id] = task

    async def _delayed_refresh(self, key_id: int, platform: str, api_key: str) -> None:
        await asyncio.sleep(REFRESH_DELAY_SECONDS)
        try:
            plugin = _plugin_map.get(platform)
            if not plugin:
                return
            quota = await plugin.check_quota(api_key)
            if quota.raw is not None:
                SessionLocal = get_session_local()
                db = SessionLocal()
                try:
                    key = db.query(Key).filter(Key.id == key_id).first()
                    if key:
                        key.quota_remaining = quota.remaining
                        key.quota_updated_at = datetime.now(UTC)
                        db.commit()
                finally:
                    db.close()
        except Exception as e:
            logger.warning(f"Failed to refresh quota for key {key_id}: {e}")
        finally:
            self._pending.pop(key_id, None)

    def cancel_all(self) -> None:
        for task in self._pending.values():
            task.cancel()
        self._pending.clear()


scheduler = QuotaRefreshScheduler()
