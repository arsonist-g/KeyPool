import uuid
from datetime import datetime, UTC

from sqlalchemy.orm import Session as DBSession

from app.core.models import Session


def create_session(db: DBSession, platform: str, key_id: int, proxy_id: int | None = None) -> Session:
    now = datetime.now(UTC)
    session = Session(
        id=uuid.uuid4().hex,
        platform=platform,
        key_id=key_id,
        proxy_id=proxy_id,
        started_at=now,
        last_active_at=now,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def touch_session(db: DBSession, session_id: str) -> None:
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        session.last_active_at = datetime.now(UTC)
        db.commit()


def close_session(db: DBSession, session_id: str) -> None:
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        session.status = "closed"
        db.commit()
        db.expire(session)


def get_active_session(db: DBSession, session_id: str) -> Session | None:
    return db.query(Session).filter(
        Session.id == session_id,
        Session.status == "active",
    ).first()
