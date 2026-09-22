import unittest
from core.signal_protection import SignalProtection
from core.signal_engine import Signal


def make_signal(direction="BUY"):
    return Signal(
        symbol="XAUUSD",
        timeframe="M5",
        direction=direction,
        strength=8,
        confirmations=3,
        entry=3000.0,
        stop_loss=2990.0 if direction == "BUY" else 3010.0,
        tp1=3010.0 if direction == "BUY" else 2990.0,
        tp2=3020.0 if direction == "BUY" else 2980.0,
        invalidation=2990.0 if direction == "BUY" else 3010.0,
        explanation="Stage 18Q",
        candle_confirmed=True,
        valid=True,
    )


class TestStage18QDuplicateCooldown(unittest.TestCase):

    def test_first_signal_allowed(self):
        p = SignalProtection(cooldown_seconds=300)
        ok, reason = p.can_emit(make_signal("BUY"), now=1000)
        self.assertTrue(ok)
        self.assertEqual(reason, "ALLOWED")

    def test_duplicate_active_signal_blocked(self):
        p = SignalProtection(cooldown_seconds=300)
        signal = make_signal("BUY")

        p.emit(signal, now=1000)

        ok, reason = p.can_emit(signal, now=1010)

        self.assertFalse(ok)
        self.assertEqual(reason, "DUPLICATE_ACTIVE_SIGNAL")

    def test_same_signal_cooldown_blocked(self):
        p = SignalProtection(cooldown_seconds=300)
        signal = make_signal("BUY")

        protected = p.emit(signal, now=1000)
        protected.state = "INVALIDATED"

        ok, reason = p.can_emit(signal, now=1100)

        self.assertFalse(ok)
        self.assertEqual(reason, "COOLDOWN_ACTIVE")

    def test_signal_allowed_after_cooldown(self):
        p = SignalProtection(cooldown_seconds=300)
        signal = make_signal("BUY")

        protected = p.emit(signal, now=1000)
        protected.state = "INVALIDATED"

        ok, reason = p.can_emit(signal, now=1301)

        self.assertTrue(ok)
        self.assertEqual(reason, "ALLOWED")

    def test_buy_and_sell_are_not_duplicates(self):
        p = SignalProtection(cooldown_seconds=300)

        buy = make_signal("BUY")
        sell = make_signal("SELL")

        p.emit(buy, now=1000)

        ok, reason = p.can_emit(sell, now=1010)

        self.assertTrue(ok)
        self.assertEqual(reason, "ALLOWED")

    def test_invalid_signal_blocked(self):
        p = SignalProtection()

        signal = make_signal("BUY")
        signal.valid = False

        ok, reason = p.can_emit(signal, now=1000)

        self.assertFalse(ok)
        self.assertEqual(reason, "INVALID_SIGNAL")

    def test_wait_signal_blocked(self):
        p = SignalProtection()

        signal = make_signal("WAIT")

        ok, reason = p.can_emit(signal, now=1000)

        self.assertFalse(ok)
        self.assertEqual(reason, "NOT_BUY_SELL")

    def test_emit_raises_when_duplicate(self):
        p = SignalProtection()

        signal = make_signal("BUY")
        p.emit(signal, now=1000)

        with self.assertRaises(ValueError):
            p.emit(signal, now=1010)


if __name__ == "__main__":
    unittest.main()
