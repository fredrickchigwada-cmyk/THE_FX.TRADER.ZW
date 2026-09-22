from dataclasses import dataclass, field
from typing import List


@dataclass
class AlertConfig:
    """
    Central configuration for THE_FX.TRADER.BOT.ZW alerts.

    SIGNAL-ONLY:
    Alert configuration cannot place, modify, or close trades.
    """

    alerts_enabled: bool = True

    buy_enabled: bool = True
    sell_enabled: bool = True
    wait_enabled: bool = False

    sound_enabled: bool = True
    vibration_enabled: bool = True

    minimum_strength: int = 6
    cooldown_seconds: int = 300

    selected_markets: List[str] = field(
        default_factory=lambda: [
            "XAUUSD",
            "BTCUSD",
            "STEP INDEX",
            "VOLATILITY 75",
        ]
    )

    selected_timeframes: List[str] = field(
        default_factory=lambda: [
            "M1",
            "M3",
            "M5",
            "M15",
            "M30",
            "H1",
            "H4",
        ]
    )

    def __post_init__(self):

        self.minimum_strength = max(
            1,
            min(
                10,
                int(self.minimum_strength),
            ),
        )

        self.cooldown_seconds = max(
            0,
            int(self.cooldown_seconds),
        )

        self.selected_markets = list(
            dict.fromkeys(
                self.selected_markets
            )
        )

        self.selected_timeframes = list(
            dict.fromkeys(
                self.selected_timeframes
            )
        )

    # ================================================
    # ALERT MASTER SWITCH
    # ================================================

    def set_alerts_enabled(
        self,
        enabled: bool,
    ):

        self.alerts_enabled = bool(
            enabled
        )

    # ================================================
    # DIRECTIONS
    # ================================================

    def set_buy_enabled(
        self,
        enabled: bool,
    ):

        self.buy_enabled = bool(
            enabled
        )

    def set_sell_enabled(
        self,
        enabled: bool,
    ):

        self.sell_enabled = bool(
            enabled
        )

    def set_wait_enabled(
        self,
        enabled: bool,
    ):

        self.wait_enabled = bool(
            enabled
        )

    # ================================================
    # SOUND / VIBRATION
    # ================================================

    def set_sound_enabled(
        self,
        enabled: bool,
    ):

        self.sound_enabled = bool(
            enabled
        )

    def set_vibration_enabled(
        self,
        enabled: bool,
    ):

        self.vibration_enabled = bool(
            enabled
        )

    # ================================================
    # STRENGTH
    # ================================================

    def set_minimum_strength(
        self,
        strength: int,
    ):

        self.minimum_strength = max(
            1,
            min(
                10,
                int(strength),
            ),
        )

    # ================================================
    # COOLDOWN
    # ================================================

    def set_cooldown(
        self,
        seconds: int,
    ):

        self.cooldown_seconds = max(
            0,
            int(seconds),
        )

    # ================================================
    # MARKETS
    # ================================================

    def set_markets(
        self,
        markets: List[str],
    ):

        self.selected_markets = list(
            dict.fromkeys(
                str(market).upper()
                for market in markets
                if str(market).strip()
            )
        )

    def add_market(
        self,
        market: str,
    ):

        market = str(
            market
        ).strip().upper()

        if (
            market
            and market not in self.selected_markets
        ):

            self.selected_markets.append(
                market
            )

    def remove_market(
        self,
        market: str,
    ):

        market = str(
            market
        ).strip().upper()

        self.selected_markets = [
            item
            for item in self.selected_markets
            if item != market
        ]

    # ================================================
    # TIMEFRAMES
    # ================================================

    def set_timeframes(
        self,
        timeframes: List[str],
    ):

        self.selected_timeframes = list(
            dict.fromkeys(
                str(timeframe).upper()
                for timeframe in timeframes
                if str(timeframe).strip()
            )
        )

    def add_timeframe(
        self,
        timeframe: str,
    ):

        timeframe = str(
            timeframe
        ).strip().upper()

        if (
            timeframe
            and timeframe not in self.selected_timeframes
        ):

            self.selected_timeframes.append(
                timeframe
            )

    def remove_timeframe(
        self,
        timeframe: str,
    ):

        timeframe = str(
            timeframe
        ).strip().upper()

        self.selected_timeframes = [
            item
            for item in self.selected_timeframes
            if item != timeframe
        ]

    # ================================================
    # FILTER HELPERS
    # ================================================

    def market_enabled(
        self,
        market: str,
    ) -> bool:

        return (
            str(market).upper()
            in self.selected_markets
        )

    def timeframe_enabled(
        self,
        timeframe: str,
    ) -> bool:

        return (
            str(timeframe).upper()
            in self.selected_timeframes
        )

    def direction_enabled(
        self,
        direction: str,
    ) -> bool:

        if not self.alerts_enabled:
            return False

        direction = str(
            direction
        ).upper()

        if direction == "BUY":
            return self.buy_enabled

        if direction == "SELL":
            return self.sell_enabled

        if direction == "WAIT":
            return self.wait_enabled

        return False

    # ================================================
    # SERIALIZATION
    # ================================================

    def to_dict(self) -> dict:

        return {
            "alerts_enabled":
                self.alerts_enabled,

            "buy_enabled":
                self.buy_enabled,

            "sell_enabled":
                self.sell_enabled,

            "wait_enabled":
                self.wait_enabled,

            "sound_enabled":
                self.sound_enabled,

            "vibration_enabled":
                self.vibration_enabled,

            "minimum_strength":
                self.minimum_strength,

            "cooldown_seconds":
                self.cooldown_seconds,

            "selected_markets":
                list(self.selected_markets),

            "selected_timeframes":
                list(self.selected_timeframes),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ):

        if not isinstance(data, dict):
            raise TypeError(
                "Alert configuration must be a dictionary."
            )

        return cls(
            alerts_enabled=data.get(
                "alerts_enabled",
                True,
            ),

            buy_enabled=data.get(
                "buy_enabled",
                True,
            ),

            sell_enabled=data.get(
                "sell_enabled",
                True,
            ),

            wait_enabled=data.get(
                "wait_enabled",
                False,
            ),

            sound_enabled=data.get(
                "sound_enabled",
                True,
            ),

            vibration_enabled=data.get(
                "vibration_enabled",
                True,
            ),

            minimum_strength=data.get(
                "minimum_strength",
                6,
            ),

            cooldown_seconds=data.get(
                "cooldown_seconds",
                300,
            ),

            selected_markets=data.get(
                "selected_markets",
                [],
            ),

            selected_timeframes=data.get(
                "selected_timeframes",
                [],
            ),
        )


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 10B - Alert Configuration"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
