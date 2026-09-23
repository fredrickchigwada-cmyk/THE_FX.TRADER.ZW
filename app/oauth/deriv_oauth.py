import os
from urllib.parse import urlencode

from .pkce import generate_pkce


DERIV_AUTH_URL = "https://auth.deriv.com/oauth2/auth"
DERIV_TOKEN_URL = "https://auth.deriv.com/oauth2/token"
DERIV_API_BASE = "https://api.derivws.com"


class DerivOAuth:
    def __init__(
        self,
        client_id=None,
        redirect_uri="",
    ):
        self.client_id = (
            client_id
            or os.environ.get(
                "DERIV_APP_ID",
                "34tKg6v2jiqdiJett8MsP",
            )
        )

        self.redirect_uri = (
            redirect_uri
            or os.environ.get(
                "DERIV_REDIRECT_URI",
                "",
            )
        )

    def create_authorization(self):
        pkce = generate_pkce()

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "trade",
            "state": pkce["state"],
            "code_challenge": pkce["code_challenge"],
            "code_challenge_method": "S256",
        }

        return {
            "authorization_url":
                DERIV_AUTH_URL + "?" + urlencode(params),
            "state": pkce["state"],
            "code_verifier": pkce["code_verifier"],
            "code_challenge": pkce["code_challenge"],
            "redirect_uri": self.redirect_uri,
            "scope": "trade",
        }
