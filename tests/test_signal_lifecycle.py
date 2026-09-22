import unittest

from core.signal_engine import Signal
from core.signal_protection import ProtectedSignal
from core.signal_lifecycle import (
    SignalLifecycle,
)


def make_protected(
    direction="BUY",
    state="ACTIVE",
):

    signal = Signal(
        symbol="frxXAUUSD",
        timeframe="M1",
        direction=direction,
        strength=8,
        confirmations=5,
        entry=100.0,
        stop_loss=95.0,
        tp1=105.0,
        tp2=110.0,
        invalidation=95.0,
        explanation="test",
        candle_confirmed=True,
        valid=True,
    )

    return ProtectedSignal(
        signal=signal,
        created_at=1000,
        expires_at=1900,
        state=state,
    )


class SignalLifecycleTest(
    unittest.TestCase
):

    def test_created_event(self):

        lifecycle = SignalLifecycle()

        protected = make_protected(
            state="CREATED"
        )

        event = lifecycle.record_state(
            protected,
            timestamp=1001,
        )

        self.assertIsNotNone(
            event
        )

        self.assertEqual(
            event.event,
            "CREATED",
        )

        self.assertEqual(
            event.symbol,
            "frxXAUUSD",
        )

    def test_active_event(self):

        lifecycle = SignalLifecycle()

        protected = make_protected(
            state="ACTIVE"
        )

        event = lifecycle.record_state(
            protected,
            timestamp=1002,
        )

        self.assertEqual(
            event.event,
            "ACTIVE",
        )

    def test_invalidated_event(self):

        lifecycle = SignalLifecycle()

        protected = make_protected(
            state="INVALIDATED"
        )

        protected.invalidation_reason = (
            "BUY_INVALIDATION_REACHED"
        )

        event = lifecycle.record_state(
            protected,
            timestamp=1003,
            price=95.0,
        )

        self.assertEqual(
            event.event,
            "INVALIDATED",
        )

        self.assertEqual(
            event.reason,
            "BUY_INVALIDATION_REACHED",
        )

        self.assertEqual(
            event.price,
            95.0,
        )

    def test_expired_event(self):

        lifecycle = SignalLifecycle()

        protected = make_protected(
            state="EXPIRED"
        )

        protected.invalidation_reason = (
            "SIGNAL_EXPIRED"
        )

        event = lifecycle.record_state(
            protected,
            timestamp=1901,
        )

        self.assertEqual(
            event.event,
            "EXPIRED",
        )

        self.assertEqual(
            event.reason,
            "SIGNAL_EXPIRED",
        )

    def test_cleared_event(self):

        lifecycle = SignalLifecycle()

        protected = make_protected(
            state="CLEARED"
        )

        event = lifecycle.record_state(
            protected,
            timestamp=2000,
        )

        self.assertEqual(
            event.event,
            "CLEARED",
        )

    def test_events_for_symbol_timeframe(self):

        lifecycle = SignalLifecycle()

        protected = make_protected()

        lifecycle.signal_created(
            protected,
            timestamp=1000,
        )

        lifecycle.signal_active(
            protected,
            timestamp=1001,
        )

        events = lifecycle.events_for(
            "frxXAUUSD",
            "M1",
        )

        self.assertEqual(
            len(events),
            2,
        )

    def test_latest_event(self):

        lifecycle = SignalLifecycle()

        protected = make_protected()

        lifecycle.signal_created(
            protected,
            timestamp=1000,
        )

        lifecycle.signal_active(
            protected,
            timestamp=1001,
        )

        latest = lifecycle.latest(
            "frxXAUUSD",
            "M1",
        )

        self.assertIsNotNone(
            latest
        )

        self.assertEqual(
            latest.event,
            "ACTIVE",
        )

    def test_event_limit(self):

        lifecycle = SignalLifecycle()

        protected = make_protected()

        for i in range(
            lifecycle.MAX_EVENTS + 10
        ):

            lifecycle.signal_active(
                protected,
                timestamp=float(i),
            )

        self.assertEqual(
            len(
                lifecycle.all_events()
            ),
            lifecycle.MAX_EVENTS,
        )

    def test_clear(self):

        lifecycle = SignalLifecycle()

        protected = make_protected()

        lifecycle.signal_created(
            protected,
            timestamp=1000,
        )

        lifecycle.clear()

        self.assertEqual(
            lifecycle.all_events(),
            [],
        )

    def test_unknown_state_is_safe(self):

        lifecycle = SignalLifecycle()

        protected = make_protected(
            state="UNKNOWN"
        )

        result = lifecycle.record_state(
            protected,
            timestamp=1000,
        )

        self.assertIsNone(
            result
        )

    def test_no_trade_methods(self):

        forbidden = {
            "buy",
            "sell",
            "place_order",
            "modify_order",
            "close_trade",
            "execute_trade",
        }

        available = set(
            dir(SignalLifecycle)
        )

        self.assertTrue(
            forbidden.isdisjoint(
                available
            )
        )


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )
