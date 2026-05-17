from datetime import datetime, UTC

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Key(Base):
    __tablename__ = "keys"
    __table_args__ = (
        UniqueConstraint("platform", "api_key", name="uq_platform_api_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), index=True)
    api_key: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    quota_remaining: Mapped[float | None] = mapped_column(Float, nullable=True)
    quota_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Proxy(Base):
    __tablename__ = "proxies"
    __table_args__ = (
        UniqueConstraint("host", "port", name="uq_proxy_host_port"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    protocol: Mapped[str] = mapped_column(String(10))
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    platform: Mapped[str] = mapped_column(String(50), index=True)
    key_id: Mapped[int] = mapped_column(Integer, ForeignKey("keys.id"))
    proxy_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("proxies.id"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String(20), default="active")


class ProjectToken(Base):
    __tablename__ = "project_tokens"
    __table_args__ = (
        UniqueConstraint("name", name="uq_token_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    token_value: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    allowed_platforms: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
