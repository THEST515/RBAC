from extensions import db


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    resource = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)

    roles = db.relationship("Role", secondary="role_permissions", back_populates="permissions")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "resource": self.resource,
            "action": self.action,
            "description": self.description,
        }
