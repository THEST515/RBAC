import os

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config_map
from extensions import db

limiter = Limiter(key_func=get_remote_address)


def create_app(config_name="development"):
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    CORS(app)
    limiter.init_app(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    with app.app_context():
        from models.user import User
        from models.role import Role
        from models.permission import Permission
        from models.file_model import FileModel
        from models.audit_log import AuditLog

        db.create_all()

    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.roles import roles_bp
    from routes.permissions import permissions_bp
    from routes.files import files_bp
    from routes.audit import audit_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(roles_bp, url_prefix="/api/roles")
    app.register_blueprint(permissions_bp, url_prefix="/api/permissions")
    app.register_blueprint(files_bp, url_prefix="/api/files")
    app.register_blueprint(audit_bp, url_prefix="/api/audit-logs")

    @app.route("/")
    def index():
        return render_template("dashboard.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/users")
    def users_page():
        return render_template("users.html")

    @app.route("/roles")
    def roles_page():
        return render_template("roles.html")

    @app.route("/files")
    def files_page():
        return render_template("files.html")

    @app.route("/audit")
    def audit_page():
        return render_template("audit.html")

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large"}), 413

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src https://cdn.jsdelivr.net; "
            "img-src 'self' data:;"
        )
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
