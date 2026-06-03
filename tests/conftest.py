"""Shared fixtures for RBAC test suite."""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db


@pytest.fixture
def app():
    """Create app with temporary database — completely isolated from dev DB."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    app = create_app("development")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["TESTING"] = True

    # Re-init db with new URI: dispose old engine, bind new one
    with app.app_context():
        db.engine.dispose()
        # Now drop any existing (from create_app's db.create_all) and re-create on temp db
        db.drop_all()
        db.create_all()
        _seed(app)

    yield app

    os.close(db_fd)
    os.unlink(db_path)


def _seed(app):
    """Seed roles, permissions, and admin user into the test database."""
    from models.user import User
    from models.role import Role
    from models.permission import Permission
    from werkzeug.security import generate_password_hash

    PERMISSIONS = [
        ("user:create", "user", "create", "Create users"),
        ("user:read", "user", "read", "View users"),
        ("user:update", "user", "update", "Edit users"),
        ("user:delete", "user", "delete", "Delete users"),
        ("role:create", "role", "create", "Create roles"),
        ("role:read", "role", "read", "View roles"),
        ("role:update", "role", "update", "Edit roles and assign permissions"),
        ("role:delete", "role", "delete", "Delete roles"),
        ("file:create", "file", "create", "Upload files"),
        ("file:read", "file", "read", "View/download files"),
        ("file:update", "file", "update", "Replace file content"),
        ("file:delete", "file", "delete", "Delete files"),
        ("audit:read", "audit", "read", "View audit logs"),
    ]

    ROLE_PERMISSIONS = {
        "Admin": [
            "user:create", "user:read", "user:update", "user:delete",
            "role:create", "role:read", "role:update", "role:delete",
            "file:create", "file:read", "file:update", "file:delete",
            "audit:read",
        ],
        "Manager": [
            "user:create", "user:read", "user:update", "user:delete",
            "role:read",
            "file:create", "file:read", "file:update", "file:delete",
            "audit:read",
        ],
        "Editor": [
            "file:create", "file:read", "file:update", "file:delete",
            "user:read",
        ],
        "Contributor": [
            "file:create", "file:read", "file:update",
        ],
        "Viewer": [
            "file:read",
        ],
        "Auditor": [
            "audit:read", "file:read",
        ],
    }

    ROLES = {
        "Admin": "Full system control",
        "Manager": "User/role management + file ops",
        "Editor": "Full file CRUD",
        "Contributor": "Upload and edit, no delete",
        "Viewer": "Read-only",
        "Auditor": "Audit log access",
    }

    perm_map = {}
    for name, resource, action, desc in PERMISSIONS:
        p = Permission(name=name, resource=resource, action=action, description=desc)
        db.session.add(p)
        db.session.flush()
        perm_map[name] = p

    for role_name, description in ROLES.items():
        r = Role(name=role_name, description=description)
        db.session.add(r)
        db.session.flush()
        for perm_name in ROLE_PERMISSIONS[role_name]:
            r.permissions.append(perm_map[perm_name])

    admin = User(
        username="admin",
        password_hash=generate_password_hash("admin123"),
        email="admin@rbac.local",
        is_active=True,
    )
    db.session.add(admin)
    db.session.flush()
    admin.roles.append(Role.query.filter_by(name="Admin").first())

    db.session.commit()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_header(client):
    """Login as admin, return Authorization header dict."""
    resp = client.post("/api/auth/login",
                       json={"username": "admin", "password": "admin123"})
    data = resp.get_json()
    return {"Authorization": f"Bearer {data['token']}"}


@pytest.fixture
def viewer_header(client, auth_header):
    """Create a Viewer user, return auth header."""
    # Create via admin so we can assign role properly
    client.post("/api/users", headers=auth_header,
                json={"username": "viewer_test", "password": "Viewer1Test",
                      "role_ids": [5]})
    resp = client.post("/api/auth/login",
                       json={"username": "viewer_test", "password": "Viewer1Test"})
    data = resp.get_json()
    return {"Authorization": f"Bearer {data['token']}"}
