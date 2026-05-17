from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.core.db import get_db
from app.core.auth import verify_admin_key
from app.core.models import Key
from app.core.schemas import KeyCreate, KeyUpdate, KeyResponse, PaginatedResponse
from app.platforms import REGISTERED_PLUGINS

router = APIRouter(prefix="/admin/keys", tags=["keys"], dependencies=[Depends(verify_admin_key)])

_plugin_map = {p.name: p for p in REGISTERED_PLUGINS}


@router.get("")
def list_keys(
    platform: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: DBSession = Depends(get_db),
):
    query = db.query(Key)
    if platform:
        query = query.filter(Key.platform == platform)
    if status:
        query = query.filter(Key.status == status)
    total = query.count()
    items = query.order_by(Key.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse[KeyResponse](items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=KeyResponse, status_code=201)
def create_key(data: KeyCreate, db: DBSession = Depends(get_db)):
    existing = db.query(Key).filter(
        Key.platform == data.platform,
        Key.api_key == data.api_key,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Key already exists for this platform")
    key = Key(
        platform=data.platform,
        api_key=data.api_key,
        weight=data.weight,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


@router.get("/{key_id}", response_model=KeyResponse)
def get_key(key_id: int, db: DBSession = Depends(get_db)):
    key = db.query(Key).filter(Key.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.patch("/{key_id}", response_model=KeyResponse)
def update_key(key_id: int, data: KeyUpdate, db: DBSession = Depends(get_db)):
    key = db.query(Key).filter(Key.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    if data.weight is not None:
        key.weight = data.weight
    if data.status is not None:
        key.status = data.status
    db.commit()
    db.refresh(key)
    return key


@router.delete("/{key_id}", status_code=204)
def delete_key(key_id: int, db: DBSession = Depends(get_db)):
    key = db.query(Key).filter(Key.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    db.delete(key)
    db.commit()


@router.get("/{key_id}/quota")
async def get_key_quota(key_id: int, db: DBSession = Depends(get_db)):
    key = db.query(Key).filter(Key.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    plugin = _plugin_map.get(key.platform)
    if not plugin:
        return {"supported": False, "remaining": None, "raw": None}
    try:
        quota = await plugin.check_quota(key.api_key)
    except Exception:
        return {"supported": False, "remaining": None, "raw": None, "error": "upstream_unreachable"}
    supported = quota.raw is not None
    if supported:
        key.quota_remaining = quota.remaining
        key.quota_updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(key)
    return {"supported": supported, "remaining": quota.remaining, "raw": quota.raw}
