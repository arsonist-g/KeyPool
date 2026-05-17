from datetime import datetime
from typing import Optional, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


# ===== Key Schemas =====

class KeyCreate(BaseModel):
    platform: str
    api_key: str
    weight: float = 1.0


class KeyUpdate(BaseModel):
    weight: Optional[float] = None
    status: Optional[str] = None


class KeyResponse(BaseModel):
    id: int
    platform: str
    api_key: str
    weight: float
    status: str
    total_requests: int
    failed_requests: int
    last_used_at: Optional[datetime]
    quota_remaining: Optional[float] = None
    quota_updated_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== Proxy Schemas =====

class ProxyCreate(BaseModel):
    protocol: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None


class ProxyUpdate(BaseModel):
    protocol: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None


class ProxyResponse(BaseModel):
    id: int
    protocol: str
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== Session Schemas =====

class SessionResponse(BaseModel):
    id: str
    platform: str
    key_id: int
    proxy_id: Optional[int]
    started_at: datetime
    last_active_at: datetime
    status: str

    model_config = {"from_attributes": True}


# ===== Stats Schemas =====

class PlatformStats(BaseModel):
    platform: str
    total_keys: int
    active_keys: int
    total_requests: int
    failed_requests: int
    active_sessions: int


# ===== Project Token Schemas =====

class TokenCreate(BaseModel):
    name: str
    allowed_platforms: list[str]


class TokenUpdate(BaseModel):
    name: Optional[str] = None
    allowed_platforms: Optional[list[str]] = None
    status: Optional[str] = None


class TokenResponse(BaseModel):
    id: int
    name: str
    token_value: str
    allowed_platforms: list[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== Platform Schemas =====

class PlatformInfo(BaseModel):
    name: str
    enabled: bool
    quota_supported: bool = False
