from extensions import db
from models.user import User
from models.role import Role
from models.audit_log import AuditLog
from utils.security import hash_password
from utils.validators import validate_username, validate_password, validate_email


def list_users():
    return [u.to_dict() for u in User.query.order_by(User.id).all()]


def create_user(username, password, email=None, role_ids=None):
    ok, msg = validate_username(username)
    if not ok:
        return None, msg
    ok, msg = validate_password(password)
    if not ok:
        return None, msg
    if email:
        ok, msg = validate_email(email)
        if not ok:
            return None, msg

    if User.query.filter_by(username=username).first():
        return None, "Username already exists"

    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
    )
    db.session.add(user)
    db.session.flush()

    if role_ids:
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles
    else:
        viewer = Role.query.filter_by(name="Viewer").first()
        if viewer:
            user.roles = [viewer]

    log = AuditLog(
        user_id=user.id,
        username=user.username,
        action="USER_CREATED",
        resource_type="user",
        resource_id=user.id,
        details=f"User '{username}' created",
    )
    db.session.add(log)
    db.session.commit()

    return user.to_dict(), None


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return None, "User not found"
    return user.to_dict(), None


def update_user(user_id, username=None, email=None, password=None, is_active=None, role_ids=None):
    user = db.session.get(User, user_id)
    if not user:
        return None, "User not found"

    if username and username != user.username:
        ok, msg = validate_username(username)
        if not ok:
            return None, msg
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        user.username = username

    if email is not None:
        if email:
            ok, msg = validate_email(email)
            if not ok:
                return None, msg
        user.email = email

    if password:
        ok, msg = validate_password(password)
        if not ok:
            return None, msg
        user.password_hash = hash_password(password)

    if is_active is not None:
        user.is_active = bool(is_active)

    if role_ids is not None:
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles

    db.session.commit()
    return user.to_dict(), None


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return None, "User not found"

    if user.username == "admin":
        return None, "Cannot delete the built-in admin user"

    db.session.delete(user)
    db.session.commit()
    return {"deleted": True}, None


def assign_roles(user_id, role_ids):
    user = db.session.get(User, user_id)
    if not user:
        return None, "User not found"

    roles = Role.query.filter(Role.id.in_(role_ids)).all()
    user.roles = roles
    db.session.commit()
    return user.to_dict(), None
