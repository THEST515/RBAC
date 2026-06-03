"""Tests for user CRUD + role assignment + permission enforcement."""


class TestListUsers:
    def test_admin_can_list_users(self, client, auth_header):
        resp = client.get("/api/users", headers=auth_header)
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert any(u["username"] == "admin" for u in data)

    def test_viewer_cannot_list_users(self, client, viewer_header):
        resp = client.get("/api/users", headers=viewer_header)
        assert resp.status_code == 403

    def test_unauthenticated_cannot_list_users(self, client):
        resp = client.get("/api/users")
        assert resp.status_code == 401


class TestCreateUser:
    def test_admin_can_create_user(self, client, auth_header):
        resp = client.post("/api/users", headers=auth_header,
                           json={"username": "created_by_admin", "password": "Created1ByAdmin"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["username"] == "created_by_admin"

    def test_create_user_with_roles(self, client, auth_header):
        resp = client.post("/api/users", headers=auth_header,
                           json={"username": "multi_role", "password": "MultiR1User",
                                 "email": "multi@test.local", "role_ids": [2, 3]})
        assert resp.status_code == 201
        data = resp.get_json()
        role_names = [r["name"] for r in data["roles"]]
        assert "Manager" in role_names
        assert "Editor" in role_names

    def test_create_user_duplicate_username(self, client, auth_header):
        client.post("/api/users", headers=auth_header,
                    json={"username": "unique_user", "password": "Unique1User"})
        resp = client.post("/api/users", headers=auth_header,
                           json={"username": "unique_user", "password": "Other1Pass"})
        assert resp.status_code == 400

    def test_viewer_cannot_create_user(self, client, viewer_header):
        resp = client.post("/api/users", headers=viewer_header,
                           json={"username": "hacker", "password": "Hacker1User"})
        assert resp.status_code == 403


class TestGetUser:
    def test_admin_can_get_user(self, client, auth_header):
        resp = client.get("/api/users/1", headers=auth_header)
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "admin"

    def test_get_nonexistent_user(self, client, auth_header):
        resp = client.get("/api/users/9999", headers=auth_header)
        assert resp.status_code == 404


class TestUpdateUser:
    def test_admin_can_update_user(self, client, auth_header):
        resp = client.put("/api/users/1", headers=auth_header,
                          json={"email": "newadmin@rbac.local"})
        assert resp.status_code == 200
        assert resp.get_json()["email"] == "newadmin@rbac.local"

    def test_update_user_roles(self, client, auth_header):
        resp = client.put("/api/users/1", headers=auth_header,
                          json={"role_ids": [1, 5]})
        assert resp.status_code == 200
        roles = [r["name"] for r in resp.get_json()["roles"]]
        assert "Admin" in roles
        assert "Viewer" in roles

    def test_viewer_cannot_update_user(self, client, viewer_header):
        resp = client.put("/api/users/1", headers=viewer_header,
                          json={"email": "hacked@hack.local"})
        assert resp.status_code == 403


class TestDeleteUser:
    def test_admin_can_delete_regular_user(self, client, auth_header):
        client.post("/api/users", headers=auth_header,
                    json={"username": "to_delete", "password": "Delete1User"})
        resp = client.delete("/api/users/2", headers=auth_header)
        assert resp.status_code == 200

    def test_cannot_delete_admin(self, client, auth_header):
        resp = client.delete("/api/users/1", headers=auth_header)
        assert resp.status_code == 400

    def test_viewer_cannot_delete_user(self, client, viewer_header):
        resp = client.delete("/api/users/1", headers=viewer_header)
        assert resp.status_code == 403
