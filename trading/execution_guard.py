class ExecutionGuard:
    """
    Safety gate for automatic trading.

    This layer validates whether an execution request is allowed.
    It does not place orders itself.
    """

    def __init__(
        self,
        *,
        symbol: str = "XAUUSD",
        trade_mode: str = "manual",
        auto_trade_enabled: bool = False,
        real_trading_enabled: bool = False,
        demo: bool = True,
        max_open_trades: int = 1,
    ):
        self.symbol = symbol
        self.trade_mode = trade_mode
        self.auto_trade_enabled = auto_trade_enabled
        self.real_trading_enabled = real_trading_enabled
        self.demo = demo
        self.max_open_trades = max_open_trades

    def validate(
        self,
        *,
        symbol: str,
        side: str,
        open_positions: int = 0,
    ) -> tuple[bool, str]:

        if symbol != self.symbol:
            return False, f"Unsupported symbol: {symbol}"

        if side not in {"BUY", "SELL"}:
            return False, f"Invalid side: {side}"

        if self.trade_mode != "auto":
            return False, "Auto trading mode is disabled"

        if not self.auto_trade_enabled:
            return False, "Auto trading is disabled"

        if open_positions >= self.max_open_trades:
            return False, "Maximum open trades reached"

        if not self.demo and not self.real_trading_enabled:
            return False, "Real trading is not explicitly enabled"

        return True, "Execution allowed"


# ------------------------------------------------------------
# FOUR USER TRADING MODES
# ------------------------------------------------------------

FOUR_TRADING_MODES = (
    "DEMO MANUAL",
    "DEMO AUTO",
    "REAL MANUAL",
    "REAL AUTO",
)

def normalize_trading_mode(account_mode: str, trade_mode: str) -> str:
    account = str(account_mode).strip().upper()
    mode = str(trade_mode).strip().upper()

    if account not in ("DEMO", "REAL"):
        raise ValueError("Account must be DEMO or REAL")

    if mode not in ("MANUAL", "AUTO"):
        raise ValueError("Trading mode must be MANUAL or AUTO")

    return f"{account} {mode}"


def is_real_mode(account_mode: str, trade_mode: str) -> bool:
    return normalize_trading_mode(
        account_mode,
        trade_mode
    ).startswith("REAL ")


def is_auto_mode(account_mode: str, trade_mode: str) -> bool:
    return normalize_trading_mode(
        account_mode,
        trade_mode
    ).endswith(" AUTO")
