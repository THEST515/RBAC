from flask import Blueprint, g, jsonify, request, send_file

from middleware.permissions import require_permission
from services import file_service, audit_service

files_bp = Blueprint("files", __name__)


@files_bp.route("/", methods=["GET"])
@require_permission("file:read")
def list_files():
    return jsonify(file_service.list_files())


@files_bp.route("/", methods=["POST"])
@require_permission("file:create")
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file_obj = request.files["file"]
    result, error = file_service.upload_file(
        file_obj,
        owner_id=g.current_user.get("user_id"),
        owner_name=g.current_user.get("username"),
    )
    if error:
        return jsonify({"error": error}), 400

    # service layer already logs FILE_UPLOAD
    return jsonify(result), 201


@files_bp.route("/<int:file_id>/info", methods=["GET"])
@require_permission("file:read")
def get_file_info(file_id):
    result, error = file_service.get_file_info(file_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(result)


@files_bp.route("/<int:file_id>", methods=["GET"])
@require_permission("file:read")
def download_file(file_id):
    file_record, error, filepath = file_service.download_file(file_id)
    if error:
        return jsonify({"error": error}), 404

    audit_service.create_log(
        user_id=g.current_user.get("user_id"),
        username=g.current_user.get("username"),
        action="FILE_DOWNLOAD",
        resource_type="file",
        resource_id=file_id,
        details=f"File '{file_record.original_filename}' downloaded",
        ip_address=request.remote_addr,
    )
    return send_file(
        filepath,
        download_name=file_record.original_filename,
        as_attachment=True,
    )


@files_bp.route("/<int:file_id>", methods=["PUT"])
@require_permission("file:update")
def update_file(file_id):
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file_obj = request.files["file"]
    result, error = file_service.update_file(
        file_id,
        file_obj,
        username=g.current_user.get("username"),
    )
    if error:
        return jsonify({"error": error}), 400

    # service layer already logs FILE_UPDATED
    return jsonify(result)


@files_bp.route("/<int:file_id>", methods=["DELETE"])
@require_permission("file:delete")
def delete_file(file_id):
    result, error = file_service.delete_file(
        file_id,
        username=g.current_user.get("username"),
    )
    if error:
        return jsonify({"error": error}), 400

    # service layer already logs FILE_DELETED
    return jsonify(result)
