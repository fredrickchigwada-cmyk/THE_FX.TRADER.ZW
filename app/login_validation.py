import re


EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def validate_login(email, password):
    errors = []

    email = (email or "").strip()
    password = password or ""

    if not email:
        errors.append("EMAIL_REQUIRED")
    elif not EMAIL_RE.match(email):
        errors.append("INVALID_EMAIL")

    if not password:
        errors.append("PASSWORD_REQUIRED")
    elif len(password) < 8:
        errors.append("PASSWORD_TOO_SHORT")

    return {
        "valid": not errors,
        "errors": errors,
    }
