
from .four_modes import TradingMode, available_modes


class TradingModeController:

    def __init__(self):
        self.mode = TradingMode()

    def select(self, account, mode):
        account = account.upper()
        mode = mode.upper()

        # Selecting REAL never silently authorizes real money.
        self.mode = TradingMode(
            account=account,
            mode=mode,
            real_authorized=False,
        )

        return self.status()

    def authorize_real(self, confirmation=False):
        if self.mode.account != "REAL":
            raise RuntimeError(
                "REAL account must be selected first"
            )

        if confirmation is not True:
            raise PermissionError(
                "Explicit REAL trading authorization required"
            )

        self.mode.real_authorized = True

        return self.status()

    def revoke_real(self):
        self.mode.real_authorized = False
        return self.status()

    def status(self):
        return {
            "account": self.mode.account,
            "mode": self.mode.mode,
            "trading_mode": self.mode.name,
            "auto": self.mode.is_auto,
            "manual": self.mode.is_manual,
            "real_authorized": self.mode.real_authorized,
            "execution_available": self.mode.can_execute,
            "available_modes": list(available_modes()),
        }

# Compatibility alias for services using the legacy controller name.
# TradingModeController remains the canonical implementation.
ModeController = TradingModeController
