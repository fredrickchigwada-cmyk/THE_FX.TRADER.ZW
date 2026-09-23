
from dataclasses import dataclass

VALID_ACCOUNTS = ("DEMO", "REAL")
VALID_MODES = ("MANUAL", "AUTO")


@dataclass
class TradingMode:
    account: str = "DEMO"
    mode: str = "MANUAL"
    real_authorized: bool = False

    def __post_init__(self):
        self.account = self.account.upper()
        self.mode = self.mode.upper()

        if self.account not in VALID_ACCOUNTS:
            raise ValueError("Account must be DEMO or REAL")

        if self.mode not in VALID_MODES:
            raise ValueError("Mode must be MANUAL or AUTO")

    @property
    def name(self):
        return f"{self.account} {self.mode}"

    @property
    def is_demo(self):
        return self.account == "DEMO"

    @property
    def is_real(self):
        return self.account == "REAL"

    @property
    def is_auto(self):
        return self.mode == "AUTO"

    @property
    def is_manual(self):
        return self.mode == "MANUAL"

    @property
    def can_execute(self):
        if self.is_demo:
            return True

        return self.real_authorized


def available_modes():
    return (
        "DEMO MANUAL",
        "DEMO AUTO",
        "REAL MANUAL",
        "REAL AUTO",
    )
