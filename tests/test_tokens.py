"""Token 管理 CRUD 接口测试。"""
import pytest

ADMIN_HEADERS = {"Authorization": "Bearer test-admin-key"}


class TestTokenCreate:
    def test_create_token_success(self, client):
        resp = client.post("/admin/tokens", json={
            "name": "test-project",
            "allowed_platforms": ["tavily", "exa"],
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test-project"
        assert data["allowed_platforms"] == ["tavily", "exa"]
        assert data["status"] == "active"
        assert len(data["token_value"]) == 64

    def test_create_token_generates_unique_values(self, client):
        r1 = client.post("/admin/tokens", json={
            "name": "token-1", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        r2 = client.post("/admin/tokens", json={
            "name": "token-2", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        assert r1.json()["token_value"] != r2.json()["token_value"]

    def test_create_token_duplicate_name_returns_409(self, client):
        client.post("/admin/tokens", json={
            "name": "dup-name", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        resp = client.post("/admin/tokens", json={
            "name": "dup-name", "allowed_platforms": ["exa"],
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]


class TestTokenList:
    def _seed_tokens(self, client):
        for i in range(3):
            client.post("/admin/tokens", json={
                "name": f"project-{i}",
                "allowed_platforms": ["tavily"],
            }, headers=ADMIN_HEADERS)

    def test_list_tokens(self, client):
        self._seed_tokens(client)
        resp = client.get("/admin/tokens", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_pagination(self, client):
        self._seed_tokens(client)
        resp = client.get("/admin/tokens?page=1&page_size=2", headers=ADMIN_HEADERS)
        data = resp.json()
        assert len(data["items"]) == 2


class TestTokenUpdate:
    def _create_token(self, client):
        resp = client.post("/admin/tokens", json={
            "name": "update-test", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        return resp.json()["id"]

    def test_update_token_name(self, client):
        tid = self._create_token(client)
        resp = client.patch(f"/admin/tokens/{tid}", json={"name": "new-name"}, headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "new-name"

    def test_update_allowed_platforms(self, client):
        tid = self._create_token(client)
        resp = client.patch(f"/admin/tokens/{tid}", json={
            "allowed_platforms": ["tavily", "exa", "context7"],
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["allowed_platforms"] == ["tavily", "exa", "context7"]

    def test_update_token_status(self, client):
        tid = self._create_token(client)
        resp = client.patch(f"/admin/tokens/{tid}", json={"status": "disabled"}, headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "disabled"

    def test_update_nonexistent_token_returns_404(self, client):
        resp = client.patch("/admin/tokens/9999", json={"name": "x"}, headers=ADMIN_HEADERS)
        assert resp.status_code == 404

    def test_update_token_name_conflict_returns_409(self, client):
        client.post("/admin/tokens", json={
            "name": "existing-name", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        r2 = client.post("/admin/tokens", json={
            "name": "other-name", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        tid = r2.json()["id"]
        resp = client.patch(f"/admin/tokens/{tid}", json={"name": "existing-name"}, headers=ADMIN_HEADERS)
        assert resp.status_code == 409

    def test_update_token_same_name_no_conflict(self, client):
        r = client.post("/admin/tokens", json={
            "name": "keep-name", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        tid = r.json()["id"]
        resp = client.patch(f"/admin/tokens/{tid}", json={"name": "keep-name"}, headers=ADMIN_HEADERS)
        assert resp.status_code == 200


class TestTokenDelete:
    def test_delete_token(self, client):
        resp = client.post("/admin/tokens", json={
            "name": "delete-me", "allowed_platforms": ["tavily"],
        }, headers=ADMIN_HEADERS)
        tid = resp.json()["id"]
        del_resp = client.delete(f"/admin/tokens/{tid}", headers=ADMIN_HEADERS)
        assert del_resp.status_code == 204

    def test_delete_nonexistent_token_returns_404(self, client):
        resp = client.delete("/admin/tokens/9999", headers=ADMIN_HEADERS)
        assert resp.status_code == 404
