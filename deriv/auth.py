from dotenv import load_dotenv
load_dotenv()
import os
from dataclasses import dataclass
from typing import Optional

import requests


DERIV_API_BASE = "https://api.derivws.com"


class DerivAuthenticationError(Exception):
    """Raised when Deriv authentication fails."""


@dataclass
class DerivAuthResult:
    authenticated: bool
    account_id: Optional[str] = None
    message: str = ""


class DerivAuthenticator:
    """
    Handles the authenticated Deriv API session.

    Authentication uses a Deriv Personal Access Token (PAT).
    The token is loaded from the local environment and is never
    hard-coded into the source code.
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        token: Optional[str] = None,
        account_id: Optional[str] = None,
    ):
        self.app_id = (
            app_id
            or os.getenv("DERIV_APP_ID", "")
        ).strip()

        self.token = (
            token
            or os.getenv("DERIV_API_TOKEN", "")
        ).strip()

        self.account_id = (
            account_id
            or os.getenv("DERIV_ACCOUNT_ID", "")
        ).strip()

        self.authenticated = False

    def configured(self) -> bool:
        """
        Check whether the required credentials have been configured.
        """
        return bool(
            self.app_id
            and self.token
            and self.account_id
        )

    def headers(self) -> dict:
        """
        Headers required for PAT authentication.
        """
        if not self.configured():
            raise DerivAuthenticationError(
                "Deriv credentials are not configured."
            )

        return {
            "Authorization": f"Bearer {self.token}",
            "Deriv-App-ID": self.app_id,
            "Content-Type": "application/json",
        }

    def validate(self) -> DerivAuthResult:
        """
        Validate that the configured credentials can authenticate
        against the Deriv API.

        This does NOT place a trade.
        """

        if not self.configured():
            return DerivAuthResult(
                authenticated=False,
                account_id=None,
                message=(
                    "Deriv authentication is not configured. "
                    "Add DERIV_APP_ID, DERIV_API_TOKEN and "
                    "DERIV_ACCOUNT_ID to .env."
                ),
            )

        url = (
            f"{DERIV_API_BASE}"
            f"/trading/v1/options/accounts"
        )

        try:
            response = requests.get(
                url,
                headers=self.headers(),
                timeout=15,
            )

        except requests.RequestException as exc:
            return DerivAuthResult(
                authenticated=False,
                message=f"Network error: {exc}",
            )

        if response.status_code in (401, 403):
            return DerivAuthResult(
                authenticated=False,
                message=(
                    "Deriv rejected the authentication "
                    f"(HTTP {response.status_code})."
                ),
            )

        if not response.ok:
            return DerivAuthResult(
                authenticated=False,
                message=(
                    f"Deriv API returned HTTP "
                    f"{response.status_code}."
                ),
            )

        self.authenticated = True

        return DerivAuthResult(
            authenticated=True,
            account_id=self.account_id,
            message="Deriv authentication successful.",
        )

    def clear(self) -> None:
        """
        Clear the in-memory authentication state.
        """
        self.authenticated = False


    def get_authenticated_websocket_url(self) -> str:
        """Return a short-lived authenticated Deriv WebSocket URL."""
        if not self.configured():
            raise DerivAuthenticationError(
                "Deriv authentication is not configured."
            )

        if not self.authenticated:
            result = self.validate()
            if not result.authenticated:
                raise DerivAuthenticationError(
                    result.message or "Deriv authentication failed."
                )

        import requests

        url = (
            f"{DERIV_API_BASE}/trading/v1/options/accounts/"
            f"{self.account_id}/otp"
        )

        try:
            response = requests.post(
                url,
                headers=self.headers(),
                timeout=15,
            )
        except requests.RequestException as exc:
            raise DerivAuthenticationError(
                f"Deriv OTP request failed: {exc}"
            ) from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}

        if response.status_code != 200:
            raise DerivAuthenticationError(
                f"Deriv OTP endpoint returned HTTP "
                f"{response.status_code}: {payload}"
            )

        data = payload.get("data", {})
        ws_url = data.get("url") if isinstance(data, dict) else None

        if not ws_url:
            raise DerivAuthenticationError(
                f"Deriv OTP response did not contain a WebSocket URL: "
                f"{payload}"
            )

        return ws_url
