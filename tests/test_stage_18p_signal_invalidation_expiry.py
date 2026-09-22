import unittest

from core.signal_engine import Signal
from core.signal_protection import SignalProtection
from core.signal_lifecycle import SignalLifecycle


def make_signal(direction="BUY", invalidation=2990.0):
    return Signal(
        symbol="XAUUSD",
        timeframe="M5",
        direction=direction,
        strength=8,
        confirmations=3,
        entry=3000.0,
        stop_loss=2990.0,
        tp1=3010.0,
        tp2=3020.0,
        invalidation=invalidation,
        explanation="Stage 18P test signal",
        candle_confirmed=True,
        valid=True,
    )


class TestStage18PSignalInvalidationExpiry(unittest.TestCase):

    def make_protected(self, direction="BUY", created=1000.0):
        protection = SignalProtection(
            cooldown_seconds=300,
            expiry_seconds=900,
            stale_seconds=30,
        )

        signal = make_signal(direction)

        protected = protection.emit(
            signal,
            now=created,
        )

        return protection, protected

    def test_buy_invalidates_when_price_reaches_invalidation(self):
        protection, protected = self.make_protected("BUY")

        result = protection.check_price(
            "XAUUSD",
            "M5",
            2990.0,
            now=1100.0,
        )

        self.assertIs(result, protected)
        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )
        self.assertEqual(
            protected.invalidation_reason,
            "BUY_INVALIDATION_REACHED",
        )

    def test_sell_invalidates_when_price_reaches_invalidation(self):
        protection, protected = self.make_protected("SELL")

        result = protection.check_price(
            "XAUUSD",
            "M5",
            2990.0,
            now=1100.0,
        )

        self.assertIs(result, protected)
        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )
        self.assertEqual(
            protected.invalidation_reason,
            "SELL_INVALIDATION_REACHED",
        )

    def test_price_not_at_invalidation_keeps_signal_active(self):
        protection, protected = self.make_protected("BUY")

        result = protection.check_price(
            "XAUUSD",
            "M5",
            2995.0,
            now=1100.0,
        )

        self.assertIs(result, protected)
        self.assertEqual(
            protected.state,
            "ACTIVE",
        )
        self.assertIsNone(
            protected.invalidation_reason,
        )

    def test_expired_signal_changes_to_expired_state(self):
        protection, protected = self.make_protected(
            "BUY",
            created=1000.0,
        )

        expired = protection.expire(
            now=1900.0,
        )

        self.assertEqual(
            len(expired),
            1,
        )
        self.assertIs(
            expired[0],
            protected,
        )
        self.assertEqual(
            protected.state,
            "EXPIRED",
        )
        self.assertEqual(
            protected.invalidation_reason,
            "SIGNAL_EXPIRED",
        )

    def test_signal_not_expired_before_expiry_time(self):
        protection, protected = self.make_protected(
            "BUY",
            created=1000.0,
        )

        expired = protection.expire(
            now=1899.0,
        )

        self.assertEqual(
            expired,
            [],
        )
        self.assertEqual(
            protected.state,
            "ACTIVE",
        )

    def test_stale_market_data_invalidates_active_signal(self):
        protection, protected = self.make_protected(
            "BUY",
            created=1000.0,
        )

        result = protection.protect_from_stale_data(
            last_data_time=1000.0,
            now=1031.0,
        )

        self.assertTrue(result)
        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )
        self.assertEqual(
            protected.invalidation_reason,
            "STALE_MARKET_DATA",
        )

    def test_fresh_market_data_does_not_invalidate_signal(self):
        protection, protected = self.make_protected(
            "BUY",
            created=1000.0,
        )

        result = protection.protect_from_stale_data(
            last_data_time=1000.0,
            now=1029.0,
        )

        self.assertFalse(result)
        self.assertEqual(
            protected.state,
            "ACTIVE",
        )

    def test_lifecycle_records_invalidation(self):
        protection, protected = self.make_protected("BUY")

        protection.check_price(
            "XAUUSD",
            "M5",
            2990.0,
            now=1100.0,
        )

        lifecycle = SignalLifecycle()

        created = lifecycle.signal_created(
            protected,
            timestamp=1000.0,
        )

        invalidated = lifecycle.signal_invalidated(
            protected,
            timestamp=1100.0,
        )

        events = lifecycle.all_events()

        self.assertEqual(created.event, "CREATED")
        self.assertEqual(
            invalidated.event,
            "INVALIDATED",
        )
        self.assertEqual(
            invalidated.reason,
            "BUY_INVALIDATION_REACHED",
        )
        self.assertEqual(len(events), 2)

    def test_lifecycle_records_expiry(self):
        protection, protected = self.make_protected(
            "BUY",
            created=1000.0,
        )

        protection.expire(now=1900.0)

        lifecycle = SignalLifecycle()

        event = lifecycle.signal_expired(
            protected,
            timestamp=1900.0,
        )

        self.assertEqual(
            event.event,
            "EXPIRED",
        )
        self.assertEqual(
            event.reason,
            "SIGNAL_EXPIRED",
        )

    def test_invalidated_signal_does_not_get_reinvalidated(self):
        protection, protected = self.make_protected("BUY")

        first = protection.check_price(
            "XAUUSD",
            "M5",
            2990.0,
            now=1100.0,
        )

        second = protection.check_price(
            "XAUUSD",
            "M5",
            2980.0,
            now=1200.0,
        )

        self.assertIs(first, protected)
        self.assertIs(second, protected)
        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )
        self.assertEqual(
            protected.invalidation_reason,
            "BUY_INVALIDATION_REACHED",
        )

    def test_invalidated_signal_is_not_expired_again(self):
        protection, protected = self.make_protected("BUY")

        protection.check_price(
            "XAUUSD",
            "M5",
            2990.0,
            now=1100.0,
        )

        expired = protection.expire(
            now=2000.0,
        )

        self.assertEqual(
            expired,
            [],
        )
        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )


if __name__ == "__main__":
    unittest.main()
