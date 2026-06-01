"""Initialize database: create tables and seed default roles, permissions, and admin user."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.user import User
from models.role import Role
from models.permission import Permission
from models.file_model import FileModel
from models.audit_log import AuditLog
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

ROLES = {
    "Admin": "Full system control — manage users, roles, files, and view audit logs",
    "Manager": "User/role management, file operations, view audit logs",
    "Editor": "Full file operations (CRUD), view users",
    "Contributor": "Upload and edit files, no deletion",
    "Viewer": "Read-only file access",
    "Auditor": "View audit logs and files",
}

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


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        perm_map = {}
        for name, resource, action, desc in PERMISSIONS:
            p = Permission.query.filter_by(name=name).first()
            if not p:
                p = Permission(name=name, resource=resource, action=action, description=desc)
                db.session.add(p)
                db.session.flush()
            perm_map[name] = p

        for role_name, description in ROLES.items():
            r = Role.query.filter_by(name=role_name).first()
            if not r:
                r = Role(name=role_name, description=description)
                db.session.add(r)
                db.session.flush()

            assigned = {p.name for p in r.permissions}
            for perm_name in ROLE_PERMISSIONS[role_name]:
                if perm_name not in assigned:
                    r.permissions.append(perm_map[perm_name])

        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                email="admin@rbac.local",
            )
            admin.roles.append(Role.query.filter_by(name="Admin").first())
            db.session.add(admin)

        db.session.commit()
        print("Database initialized successfully!")
        print("  - 13 permissions seeded")
        print("  - 6 roles seeded")
        print("  - Default admin user: admin / admin123")


if __name__ == "__main__":
    seed()
