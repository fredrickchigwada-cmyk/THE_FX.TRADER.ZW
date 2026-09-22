import unittest

from core.candle_engine import Candle
from core.candle_close_protection import (
    CandleCloseProtection,
)
from core.signal_engine import Signal


def make_candle(
    start=1000,
    end=1060,
    timeframe="M1",
):

    return Candle(
        symbol="frxXAUUSD",
        timeframe=timeframe,
        start=start,
        end=end,
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=10,
    )


def make_signal(
    direction="BUY",
    timeframe="M1",
    candle_confirmed=True,
    valid=True,
):

    return Signal(
        symbol="frxXAUUSD",
        timeframe=timeframe,
        direction=direction,
        strength=8,
        confirmations=5,
        entry=100.5,
        stop_loss=95.0,
        tp1=105.0,
        tp2=110.0,
        invalidation=95.0,
        explanation="test",
        candle_confirmed=candle_confirmed,
        valid=valid,
    )


class CandleCloseProtectionTest(
    unittest.TestCase
):

    def test_closed_candle_is_detected(self):

        protection = CandleCloseProtection()

        candle = make_candle()

        self.assertTrue(
            protection.is_closed(
                candle,
                now=1060,
            )
        )

    def test_forming_candle_is_detected(self):

        protection = CandleCloseProtection()

        candle = make_candle()

        self.assertTrue(
            protection.is_forming(
                candle,
                now=1059,
            )
        )

    def test_forming_candle_blocks_signal(self):

        protection = CandleCloseProtection()

        signal = make_signal()
        candle = make_candle()

        allowed, reason = (
            protection.confirm(
                signal,
                candle,
                now=1059,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "CANDLE_STILL_FORMING",
        )

    def test_closed_candle_confirms_signal(self):

        protection = CandleCloseProtection()

        signal = make_signal()
        candle = make_candle()

        allowed, reason = (
            protection.confirm(
                signal,
                candle,
                now=1060,
            )
        )

        self.assertTrue(
            allowed
        )

        self.assertEqual(
            reason,
            "CONFIRMED",
        )

    def test_invalid_signal_blocked(self):

        protection = CandleCloseProtection()

        signal = make_signal(
            valid=False
        )

        candle = make_candle()

        allowed, reason = (
            protection.confirm(
                signal,
                candle,
                now=1060,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "INVALID_SIGNAL",
        )

    def test_wait_blocked(self):

        protection = CandleCloseProtection()

        signal = make_signal(
            direction="WAIT"
        )

        signal.valid = False

        candle = make_candle()

        allowed, reason = (
            protection.confirm(
                signal,
                candle,
                now=1060,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "INVALID_SIGNAL",
        )

    def test_missing_candle_blocked(self):

        protection = CandleCloseProtection()

        signal = make_signal()

        allowed, reason = (
            protection.confirm(
                signal,
                None,
                now=1060,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "NO_CANDLE",
        )

    def test_symbol_mismatch(self):

        protection = CandleCloseProtection()

        signal = make_signal()

        candle = make_candle()

        candle.symbol = "BTCUSD"

        allowed, reason = (
            protection.confirm(
                signal,
                candle,
                now=1060,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "SYMBOL_MISMATCH",
        )

    def test_timeframe_mismatch(self):

        protection = CandleCloseProtection()

        signal = make_signal(
            timeframe="M5"
        )

        candle = make_candle(
            timeframe="M1"
        )

        allowed, reason = (
            protection.confirm(
                signal,
                candle,
                now=1060,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "TIMEFRAME_MISMATCH",
        )

    def test_signal_candle_confirmation_required(self):

        protection = CandleCloseProtection()

        signal = make_signal(
            candle_confirmed=False
        )

        candle = make_candle()

        allowed, reason = (
            protection.confirm(
                signal,
                candle,
                now=1060,
            )
        )

        self.assertFalse(
            allowed
        )

        self.assertEqual(
            reason,
            "SIGNAL_CANDLE_CONFIRMATION_FAILED",
        )

    def test_seconds_until_close(self):

        protection = CandleCloseProtection()

        candle = make_candle()

        remaining = (
            protection.seconds_until_close(
                candle,
                now=1030,
            )
        )

        self.assertEqual(
            remaining,
            30.0,
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
            dir(CandleCloseProtection)
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
