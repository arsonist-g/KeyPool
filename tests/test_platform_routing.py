"""平台插件路由、key 注入、使用计数测试。"""
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request

from app.platforms.tavily.plugin import TavilyPlugin
from app.platforms.context7.plugin import Context7Plugin
from app.platforms.exa.plugin import ExaPlugin
from app.platforms.base import UpstreamTarget
from app.proxy.sse_proxy import is_tool_call


# ---------- is_tool_call ----------

class TestIsToolCall:
    def test_tools_call_returns_true(self):
        body = json.dumps({"jsonrpc": "2.0", "method": "tools/call", "id": 1}).encode()
        assert is_tool_call(body) is True

    def test_initialize_returns_false(self):
        body = json.dumps({"jsonrpc": "2.0", "method": "initialize", "id": 1}).encode()
        assert is_tool_call(body) is False

    def test_tools_list_returns_false(self):
        body = json.dumps({"jsonrpc": "2.0", "method": "tools/list", "id": 1}).encode()
        assert is_tool_call(body) is False

    def test_notification_returns_false(self):
        body = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode()
        assert is_tool_call(body) is False

    def test_empty_body_returns_false(self):
        assert is_tool_call(None) is False
        assert is_tool_call(b"") is False

    def test_invalid_json_returns_false(self):
        assert is_tool_call(b"not json") is False

    def test_batch_with_tool_call(self):
        body = json.dumps([
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "method": "tools/call", "id": 2},
        ]).encode()
        assert is_tool_call(body) is True

    def test_batch_without_tool_call(self):
        body = json.dumps([
            {"jsonrpc": "2.0", "method": "initialize", "id": 1},
            {"jsonrpc": "2.0", "method": "tools/list", "id": 2},
        ]).encode()
        assert is_tool_call(body) is False


# ---------- resolve_upstream ----------

class TestTavilyResolveUpstream:
    def setup_method(self):
        self.plugin = TavilyPlugin()

    def test_mcp_path(self):
        target = self.plugin.resolve_upstream("mcp")
        assert target.url == "https://mcp.tavily.com/mcp"
        assert target.is_rest is False

    def test_mcp_subpath(self):
        target = self.plugin.resolve_upstream("mcp/some/path")
        assert target.url == "https://mcp.tavily.com/mcp/some/path"
        assert target.is_rest is False

    def test_search_rest(self):
        target = self.plugin.resolve_upstream("search")
        assert target.url == "https://api.tavily.com/search"
        assert target.is_rest is True

    def test_extract_rest(self):
        target = self.plugin.resolve_upstream("extract")
        assert target.url == "https://api.tavily.com/extract"
        assert target.is_rest is True

    def test_usage_rest(self):
        target = self.plugin.resolve_upstream("usage")
        assert target.url == "https://api.tavily.com/usage"
        assert target.is_rest is True


class TestContext7ResolveUpstream:
    def setup_method(self):
        self.plugin = Context7Plugin()

    def test_mcp_path(self):
        target = self.plugin.resolve_upstream("mcp")
        assert target.url == "https://mcp.context7.com/mcp"
        assert target.is_rest is False

    def test_rest_api_v2(self):
        target = self.plugin.resolve_upstream("api/v2/libs/search")
        assert target.url == "https://context7.com/api/v2/libs/search"
        assert target.is_rest is True

    def test_rest_context(self):
        target = self.plugin.resolve_upstream("api/v2/context")
        assert target.url == "https://context7.com/api/v2/context"
        assert target.is_rest is True


class TestExaResolveUpstream:
    def setup_method(self):
        self.plugin = ExaPlugin()

    def test_mcp_path(self):
        target = self.plugin.resolve_upstream("mcp")
        assert target.url == "https://mcp.exa.ai/mcp"
        assert target.is_rest is False

    def test_search_rest(self):
        target = self.plugin.resolve_upstream("search")
        assert target.url == "https://api.exa.ai/search"
        assert target.is_rest is True

    def test_contents_rest(self):
        target = self.plugin.resolve_upstream("contents")
        assert target.url == "https://api.exa.ai/contents"
        assert target.is_rest is True

    def test_answer_rest(self):
        target = self.plugin.resolve_upstream("answer")
        assert target.url == "https://api.exa.ai/answer"
        assert target.is_rest is True


# ---------- inject_key_for_request ----------

def _make_request(headers: dict = None) -> MagicMock:
    req = MagicMock(spec=Request)
    req.headers = headers or {}
    return req


