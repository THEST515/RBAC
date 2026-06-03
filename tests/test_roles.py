"""Tests for role CRUD + permission assignment + matrix."""


class TestListRoles:
    def test_admin_can_list_roles(self, client, auth_header):
        resp = client.get("/api/roles", headers=auth_header)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 6
        names = [r["name"] for r in data]
        assert "Admin" in names
        assert "Viewer" in names

    def test_viewer_cannot_list_roles(self, client, viewer_header):
        resp = client.get("/api/roles", headers=viewer_header)
        assert resp.status_code == 403


class TestCreateRole:
    def test_admin_can_create_role(self, client, auth_header):
        resp = client.post("/api/roles", headers=auth_header,
                           json={"name": "Tester", "description": "Test role"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Tester"
        assert data["description"] == "Test role"

    def test_create_role_duplicate_name(self, client, auth_header):
        client.post("/api/roles", headers=auth_header,
                    json={"name": "DupRole"})
        resp = client.post("/api/roles", headers=auth_header,
                           json={"name": "DupRole"})
        assert resp.status_code == 400

    def test_create_role_empty_name(self, client, auth_header):
        resp = client.post("/api/roles", headers=auth_header,
                           json={"name": ""})
        assert resp.status_code == 400


class TestUpdateRole:
    def test_admin_can_update_role(self, client, auth_header):
        resp = client.put("/api/roles/2", headers=auth_header,
                          json={"description": "Updated desc"})
        assert resp.status_code == 200
        assert "Updated desc" in resp.get_json()["description"]


class TestDeleteRole:
    def test_admin_can_delete_custom_role(self, client, auth_header):
        client.post("/api/roles", headers=auth_header,
                    json={"name": "TempRole"})
        resp = client.delete("/api/roles/7", headers=auth_header)
        assert resp.status_code == 200

    def test_cannot_delete_admin_role(self, client, auth_header):
        resp = client.delete("/api/roles/1", headers=auth_header)
        assert resp.status_code == 400

    def test_cannot_delete_viewer_role(self, client, auth_header):
        resp = client.delete("/api/roles/5", headers=auth_header)
        assert resp.status_code == 400


class TestRolePermissions:
    def test_admin_can_get_role_permissions(self, client, auth_header):
        resp = client.get("/api/roles/1/permissions", headers=auth_header)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 13

    def test_admin_can_set_role_permissions(self, client, auth_header):
        resp = client.put("/api/roles/1/permissions", headers=auth_header,
                          json={"permission_ids": [1, 2, 9, 10]})
        assert resp.status_code == 200
        data = resp.get_json()
        perm_names = [p["name"] for p in data]
        assert len(perm_names) == 4
        assert "user:create" in perm_names
        assert "file:read" in perm_names

    def test_viewer_cannot_modify_permissions(self, client, viewer_header):
        resp = client.put("/api/roles/1/permissions", headers=viewer_header,
                          json={"permission_ids": [10]})
        assert resp.status_code == 403
