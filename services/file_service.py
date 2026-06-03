import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models.file_model import FileModel
from models.audit_log import AuditLog
from utils.validators import allowed_file


def _safe_join(base, filename):
    """Join base and filename, verify result stays within base."""
    full = os.path.realpath(os.path.join(base, filename))
    if not full.startswith(os.path.realpath(base) + os.sep):
        return None
    return full


def list_files():
    return [f.to_dict() for f in FileModel.query.order_by(FileModel.created_at.desc()).all()]


def upload_file(file_obj, owner_id, owner_name):
    if not file_obj or not file_obj.filename:
        return None, "No file provided"

    if not allowed_file(file_obj.filename):
        return None, "File type not allowed"

    original_name = secure_filename(file_obj.filename)
    ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else ""
    uuid_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = _safe_join(upload_folder, uuid_name)
    if not filepath:
        return None, "Invalid file path"

    file_obj.save(filepath)
    size = os.path.getsize(filepath)

    file_record = FileModel(
        uuid_filename=uuid_name,
        original_filename=original_name,
        filepath=filepath,
        size=size,
        mime_type=file_obj.content_type,
        owner_id=owner_id,
    )
    db.session.add(file_record)
    db.session.flush()

    log = AuditLog(
        user_id=owner_id,
        username=owner_name,
        action="FILE_UPLOAD",
        resource_type="file",
        resource_id=file_record.id,
        details=f"File '{original_name}' uploaded ({size} bytes)",
    )
    db.session.add(log)
    db.session.commit()

    return file_record.to_dict(), None


def get_file_info(file_id):
    f = db.session.get(FileModel, file_id)
    if not f:
        return None, "File not found"
    return f.to_dict(), None


def download_file(file_id):
    f = db.session.get(FileModel, file_id)
    if not f:
        return None, "File not found", None

    if not os.path.exists(f.filepath):
        return None, "File missing on disk", None

    return f, None, f.filepath


def update_file(file_id, file_obj, username):
    f = db.session.get(FileModel, file_id)
    if not f:
        return None, "File not found"

    if not file_obj or not file_obj.filename:
        return None, "No file provided"

    if not allowed_file(file_obj.filename):
        return None, "File type not allowed"

    if os.path.exists(f.filepath):
        os.remove(f.filepath)

    original_name = secure_filename(file_obj.filename)
    ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else ""
    uuid_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = _safe_join(upload_folder, uuid_name)
    if not filepath:
        return None, "Invalid file path"

    file_obj.save(filepath)
    size = os.path.getsize(filepath)

    f.uuid_filename = uuid_name
    f.original_filename = original_name
    f.filepath = filepath
    f.size = size
    f.mime_type = file_obj.content_type

    log = AuditLog(
        user_id=f.owner_id,
        username=username,
        action="FILE_UPDATED",
        resource_type="file",
        resource_id=f.id,
        details=f"File '{original_name}' replaced ({size} bytes)",
    )
    db.session.add(log)
    db.session.commit()

    return f.to_dict(), None


def delete_file(file_id, username):
    f = db.session.get(FileModel, file_id)
    if not f:
        return None, "File not found"

    if os.path.exists(f.filepath):
        os.remove(f.filepath)

    db.session.delete(f)

    log = AuditLog(
        user_id=None,
        username=username,
        action="FILE_DELETED",
        resource_type="file",
        resource_id=file_id,
        details=f"File '{f.original_filename}' deleted by '{username}'",
    )
    db.session.add(log)
    db.session.commit()

    return {"deleted": True}, None
