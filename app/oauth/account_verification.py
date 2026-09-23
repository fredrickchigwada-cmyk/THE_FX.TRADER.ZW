import json
import urllib.request


DERIV_API_BASE = "https://api.derivws.com"
ACCOUNTS_PATH = "/trading/v1/options/accounts"


class DerivAccountVerificationError(Exception):
    pass


def get_accounts(access_token, opener=None):
    access_token = (access_token or "").strip()

    if not access_token:
        raise DerivAccountVerificationError(
            "ACCESS_TOKEN_REQUIRED"
        )

    request = urllib.request.Request(
        DERIV_API_BASE + ACCOUNTS_PATH,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    opener = opener or urllib.request.urlopen

    try:
        response = opener(request, timeout=15)
        raw = response.read().decode()
    except Exception as exc:
        raise DerivAccountVerificationError(
            f"ACCOUNT_REQUEST_FAILED:{type(exc).__name__}"
        ) from exc

    try:
        data = json.loads(raw)
    except Exception as exc:
        raise DerivAccountVerificationError(
            "ACCOUNT_RESPONSE_INVALID"
        ) from exc

    if isinstance(data.get("errors"), list) and data["errors"]:
        error = data["errors"][0]
        raise DerivAccountVerificationError(
            error.get("code", "ACCOUNT_REQUEST_FAILED")
        )

    return data.get("data", data)


def classify_account(account):
    if not isinstance(account, dict):
        return "UNKNOWN"

    account_type = str(
        account.get("account_type", "")
    ).lower()

    if account_type in ("demo", "virtual"):
        return "DEMO"

    if account_type in ("real", "live"):
        return "REAL"

    loginid = str(
        account.get("loginid", "")
    ).upper()

    if loginid.startswith("VRTC"):
        return "DEMO"

    return "UNKNOWN"


def normalize_accounts(payload):
    if isinstance(payload, list):
        accounts = payload
    elif isinstance(payload, dict):
        accounts = payload.get(
            "accounts",
            payload.get("data", [])
        )
    else:
        accounts = []

    if not isinstance(accounts, list):
        return []

    result = []

    for account in accounts:
        if not isinstance(account, dict):
            continue

        result.append({
            "account_id": (
                account.get("account_id")
                or account.get("loginid")
                or ""
            ),
            "loginid": account.get(
                "loginid",
                ""
            ),
            "currency": account.get(
                "currency",
                ""
            ),
            "account_type": classify_account(
                account
            ),
        })

    return result
