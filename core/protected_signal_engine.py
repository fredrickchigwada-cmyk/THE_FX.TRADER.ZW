import time
from typing import List, Optional

from core.candle_engine import Candle
from core.candle_close_protection import CandleCloseProtection
from core.signal_engine import Signal, SignalEngine
from core.signal_lifecycle import SignalLifecycle
from core.signal_protection import (
    ProtectedSignal,
    SignalProtection,
)


class ProtectedSignalEngine:
    """
    Complete protected signal pipeline.

    Handles:
    - Signal generation
    - Candle-close confirmation
    - Duplicate protection
    - Cooldown
    - Expiry
    - Price invalidation
    - Stale-data protection
    - Signal lifecycle events

    SIGNAL-ONLY:
    No trade execution is implemented.
    """

    def __init__(
        self,
        signal_engine: Optional[SignalEngine] = None,
        protection: Optional[SignalProtection] = None,
        candle_protection: Optional[
            CandleCloseProtection
        ] = None,
        lifecycle: Optional[
            SignalLifecycle
        ] = None,
    ):

        self.signal_engine = (
            signal_engine
            or SignalEngine()
        )

        self.protection = (
            protection
            or SignalProtection()
        )

        self.candle_protection = (
            candle_protection
            or CandleCloseProtection()
        )

        self.lifecycle = (
            lifecycle
            or SignalLifecycle()
        )

    # =================================================
    # GENERATE
    # =================================================

    def generate(
        self,
        symbol: str,
        timeframe: str,
        candles: List[Candle],
    ) -> Signal:

        return self.signal_engine.generate(
            symbol,
            timeframe,
            candles,
        )

    # =================================================
    # EVALUATE
    # =================================================

    def evaluate(
        self,
        symbol: str,
        timeframe: str,
        candles: List[Candle],
        now: Optional[float] = None,
    ) -> tuple:

        if now is None:
            now = time.time()

        signal = self.generate(
            symbol,
            timeframe,
            candles,
        )

        if not signal.valid:

            return (
                signal,
                None,
                "WAIT_OR_INVALID_SIGNAL",
            )

        if not candles:

            return (
                signal,
                None,
                "NO_CANDLE",
            )

        latest_candle = candles[-1]

        candle_allowed, candle_reason = (
            self.candle_protection.confirm(
                signal,
                latest_candle,
                now,
            )
        )

        if not candle_allowed:

            return (
                signal,
                None,
                candle_reason,
            )

        allowed, reason = (
            self.protection.can_emit(
                signal,
                now,
            )
        )

        if not allowed:

            return (
                signal,
                None,
                reason,
            )

        protected = (
            self.protection.emit(
                signal,
                now,
            )
        )

        # Automatically record lifecycle.
        self.lifecycle.signal_created(
            protected,
            timestamp=now,
        )

        self.lifecycle.signal_active(
            protected,
            timestamp=now,
        )

        return (
            signal,
            protected,
            "EMITTED",
        )

    # =================================================
    # PRICE UPDATE
    # =================================================

    def update_price(
        self,
        symbol: str,
        timeframe: str,
        price: float,
        now: Optional[float] = None,
    ) -> Optional[ProtectedSignal]:

        protected = (
            self.protection.check_price(
                symbol,
                timeframe,
                price,
                now,
            )
        )

        if (
            protected is not None
            and protected.state
            == SignalLifecycle.INVALIDATED
        ):

            events = (
                self.lifecycle.events_for(
                    symbol,
                    timeframe,
                )
            )

            already_recorded = any(
                event.event
                == SignalLifecycle.INVALIDATED
                for event in events
            )

            if not already_recorded:

                self.lifecycle.signal_invalidated(
                    protected,
                    reason=(
                        protected
                        .invalidation_reason
                    ),
                    price=price,
                    timestamp=now,
                )

        return protected

    # =================================================
    # EXPIRY
    # =================================================

    def expire(
        self,
        now: Optional[float] = None,
    ):

        expired = (
            self.protection.expire(
                now
            )
        )

        for protected in expired:

            self.lifecycle.signal_expired(
                protected,
                timestamp=now,
            )

        return expired

    # =================================================
    # DATA FRESHNESS
    # =================================================

    def check_data_freshness(
        self,
        last_data_time: float,
        now: Optional[float] = None,
    ) -> bool:

        invalidated = (
            self.protection
            .protect_from_stale_data(
                last_data_time,
                now,
            )
        )

        if invalidated:

            for protected in (
                self.protection.active.values()
            ):

                if (
                    protected.state
                    == SignalLifecycle.INVALIDATED
                    and protected.invalidation_reason
                    == "STALE_MARKET_DATA"
                ):

                    events = (
                        self.lifecycle.events_for(
                            protected.signal.symbol,
                            protected.signal.timeframe,
                        )
                    )

                    already_recorded = any(
                        event.event
                        == SignalLifecycle.INVALIDATED
                        and event.reason
                        == "STALE_MARKET_DATA"
                        for event in events
                    )

                    if not already_recorded:

                        self.lifecycle.signal_invalidated(
                            protected,
                            reason="STALE_MARKET_DATA",
                            timestamp=now,
                        )

        return invalidated

    # =================================================
    # ACTIVE SIGNAL
    # =================================================

    def get_active(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[ProtectedSignal]:

        return self.protection.get_active(
            symbol,
            timeframe,
        )

    # =================================================
    # EVENTS
    # =================================================

    def get_events(
        self,
        symbol: str,
        timeframe: str,
    ):

        return self.lifecycle.events_for(
            symbol,
            timeframe,
        )

    def get_latest_event(
        self,
        symbol: str,
        timeframe: str,
    ):

        return self.lifecycle.latest(
            symbol,
            timeframe,
        )

    def all_events(self):

        return self.lifecycle.all_events()

    # =================================================
    # CLEAR
    # =================================================

    def clear(
        self,
        symbol: str,
        timeframe: str,
    ):

        protected = self.get_active(
            symbol,
            timeframe,
        )

        if protected is not None:

            protected.state = (
                SignalLifecycle.CLEARED
            )

            self.lifecycle.signal_cleared(
                protected
            )

        self.protection.clear(
            symbol,
            timeframe,
        )

    def clear_all(self):

        self.protection.clear_all()
        self.lifecycle.clear()


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 9F - Complete Protected Pipeline"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
