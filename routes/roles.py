from flask import Blueprint, g, jsonify, request

from middleware.permissions import require_permission
from services import role_service, audit_service

roles_bp = Blueprint("roles", __name__)


@roles_bp.route("/", methods=["GET"])
@require_permission("role:read")
def list_roles():
    return jsonify(role_service.list_roles())


@roles_bp.route("/", methods=["POST"])
@require_permission("role:create")
def create_role():
    data = request.get_json() or {}
    name = data.get("name", "")
    description = data.get("description", "")

    result, error = role_service.create_role(name, description)
    if error:
        return jsonify({"error": error}), 400

    # service layer already logs ROLE_CREATED
    return jsonify(result), 201


@roles_bp.route("/<int:role_id>", methods=["GET"])
@require_permission("role:read")
def get_role(role_id):
    result, error = role_service.get_role(role_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(result)


@roles_bp.route("/<int:role_id>", methods=["PUT"])
@require_permission("role:update")
def update_role(role_id):
    data = request.get_json() or {}
    result, error = role_service.update_role(
        role_id,
        name=data.get("name"),
        description=data.get("description"),
    )
    if error:
        return jsonify({"error": error}), 400

    audit_service.create_log(
        user_id=g.current_user.get("user_id"),
        username=g.current_user.get("username"),
        action="ROLE_UPDATED",
        resource_type="role",
        resource_id=role_id,
        details=f"Role updated by '{g.current_user.get('username')}'",
        ip_address=request.remote_addr,
    )
    return jsonify(result)


@roles_bp.route("/<int:role_id>", methods=["DELETE"])
@require_permission("role:delete")
def delete_role(role_id):
    result, error = role_service.delete_role(role_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(result)


@roles_bp.route("/<int:role_id>/permissions", methods=["GET"])
@require_permission("role:read")
def get_role_permissions(role_id):
    result, error = role_service.get_role_permissions(role_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(result)


@roles_bp.route("/<int:role_id>/permissions", methods=["PUT"])
@require_permission("role:update")
def set_role_permissions(role_id):
    data = request.get_json() or {}
    permission_ids = data.get("permission_ids", [])

    result, error = role_service.set_role_permissions(role_id, permission_ids)
    if error:
        return jsonify({"error": error}), 400

    audit_service.create_log(
        user_id=g.current_user.get("user_id"),
        username=g.current_user.get("username"),
        action="ROLE_PERMISSIONS_CHANGED",
        resource_type="role",
        resource_id=role_id,
        details=f"Permissions modified by '{g.current_user.get('username')}'",
        ip_address=request.remote_addr,
    )
    return jsonify(result)
