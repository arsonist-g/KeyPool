"""Proxy 管理 CRUD 接口测试。"""
import pytest

ADMIN_HEADERS = {"Authorization": "Bearer test-admin-key"}


class TestProxyCreate:
    def test_create_proxy_success(self, client):
        resp = client.post("/admin/proxies", json={
            "protocol": "http",
            "host": "127.0.0.1",
            "port": 17890,
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 201
        data = resp.json()
        assert data["protocol"] == "http"
        assert data["host"] == "127.0.0.1"
        assert data["port"] == 17890
        assert data["status"] == "active"
        assert data["username"] is None
        assert data["password"] is None

    def test_create_proxy_with_auth(self, client):
        resp = client.post("/admin/proxies", json={
            "protocol": "socks5",
            "host": "proxy.example.com",
            "port": 1080,
            "username": "user",
            "password": "pass",
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "user"
        assert data["password"] == "pass"

    def test_create_proxy_duplicate_host_port_returns_409(self, client):
        client.post("/admin/proxies", json={
            "protocol": "http",
            "host": "dup.example.com",
            "port": 8080,
        }, headers=ADMIN_HEADERS)
        resp = client.post("/admin/proxies", json={
            "protocol": "socks5",
            "host": "dup.example.com",
            "port": 8080,
            "username": "user",
            "password": "pass",
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_create_proxy_same_host_different_port_ok(self, client):
        client.post("/admin/proxies", json={
            "protocol": "http",
            "host": "multi.example.com",
            "port": 8080,
        }, headers=ADMIN_HEADERS)
        resp = client.post("/admin/proxies", json={
            "protocol": "http",
            "host": "multi.example.com",
            "port": 8081,
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 201


class TestProxyList:
    def _seed_proxies(self, client):
        for i in range(3):
            client.post("/admin/proxies", json={
                "protocol": "http",
                "host": f"proxy-{i}.example.com",
                "port": 8080 + i,
            }, headers=ADMIN_HEADERS)

    def test_list_proxies(self, client):
        self._seed_proxies(client)
        resp = client.get("/admin/proxies", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_pagination(self, client):
        self._seed_proxies(client)
        resp = client.get("/admin/proxies?page=1&page_size=2", headers=ADMIN_HEADERS)
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3


class TestProxyUpdate:
    def _create_proxy(self, client):
        resp = client.post("/admin/proxies", json={
            "protocol": "http", "host": "localhost", "port": 8080,
        }, headers=ADMIN_HEADERS)
        return resp.json()["id"]

    def test_update_proxy_status(self, client):
        pid = self._create_proxy(client)
        resp = client.patch(f"/admin/proxies/{pid}", json={"status": "disabled"}, headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "disabled"

    def test_update_proxy_host_port(self, client):
        pid = self._create_proxy(client)
        resp = client.patch(f"/admin/proxies/{pid}", json={
            "host": "new-host.com", "port": 9090,
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["host"] == "new-host.com"
        assert resp.json()["port"] == 9090

    def test_update_nonexistent_proxy_returns_404(self, client):
        resp = client.patch("/admin/proxies/9999", json={"status": "disabled"}, headers=ADMIN_HEADERS)
        assert resp.status_code == 404


class TestProxyDelete:
    def test_delete_proxy(self, client):
        resp = client.post("/admin/proxies", json={
            "protocol": "http", "host": "localhost", "port": 8080,
        }, headers=ADMIN_HEADERS)
        pid = resp.json()["id"]
        del_resp = client.delete(f"/admin/proxies/{pid}", headers=ADMIN_HEADERS)
        assert del_resp.status_code == 204
        get_resp = client.get(f"/admin/proxies/{pid}", headers=ADMIN_HEADERS)
        assert get_resp.status_code == 404

    def test_delete_nonexistent_proxy_returns_404(self, client):
        resp = client.delete("/admin/proxies/9999", headers=ADMIN_HEADERS)
        assert resp.status_code == 404
