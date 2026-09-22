import time
from typing import Optional

from core.candle_engine import Candle
from core.signal_engine import Signal


class CandleCloseProtection:
    """
    Ensures signals are confirmed only from completed candles.

    SIGNAL-ONLY:
    This module performs validation only.
    It cannot place, modify, or close trades.
    """

    def __init__(
        self,
        clock=time.time,
    ):
        self.clock = clock

    # =================================================
    # CANDLE STATUS
    # =================================================

    def is_closed(
        self,
        candle: Candle,
        now: Optional[float] = None,
    ) -> bool:

        if now is None:
            now = self.clock()

        return now >= candle.end

    def is_forming(
        self,
        candle: Candle,
        now: Optional[float] = None,
    ) -> bool:

        return not self.is_closed(
            candle,
            now,
        )

    # =================================================
    # SIGNAL VALIDATION
    # =================================================

    def validate(
        self,
        signal: Signal,
        candle: Optional[Candle],
        now: Optional[float] = None,
    ) -> tuple:

        if not signal.valid:
            return (
                False,
                "INVALID_SIGNAL",
            )

        if signal.direction not in {
            "BUY",
            "SELL",
        }:
            return (
                False,
                "NOT_BUY_SELL",
            )

        if candle is None:
            return (
                False,
                "NO_CANDLE",
            )

        if not self.is_closed(
            candle,
            now,
        ):
            return (
                False,
                "CANDLE_STILL_FORMING",
            )

        if candle.symbol != signal.symbol:
            return (
                False,
                "SYMBOL_MISMATCH",
            )

        if candle.timeframe != signal.timeframe:
            return (
                False,
                "TIMEFRAME_MISMATCH",
            )

        return (
            True,
            "CANDLE_CONFIRMED",
        )

    # =================================================
    # CONFIRMED SIGNAL
    # =================================================

    def confirm(
        self,
        signal: Signal,
        candle: Optional[Candle],
        now: Optional[float] = None,
    ) -> tuple:

        allowed, reason = self.validate(
            signal,
            candle,
            now,
        )

        if not allowed:
            return (
                False,
                reason,
            )

        if not signal.candle_confirmed:
            return (
                False,
                "SIGNAL_CANDLE_CONFIRMATION_FAILED",
            )

        return (
            True,
            "CONFIRMED",
        )

    # =================================================
    # TIME REMAINING
    # =================================================

    def seconds_until_close(
        self,
        candle: Candle,
        now: Optional[float] = None,
    ) -> float:

        if now is None:
            now = self.clock()

        return max(
            0.0,
            float(candle.end) - float(now),
        )


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 9C - Candle Close Protection"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
