import unittest

from core.signal_engine import Signal
from core.signal_protection import SignalProtection


def make_signal(
    direction="BUY",
    entry=100.0,
    stop_loss=95.0,
    tp1=105.0,
    tp2=110.0,
):

    return Signal(
        symbol="frxXAUUSD",
        timeframe="M1",
        direction=direction,
        strength=8,
        confirmations=5,
        entry=entry,
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        invalidation=stop_loss
        if direction == "BUY"
        else stop_loss,
        explanation="test signal",
        candle_confirmed=True,
        valid=True,
    )


class SignalProtectionTest(
    unittest.TestCase
):

    def test_valid_signal_can_emit(self):

        protection = SignalProtection()

        signal = make_signal()

        allowed, reason = (
            protection.can_emit(
                signal,
                now=1000,
            )
        )

        self.assertTrue(
            allowed
        )

        self.assertEqual(
            reason,
            "ALLOWED",
        )

    def test_duplicate_active_signal_blocked(self):

        protection = SignalProtection()

        signal = make_signal()

        protection.emit(
            signal,
            now=1000,
        )

        allowed, reason = (
            protection.can_emit(
                signal,
                now=1001,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "DUPLICATE_ACTIVE_SIGNAL",
        )

    def test_cooldown_blocks_same_signal(self):

        protection = SignalProtection(
            cooldown_seconds=300
        )

        signal = make_signal()

        protection.emit(
            signal,
            now=1000,
        )

        protection.active[
            "frxXAUUSD:M1"
        ].state = "EXPIRED"

        allowed, reason = (
            protection.can_emit(
                signal,
                now=1100,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "COOLDOWN_ACTIVE",
        )

    def test_expiry(self):

        protection = SignalProtection(
            expiry_seconds=100
        )

        signal = make_signal()

        protected = protection.emit(
            signal,
            now=1000,
        )

        expired = protection.expire(
            now=1101
        )

        self.assertEqual(
            len(expired),
            1,
        )

        self.assertEqual(
            protected.state,
            "EXPIRED",
        )

    def test_buy_price_invalidation(self):

        protection = SignalProtection()

        signal = make_signal(
            direction="BUY",
            stop_loss=95.0,
        )

        protected = protection.emit(
            signal,
            now=1000,
        )

        protection.check_price(
            "frxXAUUSD",
            "M1",
            95.0,
            now=1001,
        )

        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )

        self.assertEqual(
            protected.invalidation_reason,
            "BUY_INVALIDATION_REACHED",
        )

    def test_sell_price_invalidation(self):

        protection = SignalProtection()

        signal = make_signal(
            direction="SELL",
            stop_loss=105.0,
        )

        protected = protection.emit(
            signal,
            now=1000,
        )

        protection.check_price(
            "frxXAUUSD",
            "M1",
            105.0,
            now=1001,
        )

        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )

        self.assertEqual(
            protected.invalidation_reason,
            "SELL_INVALIDATION_REACHED",
        )

    def test_stale_data_detection(self):

        protection = SignalProtection(
            stale_seconds=30
        )

        self.assertTrue(
            protection.check_stale(
                1000,
                now=1031,
            )
        )

        self.assertFalse(
            protection.check_stale(
                1000,
                now=1029,
            )
        )

    def test_stale_data_invalidates_active_signal(self):

        protection = SignalProtection()

        signal = make_signal()

        protected = protection.emit(
            signal,
            now=1000,
        )

        result = (
            protection.protect_from_stale_data(
                1000,
                now=1031,
            )
        )

        self.assertTrue(
            result
        )

        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )

        self.assertEqual(
            protected.invalidation_reason,
            "STALE_MARKET_DATA",
        )

    def test_invalid_signal_cannot_emit(self):

        protection = SignalProtection()

        signal = make_signal()

        signal.valid = False

        allowed, reason = (
            protection.can_emit(
                signal
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "INVALID_SIGNAL",
        )

    def test_wait_signal_cannot_emit(self):

        protection = SignalProtection()

        signal = make_signal()

        signal.direction = "WAIT"

        allowed, reason = (
            protection.can_emit(
                signal
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "NOT_BUY_SELL",
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
            dir(SignalProtection)
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
