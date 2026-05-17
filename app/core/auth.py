from fastapi import Request, HTTPException

from app.config import get_config


def _extract_token(request: Request) -> str:
    token = request.query_params.get("token")
    if token:
        return token

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    return ""


async def verify_admin_key(request: Request) -> None:
    """管理接口鉴权：验证 admin_key。"""
    config = get_config()
    if not config.admin_key:
        return

    token = _extract_token(request)
    if token != config.admin_key:
        raise HTTPException(status_code=401, detail="Invalid or missing admin key")


async def verify_project_token(request: Request) -> None:
    """代理接口鉴权：验证项目 Token 并检查平台权限。

    需要在路由中通过 request.state.platform 传入当前平台名。
    """
    from app.core.db import get_session_local
    from app.core.models import ProjectToken
    import json

    token_value = _extract_token(request)
    if not token_value:
        raise HTTPException(status_code=401, detail="Missing project token")

    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        token_record = db.query(ProjectToken).filter(
            ProjectToken.token_value == token_value,
            ProjectToken.status == "active",
        ).first()

        if not token_record:
            raise HTTPException(status_code=401, detail="Invalid project token")

        platform = getattr(request.state, "platform", None)
        if platform:
            allowed = json.loads(token_record.allowed_platforms)
            if platform not in allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Token not authorized for platform: {platform}",
                )
    finally:
        db.close()
