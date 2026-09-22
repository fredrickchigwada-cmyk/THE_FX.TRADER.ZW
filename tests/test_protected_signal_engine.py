import unittest

from core.candle_engine import Candle
from core.signal_engine import Signal
from core.signal_protection import SignalProtection
from core.candle_close_protection import (
    CandleCloseProtection,
)
from core.signal_lifecycle import SignalLifecycle
from core.protected_signal_engine import (
    ProtectedSignalEngine,
)


class FakeSignalEngine:

    def __init__(self, signal):
        self.signal = signal

    def generate(
        self,
        symbol,
        timeframe,
        candles,
    ):
        return self.signal


def make_signal(
    direction="BUY",
    entry=100.0,
    invalidation=95.0,
):

    return Signal(
        symbol="frxXAUUSD",
        timeframe="M1",
        direction=direction,
        strength=8,
        confirmations=5,
        entry=entry,
        stop_loss=invalidation,
        tp1=105.0,
        tp2=110.0,
        invalidation=invalidation,
        explanation="test",
        candle_confirmed=True,
        valid=True,
    )


def make_candles():

    return [
        Candle(
            symbol="frxXAUUSD",
            timeframe="M1",
            start=i * 60,
            end=(i + 1) * 60,
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=10,
        )
        for i in range(200)
    ]


class ProtectedSignalEngineTest(
    unittest.TestCase
):

    def make_engine(
        self,
        signal=None,
        expiry=900,
    ):

        signal = (
            signal
            or make_signal()
        )

        lifecycle = SignalLifecycle()

        return ProtectedSignalEngine(
            signal_engine=FakeSignalEngine(
                signal
            ),
            protection=SignalProtection(
                expiry_seconds=expiry
            ),
            candle_protection=CandleCloseProtection(),
            lifecycle=lifecycle,
        )

    def test_valid_closed_signal_is_emitted(self):

        engine = self.make_engine()

        result, protected, status = (
            engine.evaluate(
                "frxXAUUSD",
                "M1",
                make_candles(),
                now=12060,
            )
        )

        self.assertEqual(
            result.direction,
            "BUY",
        )

        self.assertIsNotNone(
            protected
        )

        self.assertEqual(
            status,
            "EMITTED",
        )

    def test_created_and_active_events_are_recorded(self):

        engine = self.make_engine()

        engine.evaluate(
            "frxXAUUSD",
            "M1",
            make_candles(),
            now=12060,
        )

        events = engine.get_events(
            "frxXAUUSD",
            "M1",
        )

        self.assertEqual(
            len(events),
            2,
        )

        self.assertEqual(
            events[0].event,
            "CREATED",
        )

        self.assertEqual(
            events[1].event,
            "ACTIVE",
        )

    def test_forming_candle_blocks_signal(self):

        engine = self.make_engine()

        result, protected, status = (
            engine.evaluate(
                "frxXAUUSD",
                "M1",
                make_candles(),
                now=11999,
            )
        )

        self.assertIsNone(
            protected
        )

        self.assertEqual(
            status,
            "CANDLE_STILL_FORMING",
        )

    def test_duplicate_closed_signal_is_blocked(self):

        engine = self.make_engine()

        candles = make_candles()

        first = engine.evaluate(
            "frxXAUUSD",
            "M1",
            candles,
            now=12060,
        )

        second = engine.evaluate(
            "frxXAUUSD",
            "M1",
            candles,
            now=12061,
        )

        self.assertIsNotNone(
            first[1]
        )

        self.assertIsNone(
            second[1]
        )

    def test_price_invalidation_creates_event(self):

        engine = self.make_engine()

        engine.evaluate(
            "frxXAUUSD",
            "M1",
            make_candles(),
            now=12060,
        )

        protected = engine.update_price(
            "frxXAUUSD",
            "M1",
            95.0,
            now=12061,
        )

        self.assertEqual(
            protected.state,
            "INVALIDATED",
        )

        events = engine.get_events(
            "frxXAUUSD",
            "M1",
        )

        self.assertEqual(
            events[-1].event,
            "INVALIDATED",
        )

        self.assertEqual(
            events[-1].reason,
            "BUY_INVALIDATION_REACHED",
        )

        self.assertEqual(
            events[-1].price,
            95.0,
        )

    def test_expiry_creates_event(self):

        engine = self.make_engine(
            expiry=10
        )

        engine.evaluate(
            "frxXAUUSD",
            "M1",
            make_candles(),
            now=12060,
        )

        expired = engine.expire(
            now=12071
        )

        self.assertEqual(
            len(expired),
            1,
        )

        events = engine.get_events(
            "frxXAUUSD",
            "M1",
        )

        self.assertEqual(
            events[-1].event,
            "EXPIRED",
        )

    def test_stale_data_creates_event(self):

        engine = self.make_engine()

        engine.evaluate(
            "frxXAUUSD",
            "M1",
            make_candles(),
            now=12060,
        )

        result = engine.check_data_freshness(
            1000,
            now=1031,
        )

        self.assertTrue(
            result
        )

        events = engine.get_events(
            "frxXAUUSD",
            "M1",
        )

        self.assertEqual(
            events[-1].event,
            "INVALIDATED",
        )

        self.assertEqual(
            events[-1].reason,
            "STALE_MARKET_DATA",
        )

    def test_wait_is_not_emitted(self):

        signal = make_signal()

        signal.direction = "WAIT"
        signal.valid = False

        engine = self.make_engine(
            signal
        )

        result, protected, status = (
            engine.evaluate(
                "frxXAUUSD",
                "M1",
                make_candles(),
                now=12060,
            )
        )

        self.assertIsNone(
            protected
        )

        self.assertEqual(
            status,
            "WAIT_OR_INVALID_SIGNAL",
        )

    def test_no_candle_blocks_signal(self):

        engine = self.make_engine()

        result, protected, status = (
            engine.evaluate(
                "frxXAUUSD",
                "M1",
                [],
                now=12060,
            )
        )

        self.assertIsNone(
            protected
        )

        self.assertEqual(
            status,
            "NO_CANDLE",
        )

    def test_latest_event(self):

        engine = self.make_engine()

        engine.evaluate(
            "frxXAUUSD",
            "M1",
            make_candles(),
            now=12060,
        )

        latest = engine.get_latest_event(
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
            dir(ProtectedSignalEngine)
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
