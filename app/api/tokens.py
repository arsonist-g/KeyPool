import json
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from app.core.db import get_db
from app.core.auth import verify_admin_key
from app.core.models import ProjectToken
from app.core.schemas import TokenCreate, TokenUpdate, TokenResponse, PaginatedResponse

router = APIRouter(prefix="/admin/tokens", tags=["tokens"], dependencies=[Depends(verify_admin_key)])


def _token_to_response(token: ProjectToken) -> dict:
    data = {
        "id": token.id,
        "name": token.name,
        "token_value": token.token_value,
        "allowed_platforms": json.loads(token.allowed_platforms),
        "status": token.status,
        "created_at": token.created_at,
    }
    return data


@router.get("")
def list_tokens(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: DBSession = Depends(get_db),
):
    query = db.query(ProjectToken)
    total = query.count()
    items = query.order_by(ProjectToken.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_token_to_response(t) for t in items], "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=TokenResponse, status_code=201)
def create_token(data: TokenCreate, db: DBSession = Depends(get_db)):
    existing = db.query(ProjectToken).filter(ProjectToken.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Token name already exists")
    token = ProjectToken(
        name=data.name,
        token_value=secrets.token_hex(32),
        allowed_platforms=json.dumps(data.allowed_platforms),
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return _token_to_response(token)


@router.get("/{token_id}", response_model=TokenResponse)
def get_token(token_id: int, db: DBSession = Depends(get_db)):
    token = db.query(ProjectToken).filter(ProjectToken.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return _token_to_response(token)


@router.patch("/{token_id}", response_model=TokenResponse)
def update_token(token_id: int, data: TokenUpdate, db: DBSession = Depends(get_db)):
    token = db.query(ProjectToken).filter(ProjectToken.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    if data.name is not None:
        conflict = db.query(ProjectToken).filter(ProjectToken.name == data.name, ProjectToken.id != token_id).first()
        if conflict:
            raise HTTPException(status_code=409, detail="Token name already exists")
        token.name = data.name
    if data.allowed_platforms is not None:
        token.allowed_platforms = json.dumps(data.allowed_platforms)
    if data.status is not None:
        token.status = data.status
    db.commit()
    db.refresh(token)
    return _token_to_response(token)


@router.delete("/{token_id}", status_code=204)
def delete_token(token_id: int, db: DBSession = Depends(get_db)):
    token = db.query(ProjectToken).filter(ProjectToken.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    db.delete(token)
    db.commit()
