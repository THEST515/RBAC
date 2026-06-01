from flask import Blueprint, jsonify

from models.permission import Permission

permissions_bp = Blueprint("permissions", __name__)


@permissions_bp.route("/", methods=["GET"])
def list_permissions():
    perms = Permission.query.order_by(Permission.resource, Permission.action).all()
    return jsonify([p.to_dict() for p in perms])
