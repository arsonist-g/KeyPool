"""Key 管理 CRUD 接口测试。"""
import pytest

ADMIN_HEADERS = {"Authorization": "Bearer test-admin-key"}


class TestKeyCreate:
    def test_create_key_success(self, client):
        resp = client.post("/admin/keys", json={
            "platform": "tavily",
            "api_key": "tvly-test-key-001",
            "weight": 1.5,
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 201
        data = resp.json()
        assert data["platform"] == "tavily"
        assert data["api_key"] == "tvly-test-key-001"
        assert data["weight"] == 1.5
        assert data["status"] == "active"
        assert data["total_requests"] == 0
        assert data["failed_requests"] == 0
        assert "id" in data

    def test_create_key_default_weight(self, client):
        resp = client.post("/admin/keys", json={
            "platform": "exa",
            "api_key": "exa-test-key-001",
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 201
        assert resp.json()["weight"] == 1.0

    def test_create_duplicate_key_returns_409(self, client):
        payload = {"platform": "tavily", "api_key": "tvly-dup-key"}
        client.post("/admin/keys", json=payload, headers=ADMIN_HEADERS)
        resp = client.post("/admin/keys", json=payload, headers=ADMIN_HEADERS)
        assert resp.status_code == 409

    def test_create_same_key_different_platform_ok(self, client):
        key = "shared-key-value"
        r1 = client.post("/admin/keys", json={"platform": "tavily", "api_key": key}, headers=ADMIN_HEADERS)
        r2 = client.post("/admin/keys", json={"platform": "exa", "api_key": key}, headers=ADMIN_HEADERS)
        assert r1.status_code == 201
        assert r2.status_code == 201


class TestKeyList:
    def _seed_keys(self, client):
        for i in range(5):
            client.post("/admin/keys", json={
                "platform": "tavily" if i % 2 == 0 else "exa",
                "api_key": f"key-{i}",
            }, headers=ADMIN_HEADERS)

    def test_list_all_keys(self, client):
        self._seed_keys(client)
        resp = client.get("/admin/keys", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_list_filter_by_platform(self, client):
        self._seed_keys(client)
        resp = client.get("/admin/keys?platform=tavily", headers=ADMIN_HEADERS)
        data = resp.json()
        assert data["total"] == 3
        assert all(k["platform"] == "tavily" for k in data["items"])

    def test_list_filter_by_status(self, client):
        self._seed_keys(client)
        resp = client.get("/admin/keys?status=active", headers=ADMIN_HEADERS)
        data = resp.json()
        assert data["total"] == 5

    def test_list_pagination(self, client):
        self._seed_keys(client)
        resp = client.get("/admin/keys?page=1&page_size=2", headers=ADMIN_HEADERS)
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2


class TestKeyUpdate:
    def _create_key(self, client):
        resp = client.post("/admin/keys", json={
            "platform": "tavily", "api_key": "update-test-key",
        }, headers=ADMIN_HEADERS)
        return resp.json()["id"]

    def test_update_weight(self, client):
        key_id = self._create_key(client)
        resp = client.patch(f"/admin/keys/{key_id}", json={"weight": 2.5}, headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["weight"] == 2.5

    def test_update_status(self, client):
        key_id = self._create_key(client)
        resp = client.patch(f"/admin/keys/{key_id}", json={"status": "disabled"}, headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "disabled"

    def test_update_nonexistent_key_returns_404(self, client):
        resp = client.patch("/admin/keys/9999", json={"weight": 1.0}, headers=ADMIN_HEADERS)
        assert resp.status_code == 404


class TestKeyDelete:
    def test_delete_key(self, client):
        resp = client.post("/admin/keys", json={
            "platform": "tavily", "api_key": "delete-me",
        }, headers=ADMIN_HEADERS)
        key_id = resp.json()["id"]
        del_resp = client.delete(f"/admin/keys/{key_id}", headers=ADMIN_HEADERS)
        assert del_resp.status_code == 204
        get_resp = client.get(f"/admin/keys/{key_id}", headers=ADMIN_HEADERS)
        assert get_resp.status_code == 404

    def test_delete_nonexistent_key_returns_404(self, client):
        resp = client.delete("/admin/keys/9999", headers=ADMIN_HEADERS)
        assert resp.status_code == 404
