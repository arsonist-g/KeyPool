"""认证系统测试。"""
import pytest

ADMIN_HEADERS = {"Authorization": "Bearer test-admin-key"}


class TestAdminAuth:
    def test_no_auth_returns_401(self, client):
        resp = client.get("/admin/keys")
        assert resp.status_code == 401

    def test_wrong_key_returns_401(self, client):
        resp = client.get("/admin/keys", headers={"Authorization": "Bearer wrong-key"})
        assert resp.status_code == 401

    def test_correct_bearer_auth(self, client):
        resp = client.get("/admin/keys", headers=ADMIN_HEADERS)
        assert resp.status_code == 200

    def test_query_param_auth(self, client):
        resp = client.get("/admin/keys?token=test-admin-key")
        assert resp.status_code == 200


class TestProjectTokenAuth:
    def _setup_token(self, client):
        """创建一个 key 和一个 project token。"""
        client.post("/admin/keys", json={
            "platform": "tavily", "api_key": "tvly-auth-test-key",
        }, headers=ADMIN_HEADERS)
        resp = client.post("/admin/tokens", json={
            "name": "auth-test", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        return resp.json()["token_value"]

    def test_no_token_returns_401(self, client):
        self._setup_token(client)
        resp = client.get("/api/tavily/mcp/sse")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        self._setup_token(client)
        resp = client.get("/api/tavily/mcp/sse", headers={"Authorization": "Bearer invalid-token"})
        assert resp.status_code == 401

    def test_token_wrong_platform_returns_403(self, client):
        token = self._setup_token(client)
        client.post("/admin/keys", json={
            "platform": "exa", "api_key": "exa-auth-test-key",
        }, headers=ADMIN_HEADERS)
        resp = client.get("/api/exa/mcp", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
