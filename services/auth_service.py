from extensions import db
from models.user import User
from models.role import Role
from models.audit_log import AuditLog
from utils.security import hash_password, verify_password, generate_token


def register_user(username, password, email=None):
    from utils.validators import validate_username, validate_password, validate_email

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

    if email and User.query.filter_by(email=email).first():
        return None, "Email already exists"

    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
    )

    viewer_role = Role.query.filter_by(name="Viewer").first()
    if viewer_role:
        user.roles.append(viewer_role)

    db.session.add(user)
    db.session.flush()

    log = AuditLog(
        user_id=user.id,
        username=user.username,
        action="USER_REGISTER",
        resource_type="user",
        resource_id=user.id,
        details=f"User '{username}' registered",
    )
    db.session.add(log)
    db.session.commit()

    token = generate_token(user)
    return {"token": token, "user": user.to_dict()}, None


def login_user(username, password, ip_address=None):
    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        log = AuditLog(
            username=username,
            action="LOGIN_FAILED",
            details=f"Failed login attempt for '{username}'",
            ip_address=ip_address,
        )
        db.session.add(log)
        db.session.commit()
        return None, "Invalid username or password"

    if not user.is_active:
        return None, "Account is deactivated"

    token = generate_token(user)

    log = AuditLog(
        user_id=user.id,
        username=user.username,
        action="LOGIN_SUCCESS",
        details=f"User '{username}' logged in",
        ip_address=ip_address,
    )
    db.session.add(log)
    db.session.commit()

    return {"token": token, "user": user.to_dict()}, None


def get_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return None, "User not found"
    return user.to_dict(), None
