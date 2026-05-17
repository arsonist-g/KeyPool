from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_config

router = APIRouter(prefix="/admin/auth", tags=["auth"])


class LoginRequest(BaseModel):
    admin_key: str


class LoginResponse(BaseModel):
    success: bool
    token: str


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    config = get_config()
    if data.admin_key != config.admin_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return LoginResponse(success=True, token=config.admin_key)
