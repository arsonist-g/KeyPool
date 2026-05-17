from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from app.core.db import get_db
from app.core.auth import verify_admin_key
from app.core.models import Key, Session
from app.core.schemas import PlatformStats

router = APIRouter(prefix="/admin/stats", tags=["stats"], dependencies=[Depends(verify_admin_key)])


@router.get("", response_model=list[PlatformStats])
def get_stats(db: DBSession = Depends(get_db)):
    platforms = db.query(Key.platform).distinct().all()
    result = []

    for (platform,) in platforms:
        keys = db.query(Key).filter(Key.platform == platform).all()
        active_keys = [k for k in keys if k.status == "active"]
        total_requests = sum(k.total_requests for k in keys)
        failed_requests = sum(k.failed_requests for k in keys)

        active_sessions = db.query(func.count(Session.id)).filter(
            Session.platform == platform,
            Session.status == "active",
        ).scalar()

        result.append(PlatformStats(
            platform=platform,
            total_keys=len(keys),
            active_keys=len(active_keys),
            total_requests=total_requests,
            failed_requests=failed_requests,
            active_sessions=active_sessions or 0,
        ))

    return result


@router.get("/quota/overview")
def get_quota_overview(db: DBSession = Depends(get_db)):
    """各平台余额概览：返回每个支持余额查询的平台的 key 余额分布"""
    from app.platforms import REGISTERED_PLUGINS
    supported_platforms = {p.name for p in REGISTERED_PLUGINS if p.supports_quota}

    result = []
    for platform in supported_platforms:
        keys = db.query(Key).filter(
            Key.platform == platform,
            Key.status == "active",
            Key.quota_remaining.isnot(None),
        ).all()
        if not keys:
            result.append({
                "platform": platform,
                "keys": [],
                "avg_remaining": None,
            })
            continue
        key_quotas = [{"id": k.id, "remaining": k.quota_remaining} for k in keys]
        avg = sum(k.quota_remaining for k in keys) / len(keys)
        result.append({
            "platform": platform,
            "keys": key_quotas,
            "avg_remaining": round(avg, 3),
        })
    return result


@router.get("/{platform}", response_model=PlatformStats)
def get_platform_stats(platform: str, db: DBSession = Depends(get_db)):
    keys = db.query(Key).filter(Key.platform == platform).all()
    if not keys:
        return PlatformStats(
            platform=platform,
            total_keys=0,
            active_keys=0,
            total_requests=0,
            failed_requests=0,
            active_sessions=0,
        )

    active_keys = [k for k in keys if k.status == "active"]
    total_requests = sum(k.total_requests for k in keys)
    failed_requests = sum(k.failed_requests for k in keys)

    active_sessions = db.query(func.count(Session.id)).filter(
        Session.platform == platform,
        Session.status == "active",
    ).scalar()

    return PlatformStats(
        platform=platform,
        total_keys=len(keys),
        active_keys=len(active_keys),
        total_requests=total_requests,
        failed_requests=failed_requests,
        active_sessions=active_sessions or 0,
    )
