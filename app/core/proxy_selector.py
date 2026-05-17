import random

from sqlalchemy.orm import Session as DBSession

from app.core.models import Proxy


_last_proxy_index = -1


def select_proxy(db: DBSession) -> Proxy | None:
    """轮询选择一个可用出口代理。"""
    global _last_proxy_index

    proxies = db.query(Proxy).filter(Proxy.status == "active").all()
    if not proxies:
        return None

    _last_proxy_index = (_last_proxy_index + 1) % len(proxies)
    return proxies[_last_proxy_index]


def select_next_proxy(db: DBSession, exclude_id: int | None = None) -> Proxy | None:
    """选择下一个代理（排除指定代理，用于重试）。"""
    proxies = db.query(Proxy).filter(Proxy.status == "active").all()
    if not proxies:
        return None

    if exclude_id is not None:
        candidates = [p for p in proxies if p.id != exclude_id]
        if candidates:
            return random.choice(candidates)

    return random.choice(proxies)


def build_proxy_url(proxy: Proxy) -> str:
    """构建代理 URL，如 http://user:pass@host:port"""
    if proxy.username and proxy.password:
        return f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
    return f"{proxy.protocol}://{proxy.host}:{proxy.port}"
