from flask import Blueprint, g, jsonify, request

from middleware.permissions import require_permission
from services import user_service, audit_service

# Note: user_service.create_user() logs its own audit entry internally.
# Routes add audit logs for operations the service layer does not cover.

users_bp = Blueprint("users", __name__)


@users_bp.route("/", methods=["GET"])
@require_permission("user:read")
def list_users():
    return jsonify(user_service.list_users())


@users_bp.route("/", methods=["POST"])
@require_permission("user:create")
def create_user():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip() or None
    role_ids = data.get("role_ids")

    result, error = user_service.create_user(username, password, email, role_ids)
    if error:
        return jsonify({"error": error}), 400

    # service layer already logs USER_CREATED
    return jsonify(result), 201


@users_bp.route("/<int:user_id>", methods=["GET"])
@require_permission("user:read")
def get_user(user_id):
    result, error = user_service.get_user(user_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(result)


@users_bp.route("/<int:user_id>", methods=["PUT"])
@require_permission("user:update")
def update_user(user_id):
    data = request.get_json() or {}
    result, error = user_service.update_user(
        user_id,
        username=data.get("username"),
        email=data.get("email"),
        password=data.get("password"),
        is_active=data.get("is_active"),
        role_ids=data.get("role_ids"),
    )
    if error:
        return jsonify({"error": error}), 400

    audit_service.create_log(
        user_id=g.current_user.get("user_id"),
        username=g.current_user.get("username"),
        action="USER_UPDATED",
        resource_type="user",
        resource_id=user_id,
        details=f"User '{result['username']}' updated by '{g.current_user.get('username')}'",
        ip_address=request.remote_addr,
    )
    return jsonify(result)


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@require_permission("user:delete")
def delete_user(user_id):
    result, error = user_service.delete_user(user_id)
    if error:
        return jsonify({"error": error}), 400

    audit_service.create_log(
        user_id=g.current_user.get("user_id"),
        username=g.current_user.get("username"),
        action="USER_DELETED",
        resource_type="user",
        resource_id=user_id,
        details=f"User deleted by '{g.current_user.get('username')}'",
        ip_address=request.remote_addr,
    )
    return jsonify(result)


@users_bp.route("/<int:user_id>/roles", methods=["PUT"])
@require_permission("user:update")
def assign_roles(user_id):
    data = request.get_json() or {}
    role_ids = data.get("role_ids", [])
    result, error = user_service.assign_roles(user_id, role_ids)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(result)
