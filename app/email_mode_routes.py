from flask import Blueprint, jsonify, request

from database.email_mode_service import EmailModeService

email_mode_bp = Blueprint(
    "email_mode",
    __name__,
    url_prefix="/api/email-mode",
)

service = EmailModeService()


def _email():
    data = request.get_json(silent=True) or {}
    return (data.get("email") or "").strip()


@email_mode_bp.post("/login")
def email_login():
    try:
        result = service.login(_email())
        return jsonify({
            "ok": True,
            "status": result,
        })
    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400


@email_mode_bp.post("/select")
def select_mode():
    try:
        data = request.get_json(silent=True) or {}

        result = service.select_mode(
            _email(),
            data.get("account", "DEMO"),
            data.get("mode", "MANUAL"),
        )

        return jsonify({
            "ok": True,
            "status": result,
        })
    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400


@email_mode_bp.post("/real/authorize")
def authorize_real():
    try:
        data = request.get_json(silent=True) or {}

        if data.get("confirmation") is not True:
            return jsonify({
                "ok": False,
                "error": "Explicit REAL authorization is required",
            }), 400

        result = service.authorize_real(
            _email(),
            True,
        )

        return jsonify({
            "ok": True,
            "status": result,
        })
    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400


@email_mode_bp.post("/real/revoke")
def revoke_real():
    try:
        result = service.revoke_real(_email())

        return jsonify({
            "ok": True,
            "status": result,
        })
    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400


@email_mode_bp.post("/status")
def email_mode_status():
    try:
        result = service.status(_email())

        return jsonify({
            "ok": True,
            "status": result,
        })
    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400
