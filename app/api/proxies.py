from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.core.db import get_db
from app.core.auth import verify_admin_key
from app.core.models import Proxy
from app.core.schemas import ProxyCreate, ProxyUpdate, ProxyResponse, PaginatedResponse

router = APIRouter(prefix="/admin/proxies", tags=["proxies"], dependencies=[Depends(verify_admin_key)])


@router.get("")
def list_proxies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    db: DBSession = Depends(get_db),
):
    query = db.query(Proxy)
    total = query.count()
    items = query.order_by(Proxy.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse[ProxyResponse](items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ProxyResponse, status_code=201)
def create_proxy(data: ProxyCreate, db: DBSession = Depends(get_db)):
    existing = db.query(Proxy).filter(Proxy.host == data.host, Proxy.port == data.port).first()
    if existing:
        raise HTTPException(status_code=409, detail="Proxy with same host:port already exists")
    proxy = Proxy(
        protocol=data.protocol,
        host=data.host,
        port=data.port,
        username=data.username,
        password=data.password,
    )
    db.add(proxy)
    db.commit()
    db.refresh(proxy)
    return proxy


@router.get("/{proxy_id}", response_model=ProxyResponse)
def get_proxy(proxy_id: int, db: DBSession = Depends(get_db)):
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return proxy


@router.patch("/{proxy_id}", response_model=ProxyResponse)
def update_proxy(proxy_id: int, data: ProxyUpdate, db: DBSession = Depends(get_db)):
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(proxy, field, value)
    db.commit()
    db.refresh(proxy)
    return proxy


@router.delete("/{proxy_id}", status_code=204)
def delete_proxy(proxy_id: int, db: DBSession = Depends(get_db)):
    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    db.delete(proxy)
    db.commit()
