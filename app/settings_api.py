from dataclasses import asdict, dataclass
from pathlib import Path
import json


SETTINGS_FILE = Path("database/settings.json")


@dataclass
class AppSettings:
    symbol: str = "XAUUSD"
    timeframe: str = "M15"

    trade_mode: str = "AUTO"
    auto_trade_enabled: bool = True
    real_trading_enabled: bool = False

    risk_per_trade: float = 1.0
    max_daily_loss: float = 3.0
    max_open_trades: int = 1

    min_lot: float = 0.01
    max_lot: float = 0.50
    lot_step: float = 0.01
    default_lot: float = 0.01
    risk_based_sizing: bool = True

    alerts_enabled: bool = True
    sound_enabled: bool = True
    vibration_enabled: bool = True

    def to_dict(self):
        return asdict(self)


class SettingsManager:
    ALLOWED_TIMEFRAMES = {"M1", "M5", "M15", "M30", "H1"}

    def __init__(self, path=SETTINGS_FILE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = AppSettings()
        self.load()

    def load(self):
        if not self.path.exists():
            self.save()
            return self.settings

        try:
            data = json.loads(self.path.read_text())
            defaults = AppSettings().to_dict()

            for key in defaults:
                if key in data:
                    setattr(self.settings, key, data[key])

        except (OSError, ValueError, TypeError):
            self.settings = AppSettings()

        self._enforce_safety()
        return self.settings

    def save(self):
        self._enforce_safety()
        self.path.write_text(
            json.dumps(self.settings.to_dict(), indent=2)
        )
        return self.settings

    def _enforce_safety(self):
        # XAUUSD-only system.
        self.settings.symbol = "XAUUSD"

        if self.settings.timeframe not in self.ALLOWED_TIMEFRAMES:
            self.settings.timeframe = "M15"

        # Stage 20 remains DEMO-only.
        self.settings.trade_mode = "DEMO"

        # Real trading cannot be enabled by settings.
        self.settings.real_trading_enabled = False

        # Therefore automatic execution remains locked.
        self.settings.auto_trade_enabled = False

        self.settings.risk_per_trade = max(
            0.01,
            min(float(self.settings.risk_per_trade), 100.0)
        )

        self.settings.max_daily_loss = max(
            0.01,
            min(float(self.settings.max_daily_loss), 100.0)
        )

        self.settings.max_open_trades = max(
            1,
            int(self.settings.max_open_trades)
        )

        self.settings.min_lot = 0.01
        self.settings.max_lot = 0.50
        self.settings.lot_step = 0.01

        self.settings.default_lot = max(
            self.settings.min_lot,
            min(
                float(self.settings.default_lot),
                self.settings.max_lot
            )
        )

    def update(self, **changes):
        allowed = {
            "timeframe",
            "risk_per_trade",
            "max_daily_loss",
            "max_open_trades",
            "default_lot",
            "risk_based_sizing",
            "alerts_enabled",
            "sound_enabled",
            "vibration_enabled",
        }

        # These are intentionally NOT accepted:
        # auto_trade_enabled
        # real_trading_enabled
        # trade_mode
        #
        # They are security-controlled values.

        unknown = set(changes) - allowed

        if unknown:
            raise ValueError(
                f"Unsupported or protected settings: "
                f"{sorted(unknown)}"
            )

        for key, value in changes.items():
            setattr(self.settings, key, value)

        self._enforce_safety()
        self.save()

        return self.settings

    def snapshot(self):
        self._enforce_safety()

        data = self.settings.to_dict()

        data["lot_range"] = {
            "min": self.settings.min_lot,
            "max": self.settings.max_lot,
            "step": self.settings.lot_step,
        }

        data["safety"] = {
            "demo_only": True,
            "auto_trade_locked": True,
            "real_trading_locked": True,
        }

        return data
