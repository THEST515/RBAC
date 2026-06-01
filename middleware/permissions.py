from functools import wraps

from flask import current_app, g, jsonify, request

from models.user import User
from models.audit_log import AuditLog
from utils.security import decode_token


def get_current_user():
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    if not token:
        return None

    payload = decode_token(token)
    return payload


def require_permission(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            payload = get_current_user()
            if not payload:
                from extensions import db

                log_entry = AuditLog(
                    action="PERMISSION_DENIED",
                    details=f"No valid token for {permission_name} on {request.path}",
                    ip_address=request.remote_addr,
                )
                db.session.add(log_entry)
                db.session.commit()
                return jsonify({"error": "Unauthorized — valid token required"}), 401

            if permission_name not in payload.get("permissions", []):
                from extensions import db

                log_entry = AuditLog(
                    user_id=payload.get("user_id"),
                    username=payload.get("username"),
                    action="PERMISSION_DENIED",
                    resource_type=permission_name.split(":")[0] if ":" in permission_name else None,
                    details=f"User lacks '{permission_name}' for {request.method} {request.path}",
                    ip_address=request.remote_addr,
                )
                db.session.add(log_entry)
                db.session.commit()
                return jsonify({"error": f"Forbidden — requires '{permission_name}' permission"}), 403

            g.current_user = payload
            return f(*args, **kwargs)

        return decorated_function

    return decorator
