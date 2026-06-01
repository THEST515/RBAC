from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from services.auth_service import register_user, login_user, get_profile
from middleware.permissions import get_current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip() or None

    result, error = register_user(username, password, email)
    if error:
        return jsonify({"error": error}), 400

    return jsonify(result), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    result, error = login_user(username, password, ip_address=request.remote_addr)
    if error:
        return jsonify({"error": error}), 401

    return jsonify(result)


@auth_bp.route("/profile", methods=["GET"])
def profile():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    result, error = get_profile(current_user["user_id"])
    if error:
        return jsonify({"error": error}), 404

    return jsonify(result)
