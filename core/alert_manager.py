import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AlertEvent:
    symbol: str
    timeframe: str
    direction: str
    strength: int
    message: str
    timestamp: float
    alert_type: str = "SIGNAL"


class AlertManager:
    """
    Signal alert manager.

    Stage 10A:
    - Creates alert events
    - Stores alert history
    - Filters enabled directions
    - Applies minimum strength
    - Provides test alerts

    SIGNAL-ONLY:
    This module cannot place, modify, or close trades.
    """

    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

    def __init__(
        self,
        buy_enabled: bool = True,
        sell_enabled: bool = True,
        wait_enabled: bool = False,
        minimum_strength: int = 6,
        cooldown_seconds: int = 300,
    ):
        self.buy_enabled = buy_enabled
        self.sell_enabled = sell_enabled
        self.wait_enabled = wait_enabled

        self.minimum_strength = max(
            1,
            min(10, int(minimum_strength)),
        )

        self.cooldown_seconds = max(
            0,
            int(cooldown_seconds),
        )

        self.events: List[AlertEvent] = []
        self.last_alert_times = {}

    # =================================================
    # CONFIGURATION
    # =================================================

    def set_direction_enabled(
        self,
        direction: str,
        enabled: bool,
    ):
        direction = direction.upper()

        if direction == self.BUY:
            self.buy_enabled = bool(enabled)

        elif direction == self.SELL:
            self.sell_enabled = bool(enabled)

        elif direction == self.WAIT:
            self.wait_enabled = bool(enabled)

    def is_direction_enabled(
        self,
        direction: str,
    ) -> bool:

        direction = direction.upper()

        if direction == self.BUY:
            return self.buy_enabled

        if direction == self.SELL:
            return self.sell_enabled

        if direction == self.WAIT:
            return self.wait_enabled

        return False

    def set_minimum_strength(
        self,
        strength: int,
    ):
        self.minimum_strength = max(
            1,
            min(10, int(strength)),
        )

    def set_cooldown(
        self,
        seconds: int,
    ):
        self.cooldown_seconds = max(
            0,
            int(seconds),
        )

    # =================================================
    # FILTERING
    # =================================================

    def should_alert(
        self,
        direction: str,
        strength: int,
        symbol: str,
        timeframe: str,
        now: Optional[float] = None,
    ) -> tuple:

        if now is None:
            now = time.time()

        direction = direction.upper()

        if direction not in {
            self.BUY,
            self.SELL,
            self.WAIT,
        }:
            return False, "INVALID_DIRECTION"

        if not self.is_direction_enabled(
            direction
        ):
            return False, "DIRECTION_DISABLED"

        try:
            strength = int(strength)
        except (TypeError, ValueError):
            return False, "INVALID_STRENGTH"

        if strength < self.minimum_strength:
            return False, "STRENGTH_TOO_LOW"

        key = (
            symbol,
            timeframe,
            direction,
        )

        last_time = self.last_alert_times.get(
            key
        )

        if last_time is not None:

            elapsed = now - last_time

            if elapsed < self.cooldown_seconds:

                return (
                    False,
                    "ALERT_COOLDOWN",
                )

        return True, "ALERT_ALLOWED"

    # =================================================
    # CREATE ALERT
    # =================================================

    def create_alert(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        strength: int,
        message: str,
        now: Optional[float] = None,
        alert_type: str = "SIGNAL",
    ) -> Optional[AlertEvent]:

        if now is None:
            now = time.time()

        allowed, reason = self.should_alert(
            direction=direction,
            strength=strength,
            symbol=symbol,
            timeframe=timeframe,
            now=now,
        )

        if not allowed:
            return None

        event = AlertEvent(
            symbol=symbol,
            timeframe=timeframe,
            direction=direction.upper(),
            strength=int(strength),
            message=str(message),
            timestamp=now,
            alert_type=alert_type,
        )

        self.events.append(event)

        self.last_alert_times[
            (
                symbol,
                timeframe,
                direction.upper(),
            )
        ] = now

        return event

    # =================================================
    # TEST ALERT
    # =================================================

    def test_alert(
        self,
        direction: str = "BUY",
        now: Optional[float] = None,
    ) -> Optional[AlertEvent]:

        return self.create_alert(
            symbol="TEST",
            timeframe="TEST",
            direction=direction,
            strength=10,
            message=(
                "THE_FX.TRADER.BOT.ZW "
                "TEST ALERT"
            ),
            now=now,
            alert_type="TEST",
        )

    # =================================================
    # HISTORY
    # =================================================

    def all_events(self) -> List[AlertEvent]:
        return list(self.events)

    def latest(self) -> Optional[AlertEvent]:

        if not self.events:
            return None

        return self.events[-1]

    def clear(self):
        self.events.clear()
        self.last_alert_times.clear()

    # =================================================
    # STATUS
    # =================================================

    def settings(self) -> dict:

        return {
            "buy_enabled": self.buy_enabled,
            "sell_enabled": self.sell_enabled,
            "wait_enabled": self.wait_enabled,
            "minimum_strength": self.minimum_strength,
            "cooldown_seconds": self.cooldown_seconds,
        }


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 10A - Alert Manager"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
