from flask import Blueprint, jsonify, request

from middleware.permissions import require_permission
from services.audit_service import query_logs

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/", methods=["GET"])
@require_permission("audit:read")
def list_audit_logs():
    user_id = request.args.get("user_id", type=int)
    action = request.args.get("action")
    resource_type = request.args.get("resource_type")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = query_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
    )
    return jsonify(result)
