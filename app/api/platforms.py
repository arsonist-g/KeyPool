from fastapi import APIRouter, Depends

from app.config import get_config
from app.core.auth import verify_admin_key
from app.core.schemas import PlatformInfo
from app.platforms import REGISTERED_PLUGINS

router = APIRouter(prefix="/admin/platforms", tags=["platforms"], dependencies=[Depends(verify_admin_key)])


@router.get("", response_model=list[PlatformInfo])
def list_platforms():
    config = get_config()
    result = []
    for plugin in REGISTERED_PLUGINS:
        platform_conf = config.platforms.get(plugin.name)
        enabled = True
        if platform_conf and not platform_conf.enabled:
            enabled = False
        result.append(PlatformInfo(
            name=plugin.name,
            enabled=enabled,
            quota_supported=plugin.supports_quota,
        ))
    return result
