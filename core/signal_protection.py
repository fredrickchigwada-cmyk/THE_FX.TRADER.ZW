import time
from dataclasses import dataclass
from typing import Dict, Optional

from core.signal_engine import Signal


@dataclass
class ProtectedSignal:
    signal: Signal
    created_at: float
    expires_at: float
    state: str
    invalidation_reason: Optional[str] = None


class SignalProtection:
    """
    Safety and lifecycle layer for generated signals.

    SIGNAL-ONLY:
    This module never places, modifies, or closes trades.
    """

    DEFAULT_COOLDOWN = 300.0
    DEFAULT_EXPIRY = 900.0
    DEFAULT_STALE_SECONDS = 30.0

    def __init__(
        self,
        cooldown_seconds: float = DEFAULT_COOLDOWN,
        expiry_seconds: float = DEFAULT_EXPIRY,
        stale_seconds: float = DEFAULT_STALE_SECONDS,
    ):
        if cooldown_seconds < 0:
            raise ValueError(
                "Cooldown cannot be negative."
            )

        if expiry_seconds <= 0:
            raise ValueError(
                "Expiry must be positive."
            )

        if stale_seconds <= 0:
            raise ValueError(
                "Stale timeout must be positive."
            )

        self.cooldown_seconds = cooldown_seconds
        self.expiry_seconds = expiry_seconds
        self.stale_seconds = stale_seconds

        self.active: Dict[
            str,
            ProtectedSignal
        ] = {}

        self.last_emitted: Dict[
            str,
            ProtectedSignal
        ] = {}

    # =================================================
    # INTERNAL HELPERS
    # =================================================

    @staticmethod
    def _key(
        symbol: str,
        timeframe: str,
    ) -> str:

        return f"{symbol}:{timeframe}"

    @staticmethod
    def _signature(
        signal: Signal,
    ) -> tuple:

        return (
            signal.direction,
            signal.strength,
            signal.confirmations,
            signal.entry,
            signal.stop_loss,
            signal.tp1,
            signal.tp2,
        )

    # =================================================
    # DUPLICATE / COOLDOWN
    # =================================================

    def can_emit(
        self,
        signal: Signal,
        now: Optional[float] = None,
    ) -> tuple:

        if now is None:
            now = time.time()

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

        key = self._key(
            signal.symbol,
            signal.timeframe,
        )

        active = self.active.get(key)

        if active is not None:

            if active.state == "ACTIVE":

                if (
                    self._signature(
                        active.signal
                    )
                    == self._signature(
                        signal
                    )
                ):

                    return (
                        False,
                        "DUPLICATE_ACTIVE_SIGNAL",
                    )

        previous = self.last_emitted.get(
            key
        )

        if previous is not None:

            elapsed = (
                now - previous.created_at
            )

            if elapsed < self.cooldown_seconds:

                if (
                    self._signature(
                        previous.signal
                    )
                    == self._signature(
                        signal
                    )
                ):

                    return (
                        False,
                        "COOLDOWN_ACTIVE",
                    )

        return (
            True,
            "ALLOWED",
        )

    # =================================================
    # EMIT
    # =================================================

    def emit(
        self,
        signal: Signal,
        now: Optional[float] = None,
    ) -> ProtectedSignal:

        if now is None:
            now = time.time()

        allowed, reason = self.can_emit(
            signal,
            now,
        )

        if not allowed:

            raise ValueError(
                f"Signal emission blocked: "
                f"{reason}"
            )

        protected = ProtectedSignal(
            signal=signal,
            created_at=now,
            expires_at=(
                now
                + self.expiry_seconds
            ),
            state="ACTIVE",
        )

        key = self._key(
            signal.symbol,
            signal.timeframe,
        )

        self.active[key] = protected
        self.last_emitted[key] = protected

        return protected

    # =================================================
    # EXPIRY
    # =================================================

    def expire(
        self,
        now: Optional[float] = None,
    ):

        if now is None:
            now = time.time()

        expired = []

        for key, protected in list(
            self.active.items()
        ):

            if (
                protected.state == "ACTIVE"
                and now >= protected.expires_at
            ):

                protected.state = "EXPIRED"

                protected.invalidation_reason = (
                    "SIGNAL_EXPIRED"
                )

                expired.append(
                    protected
                )

        return expired

    # =================================================
    # PRICE INVALIDATION
    # =================================================

    def check_price(
        self,
        symbol: str,
        timeframe: str,
        price: float,
        now: Optional[float] = None,
    ):

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        if now is None:
            now = time.time()

        key = self._key(
            symbol,
            timeframe,
        )

        protected = self.active.get(
            key
        )

        if protected is None:
            return None

        if protected.state != "ACTIVE":
            return protected

        signal = protected.signal

        invalidated = False
        reason = None

        if signal.direction == "BUY":

            if (
                signal.invalidation is not None
                and price <= signal.invalidation
            ):

                invalidated = True
                reason = (
                    "BUY_INVALIDATION_REACHED"
                )

        elif signal.direction == "SELL":

            if (
                signal.invalidation is not None
                and price >= signal.invalidation
            ):

                invalidated = True
                reason = (
                    "SELL_INVALIDATION_REACHED"
                )

        if invalidated:

            protected.state = "INVALIDATED"
            protected.invalidation_reason = reason

        return protected

    # =================================================
    # STALE DATA
    # =================================================

    def check_stale(
        self,
        last_data_time: float,
        now: Optional[float] = None,
    ) -> bool:

        if now is None:
            now = time.time()

        if last_data_time <= 0:
            return True

        return (
            now - last_data_time
            > self.stale_seconds
        )

    # =================================================
    # MARKET DATA SAFETY
    # =================================================

    def protect_from_stale_data(
        self,
        last_data_time: float,
        now: Optional[float] = None,
    ):

        if self.check_stale(
            last_data_time,
            now,
        ):

            for protected in self.active.values():

                if protected.state == "ACTIVE":

                    protected.state = (
                        "INVALIDATED"
                    )

                    protected.invalidation_reason = (
                        "STALE_MARKET_DATA"
                    )

            return True

        return False

    # =================================================
    # GETTERS
    # =================================================

    def get_active(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[ProtectedSignal]:

        key = self._key(
            symbol,
            timeframe,
        )

        protected = self.active.get(
            key
        )

        if protected is None:
            return None

        if protected.state != "ACTIVE":
            return protected

        return protected

    def clear(
        self,
        symbol: str,
        timeframe: str,
    ):

        key = self._key(
            symbol,
            timeframe,
        )

        self.active.pop(
            key,
            None,
        )

    def clear_all(self):

        self.active.clear()
        self.last_emitted.clear()


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 9A - Signal Protection"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
