import os
from dataclasses import dataclass
from typing import Literal


Timeframe = Literal["M1", "M5", "M15", "M30", "H1"]
ServerMode = Literal["demo", "real"]
TradeMode = Literal["manual", "auto"]


@dataclass(frozen=True)
class Settings:
    # Application
    app_name: str = "THE_FX.TRADER.ZW"
    version: str = "1.0.0"

    # Trading instrument
    symbol: str = "XAUUSD"

    # Trading configuration
    timeframe: Timeframe = "M15"
    server_mode: ServerMode = "demo"
    trade_mode: TradeMode = "manual"

    # Safety
    auto_trade_enabled: bool = False
    real_trading_enabled: bool = False

    # Risk
    risk_per_trade_percent: float = 1.0
    max_daily_loss_percent: float = 3.0
    max_open_trades: int = 1

    # Alerts
    alerts_enabled: bool = True
    sound_enabled: bool = True
    vibration_enabled: bool = True

    # Server
    api_host: str = "127.0.0.1"
    api_port: int = 8000


def _bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


def load_settings() -> Settings:
    timeframe = os.getenv("TIMEFRAME", "M15").upper()

    allowed_timeframes = {"M1", "M5", "M15", "M30", "H1"}

    if timeframe not in allowed_timeframes:
        raise ValueError(
            f"Invalid TIMEFRAME={timeframe}. "
            f"Allowed: {sorted(allowed_timeframes)}"
        )

    server_mode = os.getenv("DERIV_SERVER", "demo").lower()

    if server_mode not in {"demo", "real"}:
        raise ValueError(
            "DERIV_SERVER must be either 'demo' or 'real'"
        )

    trade_mode = os.getenv("TRADE_MODE", "manual").lower()

    if trade_mode not in {"manual", "auto"}:
        raise ValueError(
            "TRADE_MODE must be either 'manual' or 'auto'"
        )

    risk = float(os.getenv("RISK_PER_TRADE_PERCENT", "1.0"))
    daily_loss = float(os.getenv("MAX_DAILY_LOSS_PERCENT", "3.0"))
    max_trades = int(os.getenv("MAX_OPEN_TRADES", "1"))

    if not 0 < risk <= 10:
        raise ValueError(
            "RISK_PER_TRADE_PERCENT must be between 0 and 10"
        )

    if not 0 < daily_loss <= 100:
        raise ValueError(
            "MAX_DAILY_LOSS_PERCENT must be between 0 and 100"
        )

    if max_trades < 1:
        raise ValueError(
            "MAX_OPEN_TRADES must be at least 1"
        )

    real_trading = _bool(
        os.getenv("REAL_TRADING_ENABLED"),
        False,
    )

    auto_trade = _bool(
        os.getenv("AUTO_TRADE_ENABLED"),
        False,
    )

    # Safety rule:
    # Real trading cannot be enabled accidentally.
    if server_mode == "real" and not real_trading:
        auto_trade = False

    return Settings(
        timeframe=timeframe,
        server_mode=server_mode,
        trade_mode=trade_mode,
        auto_trade_enabled=auto_trade,
        real_trading_enabled=real_trading,
        risk_per_trade_percent=risk,
        max_daily_loss_percent=daily_loss,
        max_open_trades=max_trades,
        alerts_enabled=_bool(
            os.getenv("ALERTS_ENABLED"),
            True,
        ),
        sound_enabled=_bool(
            os.getenv("SOUND_ENABLED"),
            True,
        ),
        vibration_enabled=_bool(
            os.getenv("VIBRATION_ENABLED"),
            True,
        ),
        api_host=os.getenv(
            "API_HOST",
            "127.0.0.1",
        ),
        api_port=int(
            os.getenv("API_PORT", "8000")
        ),
    )


settings = load_settings()
