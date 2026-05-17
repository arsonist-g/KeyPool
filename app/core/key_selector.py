import asyncio
import random
from datetime import datetime, UTC

from sqlalchemy.orm import Session as DBSession

from app.core.models import Key


def calculate_effective_weight(key: Key, quota_factor: float = 1.0) -> float:
    if key.total_requests == 0:
        error_rate = 0.0
    else:
        error_rate = key.failed_requests / key.total_requests

    return key.weight * (1 - error_rate) * quota_factor


def select_key(db: DBSession, platform: str, quota_factors: dict[int, float] | None = None, count: bool = True) -> Key | None:
    """加权随机选择一个可用 key。

    quota_factors: {key_id: factor} 来自平台额度查询，0.0~1.0
    如果未提供，则使用数据库中持久化的 quota_remaining 值
    count: 是否计入 total_requests（仅对实际工具调用为 True）
    """
    keys = db.query(Key).filter(
        Key.platform == platform,
        Key.status == "active",
    ).all()

    if not keys:
        return None

    if quota_factors is None:
        quota_factors = {
            key.id: key.quota_remaining
            for key in keys
            if key.quota_remaining is not None
        }

    weights = []
    for key in keys:
        factor = quota_factors.get(key.id, 1.0)
        w = calculate_effective_weight(key, factor)
        weights.append(max(w, 0.01))

    selected = random.choices(keys, weights=weights, k=1)[0]

    selected.last_used_at = datetime.now(UTC)
    if count:
        selected.total_requests += 1
    db.commit()

    try:
        from app.core.quota_scheduler import scheduler
        loop = asyncio.get_event_loop()
        if loop.is_running():
            scheduler.schedule_refresh(selected.id, selected.platform, selected.api_key)
    except Exception:
        pass

    return selected


def mark_key_failed(db: DBSession, key: Key) -> None:
    key.failed_requests += 1
    db.commit()


def mark_key_exhausted(db: DBSession, key: Key) -> None:
    key.status = "exhausted"
    db.commit()


def mark_key_invalid(db: DBSession, key: Key) -> None:
    key.status = "disabled"
    db.commit()
