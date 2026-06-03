"""Tests for RBAC permission enforcement across all 6 roles."""
import io

import pytest


ROLE_USERS = {
    "Admin":       ("perm_admin",       "Admin1Pass"),
    "Manager":     ("perm_manager",     "Manager1Pass"),
    "Editor":      ("perm_editor",      "Editor1Pass"),
    "Contributor": ("perm_contributor", "Contrib1Pass"),
    "Viewer":      ("perm_viewer",      "Viewer1Pass"),
    "Auditor":     ("perm_auditor",     "Auditor1Pass"),
}


@pytest.fixture
def role_tokens(client):
    """Create 6 users (one per role) + login, return dict of auth headers."""
    tokens = {}
    for role_name in ["Admin", "Manager", "Editor", "Contributor", "Viewer", "Auditor"]:
        username, password = ROLE_USERS[role_name]
        client.post("/api/auth/register",
                    json={"username": username, "password": password})
        # Admin assigns the correct role
        admin_resp = client.post("/api/auth/login",
                                 json={"username": "admin", "password": "admin123"})
        admin_token = admin_resp.get_json()["token"]
        admin_header = {"Authorization": f"Bearer {admin_token}"}

        # find user id and role id
        users_resp = client.get("/api/users", headers=admin_header)
        uid = next(u["id"] for u in users_resp.get_json() if u["username"] == username)
        roles_resp = client.get("/api/roles", headers=admin_header)
        rid = next(r["id"] for r in roles_resp.get_json() if r["name"] == role_name)

        client.put(f"/api/users/{uid}", headers=admin_header,
                   json={"role_ids": [rid]})

        login_resp = client.post("/api/auth/login",
                                 json={"username": username, "password": password})
        tokens[role_name] = {
            "Authorization": f"Bearer {login_resp.get_json()['token']}"
        }
    return tokens


class TestPermissionMatrix:
    """Verify each role can only do what they're permitted."""

    # ── user CRUD ──
    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", True), ("Editor", False),
        ("Contributor", False), ("Viewer", False), ("Auditor", False),
    ])
    def test_user_create(self, client, role_tokens, role, allowed):
        resp = client.post("/api/users", headers=role_tokens[role],
                           json={"username": f"u_{role}", "password": "Test1234"})
        assert (resp.status_code == 201) == allowed, \
            f"{role} create user: expected {allowed}, got {resp.status_code}"

    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", True), ("Editor", True),
        ("Contributor", False), ("Viewer", False), ("Auditor", False),
    ])
    def test_user_read(self, client, role_tokens, role, allowed):
        resp = client.get("/api/users", headers=role_tokens[role])
        assert (resp.status_code == 200) == allowed, \
            f"{role} read users: expected {allowed}, got {resp.status_code}"

    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", True), ("Editor", False),
        ("Contributor", False), ("Viewer", False), ("Auditor", False),
    ])
    def test_user_update(self, client, role_tokens, role, allowed):
        resp = client.put("/api/users/1", headers=role_tokens[role],
                          json={"email": "x@x.com"})
        assert (resp.status_code == 200) == allowed, \
            f"{role} update user: expected {allowed}, got {resp.status_code}"

    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", True), ("Editor", False),
        ("Contributor", False), ("Viewer", False), ("Auditor", False),
    ])
    def test_user_delete(self, client, role_tokens, role, allowed):
        # Try deleting a non-admin user (user id 2 = perm_admin)
        resp = client.delete("/api/users/2", headers=role_tokens[role])
        assert (resp.status_code in (200, 400)) == allowed, \
            f"{role} delete user: expected {allowed}, got {resp.status_code}"

    # ── role CRUD ──
    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", False), ("Editor", False),
        ("Contributor", False), ("Viewer", False), ("Auditor", False),
    ])
    def test_role_create(self, client, role_tokens, role, allowed):
        resp = client.post("/api/roles", headers=role_tokens[role],
                           json={"name": f"r_{role}"})
        assert (resp.status_code == 201) == allowed, \
            f"{role} create role: expected {allowed}, got {resp.status_code}"

    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", True), ("Editor", False),
        ("Contributor", False), ("Viewer", False), ("Auditor", False),
    ])
    def test_role_read(self, client, role_tokens, role, allowed):
        resp = client.get("/api/roles", headers=role_tokens[role])
        assert (resp.status_code == 200) == allowed, \
            f"{role} read roles: expected {allowed}, got {resp.status_code}"

    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", False), ("Editor", False),
        ("Contributor", False), ("Viewer", False), ("Auditor", False),
    ])
    def test_role_update(self, client, role_tokens, role, allowed):
        resp = client.put("/api/roles/2", headers=role_tokens[role],
                          json={"description": "X"})
        assert (resp.status_code == 200) == allowed, \
            f"{role} update role: expected {allowed}, got {resp.status_code}"

    # ── file operations ──
    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", True), ("Editor", True),
        ("Contributor", True), ("Viewer", False), ("Auditor", False),
    ])
    def test_file_create(self, client, role_tokens, role, allowed):
        data = {"file": (io.BytesIO(b"x"), f"f_{role}.txt")}
        resp = client.post("/api/files", headers=role_tokens[role],
                           content_type="multipart/form-data", data=data)
        assert (resp.status_code == 201) == allowed, \
            f"{role} upload file: expected {allowed}, got {resp.status_code}"

    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", True), ("Editor", True),
        ("Contributor", True), ("Viewer", True), ("Auditor", True),
    ])
    def test_file_read(self, client, role_tokens, role, allowed):
        resp = client.get("/api/files", headers=role_tokens[role])
        assert (resp.status_code == 200) == allowed, \
            f"{role} list files: expected {allowed}, got {resp.status_code}"

    # ── audit log ──
    @pytest.mark.parametrize("role,allowed", [
        ("Admin", True), ("Manager", True), ("Editor", False),
        ("Contributor", False), ("Viewer", False), ("Auditor", True),
    ])
    def test_audit_read(self, client, role_tokens, role, allowed):
        resp = client.get("/api/audit-logs", headers=role_tokens[role])
        assert (resp.status_code == 200) == allowed, \
            f"{role} read audit: expected {allowed}, got {resp.status_code}"


class TestPermissionDenied:
    """Verify that denied requests DO NOT succeed."""
    def test_contributor_cannot_delete_file(self, client, role_tokens):
        resp = client.delete("/api/files/1", headers=role_tokens["Contributor"])
        assert resp.status_code == 403

    def test_editor_cannot_create_role(self, client, role_tokens):
        resp = client.post("/api/roles", headers=role_tokens["Editor"],
                           json={"name": "HackRole"})
        assert resp.status_code == 403

    def test_viewer_cannot_upload(self, client, role_tokens):
        data = {"file": (io.BytesIO(b"x"), "nope.txt")}
        resp = client.post("/api/files", headers=role_tokens["Viewer"],
                           content_type="multipart/form-data", data=data)
        assert resp.status_code == 403
