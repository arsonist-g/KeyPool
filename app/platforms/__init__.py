from typing import Optional

from app.platforms.base import PlatformPlugin
from app.platforms.context7 import Context7Plugin
from app.platforms.exa import ExaPlugin
from app.platforms.tavily import TavilyPlugin


REGISTERED_PLUGINS: list[PlatformPlugin] = [
    TavilyPlugin(),
    ExaPlugin(),
    Context7Plugin(),
]


def get_plugin(name: str) -> Optional[PlatformPlugin]:
    for plugin in REGISTERED_PLUGINS:
        if plugin.name == name:
            return plugin
    return None


def get_enabled_plugins(enabled_platforms: dict) -> list[PlatformPlugin]:
    """根据配置过滤出已启用的插件。"""
    result = []
    for p in REGISTERED_PLUGINS:
        conf = enabled_platforms.get(p.name)
        if conf is None or not hasattr(conf, "enabled") or conf.enabled:
            result.append(p)
    return result
