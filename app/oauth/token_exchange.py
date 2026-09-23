import json
import os
import urllib.parse
import urllib.request


DERIV_TOKEN_URL = "https://auth.deriv.com/oauth2/token"


class DerivOAuthTokenError(Exception):
    pass


def exchange_code(
    code,
    code_verifier,
    client_id=None,
    redirect_uri=None,
    opener=None,
):
    code = (code or "").strip()
    code_verifier = (code_verifier or "").strip()

    if not code:
        raise DerivOAuthTokenError("OAUTH_CODE_REQUIRED")

    if not code_verifier:
        raise DerivOAuthTokenError(
            "OAUTH_CODE_VERIFIER_REQUIRED"
        )

    client_id = (
        client_id
        or os.environ.get("DERIV_APP_ID")
        or "34tKg6v2jiqdiJett8MsP"
    )

    redirect_uri = (
        redirect_uri
        or os.environ.get(
            "DERIV_REDIRECT_URI",
            "",
        )
    )

    payload = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
    }).encode()

    request = urllib.request.Request(
        DERIV_TOKEN_URL,
        data=payload,
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )

    opener = opener or urllib.request.urlopen

    try:
        response = opener(request, timeout=15)
        raw = response.read().decode()
    except Exception as exc:
        raise DerivOAuthTokenError(
            f"OAUTH_TOKEN_REQUEST_FAILED:{type(exc).__name__}"
        ) from exc

    try:
        data = json.loads(raw)
    except Exception as exc:
        raise DerivOAuthTokenError(
            "OAUTH_TOKEN_RESPONSE_INVALID"
        ) from exc

    if not data.get("access_token"):
        raise DerivOAuthTokenError(
            data.get(
                "error",
                "OAUTH_ACCESS_TOKEN_MISSING",
            )
        )

    return {
        "access_token": data["access_token"],
        "token_type": data.get(
            "token_type",
            "Bearer",
        ),
        "expires_in": data.get("expires_in"),
        "refresh_token": data.get("refresh_token"),
    }