class TestTavilyInjectKey:
    def setup_method(self):
        self.plugin = TavilyPlugin()

    def test_rest_always_bearer(self):
        target = UpstreamTarget(url="https://api.tavily.com/search", is_rest=True)
        req = _make_request()
        url, headers = self.plugin.inject_key_for_request(target, "key123", req)
        assert url == "https://api.tavily.com/search"
        assert headers == {"Authorization": "Bearer key123"}

    def test_mcp_with_bearer_client(self):
        target = UpstreamTarget(url="https://mcp.tavily.com/mcp", is_rest=False)
        req = _make_request({"authorization": "Bearer client-token"})
        url, headers = self.plugin.inject_key_for_request(target, "key123", req)
        assert headers == {"Authorization": "Bearer key123"}

    def test_mcp_without_bearer_uses_query_param(self):
        target = UpstreamTarget(url="https://mcp.tavily.com/mcp", is_rest=False)
        req = _make_request({"authorization": ""})
        url, headers = self.plugin.inject_key_for_request(target, "key123", req)
        assert "tavilyApiKey=key123" in url
        assert headers is None


class TestContext7InjectKey:
    def setup_method(self):
        self.plugin = Context7Plugin()

    def test_rest_uses_bearer(self):
        target = UpstreamTarget(url="https://context7.com/api/v2/context", is_rest=True)
        req = _make_request()
        url, headers = self.plugin.inject_key_for_request(target, "ctx7sk-abc", req)
        assert headers == {"Authorization": "Bearer ctx7sk-abc"}

    def test_mcp_uses_custom_header(self):
        target = UpstreamTarget(url="https://mcp.context7.com/mcp", is_rest=False)
        req = _make_request()
        url, headers = self.plugin.inject_key_for_request(target, "ctx7sk-abc", req)
        assert headers == {"CONTEXT7_API_KEY": "ctx7sk-abc"}


class TestExaInjectKey:
    def setup_method(self):
        self.plugin = ExaPlugin()

    def test_rest_uses_x_api_key(self):
        target = UpstreamTarget(url="https://api.exa.ai/search", is_rest=True)
        req = _make_request()
        url, headers = self.plugin.inject_key_for_request(target, "exa-key", req)
        assert headers == {"x-api-key": "exa-key"}

    def test_mcp_with_x_api_key_client(self):
        target = UpstreamTarget(url="https://mcp.exa.ai/mcp", is_rest=False)
        req = _make_request({"x-api-key": "client-key"})
        url, headers = self.plugin.inject_key_for_request(target, "exa-key", req)
        assert headers == {"x-api-key": "exa-key"}

    def test_mcp_with_bearer_client(self):
        target = UpstreamTarget(url="https://mcp.exa.ai/mcp", is_rest=False)
        req = _make_request({"authorization": "Bearer client-token"})
        url, headers = self.plugin.inject_key_for_request(target, "exa-key", req)
        assert headers == {"Authorization": "Bearer exa-key"}


# ---------- REST 请求计数 ----------

class TestRestUsageCounting:
    """验证 REST 请求始终计数，MCP 非工具请求不计数。"""

    def _seed_key(self, client, platform):
        resp = client.post("/admin/keys", json={
            "platform": platform,
            "api_key": f"test-key-{platform}",
            "weight": 10,
        }, headers={"Authorization": "Bearer test-admin-key"})
        return resp.json()

    def _seed_token(self, client):
        resp = client.post("/admin/tokens", json={
            "name": "test-token",
            "allowed_platforms": ["tavily", "context7", "exa"],
        }, headers={"Authorization": "Bearer test-admin-key"})
        return resp.json()["token_value"]

    @patch("app.proxy.sse_proxy.get_shared_client")
    def test_rest_request_counts(self, mock_client_fn, client, db_session):
        self._seed_key(client, "tavily")
        token = self._seed_token(client)

        # Mock 上游响应
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.aread = AsyncMock(return_value=b'{"results":[]}')
        mock_resp.aclose = AsyncMock()

        mock_http_client = AsyncMock()
        mock_http_client.send = AsyncMock(return_value=mock_resp)
        mock_http_client.build_request = MagicMock(return_value=MagicMock())
        mock_client_fn.return_value = mock_http_client

        resp = client.post(
            "/api/tavily/search",
            json={"query": "test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # 验证 key 的 total_requests 递增了
        from app.core.models import Key
        key = db_session.query(Key).filter(Key.platform == "tavily").first()
        assert key.total_requests == 1

    @patch("app.proxy.sse_proxy.get_shared_client")
    def test_mcp_initialize_does_not_count(self, mock_client_fn, client, db_session):
        self._seed_key(client, "tavily")
        token = self._seed_token(client)

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.aread = AsyncMock(return_value=b'{"jsonrpc":"2.0","result":{}}')
        mock_resp.aclose = AsyncMock()

        mock_http_client = AsyncMock()
        mock_http_client.send = AsyncMock(return_value=mock_resp)
        mock_http_client.build_request = MagicMock(return_value=MagicMock())
        mock_client_fn.return_value = mock_http_client

        resp = client.post(
            "/api/tavily/mcp",
            json={"jsonrpc": "2.0", "method": "initialize", "id": 1,
                  "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                             "clientInfo": {"name": "test", "version": "1.0"}}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        from app.core.models import Key
        key = db_session.query(Key).filter(Key.platform == "tavily").first()
        assert key.total_requests == 0
