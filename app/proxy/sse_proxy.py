from typing import Optional, AsyncGenerator
import json

import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse, Response

from app.proxy.client import get_shared_client

PASSTHROUGH_HEADERS = ("mcp-session-id",)

# 只有这些 method 算作实际使用（消耗配额的请求）
USAGE_METHODS = ("tools/call",)


def is_tool_call(body: bytes | None) -> bool:
    """判断请求体是否为 tools/call 调用。"""
    if not body:
        return False
    try:
        data = json.loads(body)
        if isinstance(data, list):
            return any(item.get("method") in USAGE_METHODS for item in data if isinstance(item, dict))
        return data.get("method") in USAGE_METHODS
    except (json.JSONDecodeError, AttributeError):
        return False


async def proxy_mcp_request(
    request: Request,
    upstream_url: str,
    proxy_url: Optional[str] = None,
    extra_headers: Optional[dict] = None,
) -> StreamingResponse | Response:
    """统一 MCP 代理：透传上游的原始 content-type 和响应体。

    使用共享连接池客户端，复用 TCP/TLS 连接以减少延迟。
    支持 SSE 和 Streamable HTTP 两种协议——不预设响应格式，
    由上游决定返回 text/event-stream 还是 application/json。
    """

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers.pop("authorization", None)
    if extra_headers:
        headers.update(extra_headers)

    body = await request.body() if request.method != "GET" else None
    client = get_shared_client(proxy_url)

    try:
        resp = await client.send(
            client.build_request(
                method=request.method,
                url=upstream_url,
                headers=headers,
                content=body,
            ),
            stream=True,
        )
    except (httpx.ConnectError, httpx.TimeoutException):
        return JSONResponse(
            content={"error": "upstream connection failed"},
            status_code=502,
        )

    content_type = resp.headers.get("content-type", "application/json")
    resp_headers = {"Cache-Control": "no-cache"}
    for h in PASSTHROUGH_HEADERS:
        if h in resp.headers:
            resp_headers[h] = resp.headers[h]

    if "text/event-stream" in content_type:
        async def stream_sse() -> AsyncGenerator[bytes, None]:
            try:
                async for chunk in resp.aiter_bytes():
                    yield chunk
            finally:
                await resp.aclose()

        return StreamingResponse(
            stream_sse(),
            status_code=resp.status_code,
            media_type=content_type,
            headers={**resp_headers, "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    # 非流式响应（JSON-RPC 等）：读取完整 body 后返回
    body_bytes = await resp.aread()
    await resp.aclose()

    return Response(
        content=body_bytes,
        status_code=resp.status_code,
        media_type=content_type,
        headers=resp_headers,
    )


# 向后兼容别名
proxy_sse_connection = proxy_mcp_request
proxy_streamable_http = proxy_mcp_request
