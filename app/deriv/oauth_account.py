import json
import urllib.request
import urllib.error


DERIV_API_BASE = "https://api.derivws.com"
OTP_PATH = "/trading/v1/options/accounts/{account_id}/otp"


class DerivAccountError(Exception):
    pass


class DerivOAuthAccount:
    """
    Connects an OAuth Bearer token to the Deriv
    account-specific authenticated WebSocket layer.

    No password or PAT is handled here.
    """

    def __init__(self, access_token):
        access_token = (access_token or "").strip()

        if not access_token:
            raise DerivAccountError(
                "ACCESS_TOKEN_REQUIRED"
            )

        self.access_token = access_token
        self.account_id = ""
        self.account_type = ""
        self.ws_url = ""
        self.connected = False

    def _otp_request(self, account_id, opener=None):
        account_id = (account_id or "").strip()

        if not account_id:
            raise DerivAccountError(
                "ACCOUNT_ID_REQUIRED"
            )

        url = DERIV_API_BASE + OTP_PATH.format(
            account_id=account_id
        )

        request = urllib.request.Request(
            url,
            data=b"{}",
            headers={
                "Authorization":
                    f"Bearer {self.access_token}",
                "Content-Type":
                    "application/json",
                "Accept":
                    "application/json",
            },
            method="POST",
        )

        opener = opener or urllib.request.urlopen

        try:
            response = opener(
                request,
                timeout=15,
            )
            raw = response.read().decode()
        except Exception as exc:
            raise DerivAccountError(
                f"OTP_REQUEST_FAILED:{type(exc).__name__}"
            ) from exc

        try:
            return json.loads(raw)
        except Exception as exc:
            raise DerivAccountError(
                "OTP_RESPONSE_INVALID"
            ) from exc

    def connect_account(
        self,
        account_id,
        account_type,
        opener=None,
    ):
        account_type = (
            account_type or ""
        ).upper().strip()

        if account_type not in (
            "DEMO",
            "REAL",
        ):
            raise DerivAccountError(
                "INVALID_ACCOUNT_TYPE"
            )

        data = self._otp_request(
            account_id,
            opener=opener,
        )

        payload = data.get("data", data)

        ws_url = payload.get("url")

        if not ws_url:
            raise DerivAccountError(
                "AUTHENTICATED_WS_URL_MISSING"
            )

        expected_endpoint = (
            "/ws/demo"
            if account_type == "DEMO"
            else "/ws/real"
        )

        if expected_endpoint not in ws_url:
            raise DerivAccountError(
                "ACCOUNT_TYPE_ENDPOINT_MISMATCH"
            )

        self.account_id = account_id
        self.account_type = account_type
        self.ws_url = ws_url
        self.connected = True

        return self.snapshot()

    def xauusd_mapping(self):
        return {
            "symbol": "XAUUSD",
            "deriv_symbol": "frxXAUUSD",
        }

    def disconnect(self):
        self.connected = False
        self.ws_url = ""
        self.account_id = ""
        self.account_type = ""

    def snapshot(self):
        return {
            "connected": self.connected,
            "account_id": self.account_id,
            "account_type": self.account_type,
            "ws_url_present": bool(self.ws_url),
            "symbol": "XAUUSD",
            "deriv_symbol": "frxXAUUSD",
        }
