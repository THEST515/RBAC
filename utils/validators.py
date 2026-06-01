import re

ALLOWED_EXTENSIONS = {
    "txt", "pdf", "png", "jpg", "jpeg", "gif",
    "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip",
}


def validate_username(username):
    if not username or len(username) < 3 or len(username) > 50:
        return False, "Username must be 3-50 characters"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""


def validate_password(password):
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain a lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain a digit"
    return True, ""


def validate_email(email):
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Invalid email format"
    return True, ""


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
