import time
from dataclasses import dataclass
from typing import List, Optional

from core.signal_protection import ProtectedSignal


@dataclass
class SignalEvent:
    symbol: str
    timeframe: str
    direction: str
    event: str
    timestamp: float
    reason: Optional[str] = None
    price: Optional[float] = None


class SignalLifecycle:
    """
    Tracks the lifecycle and events of protected signals.

    SIGNAL-ONLY:
    This module records signal state.
    It cannot place, modify, or close trades.
    """

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    CLEARED = "CLEARED"

    MAX_EVENTS = 5000

    def __init__(self):
        self.events: List[SignalEvent] = []

    # =================================================
    # INTERNAL EVENT CREATION
    # =================================================

    def _record(
        self,
        protected: ProtectedSignal,
        event: str,
        timestamp: Optional[float] = None,
        reason: Optional[str] = None,
        price: Optional[float] = None,
    ) -> SignalEvent:

        if timestamp is None:
            timestamp = time.time()

        signal = protected.signal

        item = SignalEvent(
            symbol=signal.symbol,
            timeframe=signal.timeframe,
            direction=signal.direction,
            event=event,
            timestamp=timestamp,
            reason=reason,
            price=price,
        )

        self.events.append(item)

        if len(self.events) > self.MAX_EVENTS:
            self.events = self.events[
                -self.MAX_EVENTS:
            ]

        return item

    # =================================================
    # CREATED / ACTIVE
    # =================================================

    def signal_created(
        self,
        protected: ProtectedSignal,
        timestamp: Optional[float] = None,
    ) -> SignalEvent:

        return self._record(
            protected,
            self.CREATED,
            timestamp=timestamp,
        )

    def signal_active(
        self,
        protected: ProtectedSignal,
        timestamp: Optional[float] = None,
    ) -> SignalEvent:

        return self._record(
            protected,
            self.ACTIVE,
            timestamp=timestamp,
        )

    # =================================================
    # INVALIDATION
    # =================================================

    def signal_invalidated(
        self,
        protected: ProtectedSignal,
        reason: Optional[str] = None,
        price: Optional[float] = None,
        timestamp: Optional[float] = None,
    ) -> SignalEvent:

        if reason is None:
            reason = protected.invalidation_reason

        return self._record(
            protected,
            self.INVALIDATED,
            timestamp=timestamp,
            reason=reason,
            price=price,
        )

    # =================================================
    # EXPIRY
    # =================================================

    def signal_expired(
        self,
        protected: ProtectedSignal,
        timestamp: Optional[float] = None,
    ) -> SignalEvent:

        return self._record(
            protected,
            self.EXPIRED,
            timestamp=timestamp,
            reason=protected.invalidation_reason,
        )

    # =================================================
    # CLEARED
    # =================================================

    def signal_cleared(
        self,
        protected: ProtectedSignal,
        timestamp: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> SignalEvent:

        return self._record(
            protected,
            self.CLEARED,
            timestamp=timestamp,
            reason=reason,
        )

    # =================================================
    # AUTOMATIC STATE RECORDING
    # =================================================

    def record_state(
        self,
        protected: ProtectedSignal,
        timestamp: Optional[float] = None,
        price: Optional[float] = None,
    ) -> Optional[SignalEvent]:

        state = protected.state

        if state == self.CREATED:
            return self.signal_created(
                protected,
                timestamp,
            )

        if state == self.ACTIVE:
            return self.signal_active(
                protected,
                timestamp,
            )

        if state == self.INVALIDATED:
            return self.signal_invalidated(
                protected,
                reason=protected.invalidation_reason,
                price=price,
                timestamp=timestamp,
            )

        if state == self.EXPIRED:
            return self.signal_expired(
                protected,
                timestamp,
            )

        if state == self.CLEARED:
            return self.signal_cleared(
                protected,
                timestamp,
            )

        return None

    # =================================================
    # QUERY
    # =================================================

    def all_events(self) -> List[SignalEvent]:

        return list(self.events)

    def events_for(
        self,
        symbol: str,
        timeframe: str,
    ) -> List[SignalEvent]:

        return [
            event
            for event in self.events
            if (
                event.symbol == symbol
                and event.timeframe == timeframe
            )
        ]

    def latest(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[SignalEvent]:

        matching = self.events_for(
            symbol,
            timeframe,
        )

        if not matching:
            return None

        return matching[-1]

    def clear(self):

        self.events.clear()


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 9E - Signal Lifecycle"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
