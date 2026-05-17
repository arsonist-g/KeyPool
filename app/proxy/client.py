import httpx
from typing import Optional

# 共享连接池客户端：按 proxy_url 缓存，复用 TCP/TLS 连接
_shared_clients: dict[Optional[str], httpx.AsyncClient] = {}


def get_shared_client(proxy_url: Optional[str] = None) -> httpx.AsyncClient:
    """获取共享的连接池客户端，避免每次请求都重新建立 TCP/TLS。"""
    if proxy_url not in _shared_clients:
        kwargs = {
            "http2": True,
            "timeout": httpx.Timeout(300.0, connect=15.0, read=300.0),
            "follow_redirects": True,
            "limits": httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20,
                keepalive_expiry=120,
            ),
        }
        if proxy_url:
            kwargs["proxy"] = proxy_url
        _shared_clients[proxy_url] = httpx.AsyncClient(**kwargs)
    return _shared_clients[proxy_url]


async def close_shared_clients():
    """关闭所有共享客户端（应用关闭时调用）。"""
    for client in _shared_clients.values():
        await client.aclose()
    _shared_clients.clear()


def build_httpx_client(
    proxy_url: Optional[str] = None,
    timeout: float = 30.0,
) -> httpx.AsyncClient:
    """构建支持代理的异步 HTTP 客户端。"""
    kwargs = {
        "timeout": httpx.Timeout(timeout, connect=20.0),
        "follow_redirects": True,
    }
    if proxy_url:
        kwargs["proxy"] = proxy_url
    return httpx.AsyncClient(**kwargs)


def build_httpx_stream_client(
    proxy_url: Optional[str] = None,
    timeout: float = 300.0,
) -> httpx.AsyncClient:
    """构建用于 SSE 长连接的异步 HTTP 客户端。"""
    kwargs = {
        "timeout": httpx.Timeout(timeout, connect=30.0, read=300.0),
        "follow_redirects": True,
    }
    if proxy_url:
        kwargs["proxy"] = proxy_url
    return httpx.AsyncClient(**kwargs)
