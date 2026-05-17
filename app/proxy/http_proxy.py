from typing import Optional

import httpx
from fastapi import Request, Response

from app.proxy.client import build_httpx_client


async def proxy_http_request(
    request: Request,
    upstream_url: str,
    proxy_url: Optional[str] = None,
    extra_headers: Optional[dict] = None,
) -> Response:
    """HTTP 请求转发：将客户端请求转发到上游并返回响应。

    注意：query params 应由调用方编码到 upstream_url 中，不自动转发客户端的 query params。
    """

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    if extra_headers:
        headers.update(extra_headers)

    body = await request.body()

    client = build_httpx_client(proxy_url=proxy_url)
    try:
        response = await client.request(
            method=request.method,
            url=upstream_url,
            headers=headers,
            content=body if body else None,
        )

        excluded_headers = {"transfer-encoding", "content-encoding", "content-length"}
        resp_headers = {
            k: v for k, v in response.headers.items()
            if k.lower() not in excluded_headers
        }

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=resp_headers,
        )
    except httpx.ConnectError:
        return Response(
            content=b'{"error":"upstream connection failed"}',
            status_code=502,
            media_type="application/json",
        )
    except httpx.TimeoutException:
        return Response(
            content=b'{"error":"upstream timeout"}',
            status_code=504,
            media_type="application/json",
        )
    finally:
        await client.aclose()
