"""Stats 接口测试。"""
import pytest

ADMIN_HEADERS = {"Authorization": "Bearer test-admin-key"}


class TestGlobalStats:
    def test_empty_stats(self, client):
        resp = client.get("/admin/stats", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_stats_with_keys(self, client):
        client.post("/admin/keys", json={"platform": "tavily", "api_key": "k1"}, headers=ADMIN_HEADERS)
        client.post("/admin/keys", json={"platform": "tavily", "api_key": "k2"}, headers=ADMIN_HEADERS)
        client.post("/admin/keys", json={"platform": "exa", "api_key": "k3"}, headers=ADMIN_HEADERS)

        resp = client.get("/admin/stats", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        platforms = {s["platform"]: s for s in data}
        assert "tavily" in platforms
        assert "exa" in platforms
        assert platforms["tavily"]["total_keys"] == 2
        assert platforms["tavily"]["active_keys"] == 2
        assert platforms["exa"]["total_keys"] == 1


class TestPlatformStats:
    def test_platform_stats_no_keys(self, client):
        resp = client.get("/admin/stats/tavily", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "tavily"
        assert data["total_keys"] == 0

    def test_platform_stats_with_keys(self, client):
        client.post("/admin/keys", json={"platform": "tavily", "api_key": "k1"}, headers=ADMIN_HEADERS)
        client.post("/admin/keys", json={"platform": "tavily", "api_key": "k2"}, headers=ADMIN_HEADERS)
        resp = client.get("/admin/stats/tavily", headers=ADMIN_HEADERS)
        data = resp.json()
        assert data["total_keys"] == 2
        assert data["active_keys"] == 2
        assert data["total_requests"] == 0


class TestQuotaOverview:
    def test_quota_overview_empty(self, client):
        resp = client.get("/admin/stats/quota/overview", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
