import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "rbac-dev-secret-key-change-in-prod")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "rbac-jwt-secret-change-in-prod")
    JWT_EXPIRATION_HOURS = 24
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {
        "txt", "pdf", "png", "jpg", "jpeg", "gif",
        "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip",
    }
    RATELIMIT_DEFAULT = "100 per minute"


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'rbac.db')}"
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
