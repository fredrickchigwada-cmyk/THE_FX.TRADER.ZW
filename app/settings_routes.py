from flask import Blueprint, jsonify, request

from app.settings_api import SettingsManager


settings_bp = Blueprint("settings_bp", __name__)
settings_manager = SettingsManager()


@settings_bp.get("/api/v1/settings")
def get_settings():
    return jsonify({
        "status": "OK",
        "settings": settings_manager.snapshot(),
    })


@settings_bp.post("/api/v1/settings")
def update_settings():
    payload = request.get_json(silent=True) or {}

    try:
        settings = settings_manager.update(**payload)

        return jsonify({
            "status": "OK",
            "settings": settings_manager.snapshot(),
        })

    except (ValueError, TypeError) as exc:
        return jsonify({
            "status": "ERROR",
            "message": str(exc),
        }), 400
