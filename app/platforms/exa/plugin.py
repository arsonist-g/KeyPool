from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from app.core.auth import verify_project_token
from app.core.db import get_db
from app.core.key_selector import select_key
from app.core.proxy_selector import select_proxy, build_proxy_url
from app.core.session_manager import create_session
from app.platforms.base import PlatformPlugin, QuotaInfo, UpstreamTarget
from app.proxy.sse_proxy import proxy_mcp_request, is_tool_call


EXA_MCP_BASE = "https://mcp.exa.ai"
EXA_API_BASE = "https://api.exa.ai"


class ExaPlugin(PlatformPlugin):

    @property
    def name(self) -> str:
        return "exa"

    def resolve_upstream(self, path: str) -> UpstreamTarget:
        if path == "mcp" or path.startswith("mcp/"):
            return UpstreamTarget(url=f"{EXA_MCP_BASE}/{path}", is_rest=False)
        return UpstreamTarget(url=f"{EXA_API_BASE}/{path}", is_rest=True)

    def inject_key_for_request(
        self, target: UpstreamTarget, key: str, request: Request
    ) -> tuple[str, Optional[dict]]:
        if target.is_rest:
            return target.url, {"x-api-key": key}
        # MCP: 检测客户端使用的认证方式
        if request.headers.get("x-api-key"):
            return target.url, {"x-api-key": key}
        elif request.headers.get("authorization", "").lower().startswith("bearer "):
            return target.url, {"Authorization": f"Bearer {key}"}
        else:
            url = self._inject_key_to_url(target.url, key)
            return url, {"x-api-key": key}

    async def check_quota(self, key: str) -> QuotaInfo:
        return QuotaInfo(remaining=1.0, raw=None)

    def is_key_exhausted(self, status_code: int, response_body: bytes) -> bool:
        return status_code == 429

    def is_key_invalid(self, status_code: int, response_body: bytes) -> bool:
        return status_code == 401

    def get_router(self) -> APIRouter:
        router = APIRouter(tags=["exa"])
        plugin = self

        @router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
        async def proxy_handler(request: Request, path: str = "", db=Depends(get_db)):
            request.state.platform = "exa"
            await verify_project_token(request)

            target = plugin.resolve_upstream(path)

            body = await request.body() if request.method != "GET" else None
            is_usage = target.is_rest or is_tool_call(body)

            key_model = select_key(db, "exa", count=is_usage)
            if key_model is None:
                return Response(
                    content=b'{"error":"no available key"}',
                    status_code=503,
                    media_type="application/json",
                )

            proxy_model = select_proxy(db)
            proxy_url = build_proxy_url(proxy_model) if proxy_model else None

            upstream_url, extra_headers = plugin.inject_key_for_request(
                target, key_model.api_key, request
            )

            if target.is_rest and request.url.query:
                upstream_url = f"{upstream_url}?{request.url.query}"

            if is_usage:
                create_session(db, "exa", key_model.id)

            return await proxy_mcp_request(
                request=request,
                upstream_url=upstream_url,
                proxy_url=proxy_url,
                extra_headers=extra_headers,
            )

        return router

    @staticmethod
    def _inject_key_to_url(upstream_url: str, key: str) -> str:
        parsed = urlparse(upstream_url)
        params = parse_qs(parsed.query)
        params["exaApiKey"] = [key]
        new_query = urlencode(params, doseq=True)
        return str(urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                               parsed.params, new_query, parsed.fragment)))
