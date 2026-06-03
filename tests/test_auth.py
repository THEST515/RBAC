"""Tests for authentication: login, register, profile, token validation."""


class TestRegister:
    def test_register_creates_user_with_viewer_role(self, client):
        resp = client.post("/api/auth/register",
                           json={"username": "newuser", "password": "NewUser1Pass"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert "token" in data
        assert data["user"]["username"] == "newuser"
        roles = [r["name"] for r in data["user"]["roles"]]
        assert "Viewer" in roles

    def test_register_duplicate_username_fails(self, client):
        client.post("/api/auth/register",
                    json={"username": "dup_user", "password": "DupUser1Pass"})
        resp = client.post("/api/auth/register",
                           json={"username": "dup_user", "password": "Other1Pass"})
        assert resp.status_code == 400
        assert "already exists" in resp.get_json()["error"].lower()

    def test_register_weak_password_rejected(self, client):
        resp = client.post("/api/auth/register",
                           json={"username": "weakpw", "password": "short"})
        assert resp.status_code == 400

    def test_register_no_digits_rejected(self, client):
        resp = client.post("/api/auth/register",
                           json={"username": "nodigits", "password": "NoDigitsHere"})
        assert resp.status_code == 400

    def test_register_no_uppercase_rejected(self, client):
        resp = client.post("/api/auth/register",
                           json={"username": "noupper", "password": "nouppercase1"})
        assert resp.status_code == 400

    def test_register_short_username_rejected(self, client):
        resp = client.post("/api/auth/register",
                           json={"username": "ab", "password": "ShortUs1Pass"})
        assert resp.status_code == 400


class TestLogin:
    def test_login_admin_success(self, client):
        resp = client.post("/api/auth/login",
                           json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert data["user"]["username"] == "admin"
        assert "Admin" in [r["name"] for r in data["user"]["roles"]]

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login",
                           json={"username": "admin", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login",
                           json={"username": "ghost_user", "password": "Ghost123User"})
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/api/auth/login",
                           json={"username": "admin"})
        assert resp.status_code == 400


class TestProfile:
    def test_profile_with_valid_token(self, client, auth_header):
        resp = client.get("/api/auth/profile", headers=auth_header)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["username"] == "admin"

    def test_profile_without_token_returns_401(self, client):
        resp = client.get("/api/auth/profile")
        assert resp.status_code == 401

    def test_profile_with_invalid_token(self, client):
        resp = client.get("/api/auth/profile",
                          headers={"Authorization": "Bearer fake.token.here"})
        assert resp.status_code == 401


class TestToken:
    def test_token_contains_permissions(self, client, auth_header):
        resp = client.get("/api/auth/profile", headers=auth_header)
        data = resp.get_json()
        assert len(data["permissions"]) == 13
        assert "user:create" in data["permissions"]
        assert "file:read" in data["permissions"]

    def test_viewer_token_has_only_file_read(self, client, viewer_header):
        resp = client.get("/api/auth/profile", headers=viewer_header)
        data = resp.get_json()
        assert data["permissions"] == ["file:read"]
