from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class OAuthSession:
    state: str = ""
    code_verifier: str = ""
    created_at: str = ""
    authenticated: bool = False
    account_id: str = ""
    account_type: str = ""

    def create(self, state, code_verifier):
        self.state = state
        self.code_verifier = code_verifier
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.authenticated = False
        self.account_id = ""
        self.account_type = ""

    def verify_state(self, received_state):
        return bool(
            self.state
            and received_state
            and self.state == received_state
        )

    def authenticate(
        self,
        account_id="",
        account_type="",
    ):
        self.authenticated = True
        self.account_id = account_id or ""
        self.account_type = account_type or ""

    def clear(self):
        self.state = ""
        self.code_verifier = ""
        self.created_at = ""
        self.authenticated = False
        self.account_id = ""
        self.account_type = ""
