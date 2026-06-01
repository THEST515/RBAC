import jwt
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def generate_token(user):
    payload = {
        "user_id": user.id,
        "username": user.username,
        "roles": [r.name for r in user.roles],
        "permissions": list(user.get_permissions()),
        "exp": datetime.utcnow() + timedelta(hours=current_app.config.get("JWT_EXPIRATION_HOURS", 24)),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
