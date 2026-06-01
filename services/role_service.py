from extensions import db
from models.role import Role
from models.permission import Permission
from models.audit_log import AuditLog


def list_roles():
    return [r.to_dict() for r in Role.query.order_by(Role.id).all()]


def create_role(name, description=None):
    if not name or len(name.strip()) < 2:
        return None, "Role name must be at least 2 characters"

    name = name.strip()
    if Role.query.filter_by(name=name).first():
        return None, "Role already exists"

    role = Role(name=name, description=description)
    db.session.add(role)
    db.session.flush()

    log = AuditLog(
        action="ROLE_CREATED",
        resource_type="role",
        resource_id=role.id,
        details=f"Role '{name}' created",
    )
    db.session.add(log)
    db.session.commit()

    return role.to_dict(), None


def get_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return None, "Role not found"
    return role.to_dict(), None


def update_role(role_id, name=None, description=None):
    role = Role.query.get(role_id)
    if not role:
        return None, "Role not found"

    if name and name != role.name:
        if Role.query.filter_by(name=name).first():
            return None, "Role name already exists"
        role.name = name

    if description is not None:
        role.description = description

    db.session.commit()
    return role.to_dict(), None


def delete_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return None, "Role not found"

    if role.name in ("Admin", "Viewer"):
        return None, f"Cannot delete the built-in '{role.name}' role"

    db.session.delete(role)
    db.session.commit()
    return {"deleted": True}, None


def get_role_permissions(role_id):
    role = Role.query.get(role_id)
    if not role:
        return None, "Role not found"
    return [p.to_dict() for p in role.permissions], None


def set_role_permissions(role_id, permission_ids):
    role = Role.query.get(role_id)
    if not role:
        return None, "Role not found"

    permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
    role.permissions = permissions
    db.session.commit()

    return [p.to_dict() for p in role.permissions], None
