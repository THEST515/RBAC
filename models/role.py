from extensions import db

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles", lazy="joined")
    users = db.relationship("User", secondary="user_roles", back_populates="roles")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": [{"id": p.id, "name": p.name} for p in self.permissions],
            "user_count": len(self.users),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
