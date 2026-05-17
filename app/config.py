import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlatformConfig:
    enabled: bool = True
    upstream_base_url: str = ""


@dataclass
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    admin_key: str = ""
    database: str = "data/keypool.db"
    retry_limit: int = 3
    platforms: dict[str, PlatformConfig] = field(default_factory=dict)


_config: Optional[AppConfig] = None


def load_config(config_path: str = "config.json") -> AppConfig:
    global _config
    path = Path(config_path)
    if not path.exists():
        _config = AppConfig()
        return _config

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    platforms = {}
    for name, pconf in data.get("platforms", {}).items():
        platforms[name] = PlatformConfig(
            enabled=pconf.get("enabled", True),
            upstream_base_url=pconf.get("upstream_base_url", ""),
        )

    _config = AppConfig(
        host=data.get("host", "0.0.0.0"),
        port=data.get("port", 8000),
        admin_key=data.get("admin_key", ""),
        database=data.get("database", "data/keypool.db"),
        retry_limit=data.get("retry_limit", 3),
        platforms=platforms,
    )
    return _config


def get_config() -> AppConfig:
    if _config is None:
        return load_config()
    return _config
