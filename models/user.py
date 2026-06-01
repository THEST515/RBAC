from extensions import db

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    roles = db.relationship("Role", secondary=user_roles, back_populates="users", lazy="joined")

    def has_permission(self, permission_name):
        for role in self.roles:
            for perm in role.permissions:
                if perm.name == permission_name:
                    return True
        return False

    def get_permissions(self):
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.name)
        return perms

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "roles": [{"id": r.id, "name": r.name} for r in self.roles],
            "permissions": list(self.get_permissions()),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
