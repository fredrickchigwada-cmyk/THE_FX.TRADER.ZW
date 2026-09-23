
from flask import Blueprint, jsonify, request

from trading.mode_controller import TradingModeController

mode_bp = Blueprint(
    "trading_mode",
    __name__,
    url_prefix="/api/trading",
)

controller = TradingModeController()


@mode_bp.get("/mode")
def get_mode():
    return jsonify({
        "ok": True,
        **controller.status(),
    })


@mode_bp.post("/mode")
def set_mode():
    data = request.get_json(silent=True) or {}

    account = data.get("account")
    mode = data.get("mode")

    if account not in ("DEMO", "REAL"):
        return jsonify({
            "ok": False,
            "error": "Account must be DEMO or REAL",
        }), 400

    if mode not in ("MANUAL", "AUTO"):
        return jsonify({
            "ok": False,
            "error": "Mode must be MANUAL or AUTO",
        }), 400

    result = controller.select(account, mode)

    return jsonify({
        "ok": True,
        **result,
    })


@mode_bp.post("/real/authorize")
def authorize_real():
    data = request.get_json(silent=True) or {}

    if data.get("confirmation") is not True:
        return jsonify({
            "ok": False,
            "error": "Explicit REAL authorization required",
        }), 403

    try:
        result = controller.authorize_real(
            confirmation=True
        )

        return jsonify({
            "ok": True,
            **result,
        })

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 400


@mode_bp.post("/real/revoke")
def revoke_real():
    return jsonify({
        "ok": True,
        **controller.revoke_real(),
    })
