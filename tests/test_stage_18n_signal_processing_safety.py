import unittest
from unittest.mock import Mock

from core.production_runtime import ProductionRuntime
from core.signal_engine import Signal
from core.candle_engine import Candle


def make_signal(
    direction="BUY",
    valid=True,
    candle_confirmed=True,
    symbol="XAUUSD",
    timeframe="M5",
):
    return Signal(
        symbol=symbol,
        timeframe=timeframe,
        direction=direction,
        strength=8,
        confirmations=3,
        entry=3000.0 if direction != "WAIT" else None,
        stop_loss=2990.0 if direction == "BUY" else None,
        tp1=3010.0 if direction == "BUY" else None,
        tp2=3020.0 if direction == "BUY" else None,
        invalidation=2990.0 if direction == "BUY" else None,
        explanation="Stage 18N test signal",
        candle_confirmed=candle_confirmed,
        valid=valid,
    )


def make_closed_candle():
    # Deliberately ended in the past.
    return Candle(
        symbol="XAUUSD",
        timeframe="M5",
        start=1000,
        end=1300,
        open=2995.0,
        high=3005.0,
        low=2990.0,
        close=3000.0,
        volume=10,
    )


def make_forming_candle():
    # Deliberately ends in the future.
    return Candle(
        symbol="XAUUSD",
        timeframe="M5",
        start=1000,
        end=9999999999,
        open=2995.0,
        high=3005.0,
        low=2990.0,
        close=3000.0,
        volume=10,
    )


class TestStage18NSignalProcessingSafety(unittest.TestCase):

    def build_runtime(self):
        runtime = ProductionRuntime()

        runtime.PRIMARY_SYMBOL = "XAUUSD"
        runtime.PRIMARY_TIMEFRAME = "M5"

        runtime.candles = Mock()
        runtime.pipeline = Mock()
        runtime.lifecycle = Mock()
        runtime.protection = Mock()
        runtime.candle_protection = Mock()

        runtime.status.news_risk = "LOW"
        runtime.status.news_bias = "NEUTRAL"

        runtime.pipeline.process_signal.return_value = "PIPELINE_RESULT"

        return runtime

    def test_wait_signal_never_enters_protection(self):
        runtime = self.build_runtime()

        signal = make_signal(
            direction="WAIT",
            valid=True,
            candle_confirmed=False,
        )

        result = runtime.process_signal(signal)

        self.assertEqual(result, "PIPELINE_RESULT")
        runtime.candle_protection.confirm.assert_not_called()
        runtime.protection.emit.assert_not_called()
        runtime.lifecycle.signal_created.assert_not_called()
        runtime.pipeline.process_signal.assert_called_once()

    def test_invalid_signal_never_enters_protection(self):
        runtime = self.build_runtime()

        signal = make_signal(
            direction="BUY",
            valid=False,
            candle_confirmed=True,
        )

        result = runtime.process_signal(signal)

        self.assertEqual(result, "PIPELINE_RESULT")
        runtime.candle_protection.confirm.assert_not_called()
        runtime.protection.emit.assert_not_called()
        runtime.lifecycle.signal_created.assert_not_called()

    def test_candle_protection_failure_blocks_signal(self):
        runtime = self.build_runtime()

        signal = make_signal(
            direction="BUY",
            valid=True,
            candle_confirmed=True,
        )

        runtime.candles.get_current.return_value = make_forming_candle()
        runtime.candle_protection.confirm.return_value = (
            False,
            "CANDLE_NOT_CLOSED",
        )

        result = runtime.process_signal(signal)

        self.assertEqual(result, "PIPELINE_RESULT")
        runtime.protection.emit.assert_not_called()
        runtime.lifecycle.signal_created.assert_not_called()

    def test_protected_signal_reaches_lifecycle(self):
        runtime = self.build_runtime()

        signal = make_signal(
            direction="BUY",
            valid=True,
            candle_confirmed=True,
        )

        protected = Mock()
        runtime.candles.get_current.return_value = make_closed_candle()
        runtime.candle_protection.confirm.return_value = (
            True,
            "CONFIRMED",
        )
        runtime.protection.emit.return_value = protected

        result = runtime.process_signal(signal)

        self.assertEqual(result, "PIPELINE_RESULT")
        runtime.protection.emit.assert_called_once_with(signal)
        runtime.lifecycle.signal_created.assert_called_once_with(protected)

    def test_protection_exception_does_not_create_alert(self):
        runtime = self.build_runtime()

        signal = make_signal(
            direction="BUY",
            valid=True,
            candle_confirmed=True,
        )

        runtime.candles.get_current.return_value = make_closed_candle()
        runtime.candle_protection.confirm.return_value = (
            True,
            "CONFIRMED",
        )
        runtime.protection.emit.side_effect = ValueError(
            "Signal emission blocked: DUPLICATE_ACTIVE_SIGNAL"
        )

        result = runtime.process_signal(signal)

        self.assertIsNone(result)
        runtime.lifecycle.signal_created.assert_not_called()

    def test_protection_stale_invalidation_is_not_a_new_signal(self):
        from core.signal_protection import SignalProtection

        protection = SignalProtection(
            cooldown_seconds=300,
            expiry_seconds=900,
            stale_seconds=30,
        )

        signal = make_signal()

        protected = protection.emit(signal, now=1000.0)

        self.assertEqual(protected.state, "ACTIVE")

        changed = protection.protect_from_stale_data(
            last_data_time=900.0,
            now=1000.0,
        )

        self.assertTrue(changed)
        self.assertEqual(protected.state, "INVALIDATED")
        self.assertEqual(
            protected.invalidation_reason,
            "STALE_MARKET_DATA",
        )

    def test_duplicate_signal_is_blocked_by_signal_protection(self):
        from core.signal_protection import SignalProtection

        protection = SignalProtection(
            cooldown_seconds=300,
            expiry_seconds=900,
            stale_seconds=30,
        )

        signal = make_signal()

        first = protection.emit(signal, now=1000.0)

        self.assertEqual(first.state, "ACTIVE")

        allowed, reason = protection.can_emit(
            signal,
            now=1001.0,
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "DUPLICATE_ACTIVE_SIGNAL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
