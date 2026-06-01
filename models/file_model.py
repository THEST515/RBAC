from extensions import db


class FileModel(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    owner = db.relationship("User", backref="files")

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "size": self.size,
            "mime_type": self.mime_type,
            "owner_id": self.owner_id,
            "owner_name": self.owner.username if self.owner else "Unknown",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
