from app.oauth.token_exchange import exchange_code
import os

from flask import (
    Blueprint,
    redirect,
    request,
    session,
    jsonify,
)

from .deriv_oauth import DerivOAuth
from .oauth_session import OAuthSession
from .account_verification import (
    get_accounts,
    normalize_accounts,
)


oauth_bp = Blueprint(
    "deriv_oauth",
    __name__,
    url_prefix="/api/oauth",
)

_oauth_session = OAuthSession()


def _get_oauth():
    redirect_uri = os.environ.get(
        "DERIV_REDIRECT_URI",
        "",
    )

    return DerivOAuth(
        client_id=os.environ.get(
            "DERIV_APP_ID",
            "34tKg6v2jiqdiJett8MsP",
        ),
        redirect_uri=redirect_uri,
    )


@oauth_bp.get("/login")
def oauth_login():
    oauth = _get_oauth()
    auth = oauth.create_authorization()

    _oauth_session.create(
        auth["state"],
        auth["code_verifier"],
    )

    session["deriv_oauth_state"] = auth["state"]

    return redirect(auth["authorization_url"])


@oauth_bp.get("/status")
def oauth_status():
    return jsonify({
        "authenticated": _oauth_session.authenticated,
        "account_id": _oauth_session.account_id,
        "account_type": _oauth_session.account_type,
        "oauth_state_present": bool(
            _oauth_session.state
        ),
    })


@oauth_bp.get("/callback")
def oauth_callback():
    error = request.args.get("error")

    if error:
        _oauth_session.clear()

        return jsonify({
            "ok": False,
            "error": "DERIV_OAUTH_DENIED",
            "detail": error,
        }), 400

    code = request.args.get("code")
    received_state = request.args.get("state")

    if not code:
        return jsonify({
            "ok": False,
            "error": "OAUTH_CODE_MISSING",
        }), 400

    if not received_state:
        return jsonify({
            "ok": False,
            "error": "OAUTH_STATE_MISSING",
        }), 400

    stored_state = session.get(
        "deriv_oauth_state",
        "",
    )

    if not _oauth_session.verify_state(
        received_state
    ):
        _oauth_session.clear()

        return jsonify({
            "ok": False,
            "error": "OAUTH_STATE_MISMATCH",
        }), 400

    if (
        stored_state
        and stored_state != received_state
    ):
        _oauth_session.clear()

        return jsonify({
            "ok": False,
            "error": "SESSION_STATE_MISMATCH",
        }), 400

    # Exchange the authorization code server-side.
    code_verifier = _oauth_session.code_verifier

    if not code_verifier:
        _oauth_session.clear()
        session.pop("deriv_oauth_state", None)

        return jsonify({
            "ok": False,
            "authenticated": False,
            "error": "OAUTH_CODE_VERIFIER_MISSING",
        }), 400

    try:
        token_payload = exchange_code(
            authorization_code,
            code_verifier,
            os.environ.get(
                "DERIV_REDIRECT_URI",
                "",
            ),
        )
    except Exception as exc:
        _oauth_session.clear()
        session.pop("deriv_oauth_state", None)

        return jsonify({
            "ok": False,
            "authenticated": False,
            "error": "OAUTH_TOKEN_EXCHANGE_FAILED",
            "message": str(exc),
        }), 502

    access_token = (
        token_payload.get("access_token", "")
        if isinstance(token_payload, dict)
        else ""
    )

    if not access_token:
        _oauth_session.clear()
        session.pop("deriv_oauth_state", None)

        return jsonify({
            "ok": False,
            "authenticated": False,
            "error": "OAUTH_ACCESS_TOKEN_MISSING",
        }), 502

    session["deriv_access_token"] = access_token
    session["deriv_oauth_authenticated"] = True

    _oauth_session.authenticate()

    session.pop("deriv_oauth_state", None)

    return jsonify({
        "ok": True,
        "authenticated": True,
        "real_order": False,
        "status": "AUTHENTICATED",
        "token_received": True,
    })
    #
    # The secure server-side token exchange will be
    # added in the next integration stage.

    session.pop(
        "deriv_oauth_state",
        None,
    )

    return jsonify({
        "ok": True,
        "status": "AUTHORIZATION_CODE_RECEIVED",
        "message":
            "Deriv authorization code received. "
            "Server-side exchange is pending.",
        "code_received": True,
        "token_received": False,
        "real_order": False,
    })


@oauth_bp.post("/logout")
def oauth_logout():
    _oauth_session.clear()

    session.pop(
        "deriv_oauth_state",
        None,
    )

    return jsonify({
        "ok": True,
        "authenticated": False,
    })


@oauth_bp.get("/accounts")
def oauth_accounts():
    access_token = session.get(
        "deriv_access_token",
        "",
    )

    if not access_token:
        return jsonify({
            "ok": False,
            "authenticated": False,
            "error": "DERIV_NOT_AUTHENTICATED",
        }), 401

    try:
        payload = get_accounts(
            access_token
        )

        accounts = normalize_accounts(
            payload
        )

        return jsonify({
            "ok": True,
            "authenticated": True,
            "accounts": accounts,
            "xauusd": {
                "symbol": "XAUUSD",
                "deriv_symbol": "frxXAUUSD",
            },
        })

    except Exception:
        return jsonify({
            "ok": False,
            "authenticated": True,
            "error": "DERIV_ACCOUNT_LOOKUP_FAILED",
        }), 502
