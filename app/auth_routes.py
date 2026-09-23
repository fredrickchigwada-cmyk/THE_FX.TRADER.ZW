from flask import Blueprint, jsonify, request, session
from deriv.auth import DerivAuthenticator, DerivAuthenticationError

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}

    app_id = str(data.get("app_id", "")).strip()
    account_id = str(data.get("account_id", "")).strip()
    token = str(data.get("token", "")).strip()
    server = str(data.get("server", "demo")).strip().lower()

    if server not in {"demo", "real"}:
        return jsonify({
            "ok": False,
            "error": "Invalid server selection."
        }), 400

    if not app_id or not account_id or not token:
        return jsonify({
            "ok": False,
            "error": "Account ID, App ID and API Token are required."
        }), 400

    try:
        auth = DerivAuthenticator(
            app_id=app_id,
            token=token,
            account_id=account_id,
        )

        if not auth.configured():
            return jsonify({
                "ok": False,
                "error": "Deriv credentials are not configured."
            }), 401

        result = auth.validate()

        if not result:
            return jsonify({
                "ok": False,
                "error": "Deriv authentication failed."
            }), 401

        # Store only non-secret session state.
        # Never store the API token in browser localStorage.
        session["fx_authenticated"] = True
        session["fx_account_id"] = account_id
        session["fx_server"] = server

        # Real trading remains independently protected by the
        # existing execution/safety system.
        return jsonify({
            "ok": True,
            "authenticated": True,
            "account_id": account_id,
            "server": server,
            "message": "Deriv authentication successful."
        })

    except DerivAuthenticationError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 401

    except Exception:
        return jsonify({
            "ok": False,
            "error": "Authentication service error."
        }), 500


@auth_bp.post("/api/auth/logout")
def logout():
    session.clear()

    return jsonify({
        "ok": True,
        "authenticated": False
    })


@auth_bp.get("/api/auth/status")
def auth_status():
    return jsonify({
        "ok": True,
        "authenticated": bool(session.get("fx_authenticated")),
        "account_id": session.get("fx_account_id"),
        "server": session.get("fx_server", "demo"),
    })
