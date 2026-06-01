from extensions import db
from models.audit_log import AuditLog
from datetime import datetime


def create_log(user_id=None, username=None, action="", resource_type=None,
               resource_id=None, details=None, ip_address=None):
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.session.add(log)
    db.session.flush()
    return log


def query_logs(user_id=None, action=None, resource_type=None,
               start_date=None, end_date=None, page=1, per_page=20):
    q = AuditLog.query

    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            q = q.filter(AuditLog.timestamp >= sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            q = q.filter(AuditLog.timestamp <= ed)
        except ValueError:
            pass

    q = q.order_by(AuditLog.timestamp.desc())
    pagination = q.paginate(page=int(page), per_page=int(per_page), error_out=False)

    return {
        "items": [log.to_dict() for log in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }
