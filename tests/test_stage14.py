import os
import tempfile
import time
import unittest

from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline
from core.signal_journal import SignalJournal


class FakeSignal:

    def __init__(
        self,
        signal,
        strength=8,
        confirmations=5,
    ):
        self.signal = signal
        self.strength = strength
        self.confirmations = confirmations
        self.entry = 4365.0
        self.stop_loss = 4362.0
        self.tp1 = 4368.0
        self.tp2 = 4371.0
        self.setup = "TEST"
        self.explanation = "TEST SIGNAL"


class TestStage14(unittest.TestCase):

    def setUp(self):

        self.temp = tempfile.NamedTemporaryFile(
            delete=False
        )

        self.temp.close()

        self.journal = SignalJournal(
            self.temp.name
        )

        self.system = FullSystem(
            market="XAUUSD",
            timeframe="M1",
            journal=self.journal,
        )

    def tearDown(self):

        self.system.stop()

        try:
            os.remove(self.temp.name)
        except FileNotFoundError:
            pass

    def test_system_start(self):

        self.assertTrue(
            self.system.start()
        )

        time.sleep(0.05)

        status = self.system.snapshot()

        self.assertTrue(status.running)
        self.assertTrue(status.connected)
        self.assertTrue(status.healthy)

    def test_system_stop(self):

        self.system.start()

        self.system.stop()

        status = self.system.snapshot()

        self.assertFalse(status.running)

    def test_accept_buy_signal(self):

        record = self.system.accept_signal(
            "BUY",
            strength=8,
            confirmations=5,
            entry=4365,
            stop_loss=4362,
            tp1=4368,
            tp2=4371,
        )

        self.assertIsNotNone(record)
        self.assertEqual(
            record.signal,
            "BUY",
        )

        self.assertEqual(
            self.journal.count(),
            1,
        )

    def test_accept_wait(self):

        record = self.system.accept_signal(
            "WAIT",
            strength=0,
            confirmations=0,
        )

        self.assertIsNotNone(record)
        self.assertEqual(
            record.signal,
            "WAIT",
        )

    def test_pipeline(self):

        pipeline = IntegrationPipeline(
            system=self.system
        )

        result = pipeline.process_signal(
            FakeSignal("BUY")
        )

        self.assertEqual(
            result.status,
            "PROCESSED",
        )

        self.assertTrue(
            result.journaled
        )

    def test_emergency_stop(self):

        self.system.start()

        self.system.emergency_stop_system()

        status = self.system.snapshot()

        self.assertTrue(
            status.emergency_stop
        )

        self.assertFalse(
            status.running
        )

    def test_emergency_stop_blocks_signal(self):

        self.system.emergency_stop_system()

        record = self.system.accept_signal(
            "BUY",
            strength=10,
            confirmations=10,
        )

        self.assertIsNone(record)

        self.assertEqual(
            self.journal.count(),
            0,
        )

    def test_invalid_signal_rejected(self):

        with self.assertRaises(ValueError):

            self.system.accept_signal(
                "INVALID"
            )

    def test_result_update(self):

        record = self.system.accept_signal(
            "BUY",
            strength=8,
            confirmations=5,
        )

        self.assertTrue(
            self.system.update_result(
                record.timestamp,
                "TP1",
            )
        )

        self.assertEqual(
            self.journal.all()[0].result,
            "TP1",
        )

    def test_performance(self):

        self.system.accept_signal(
            "BUY",
            strength=8,
            confirmations=5,
        )

        self.system.accept_signal(
            "SELL",
            strength=7,
            confirmations=4,
        )

        records = self.journal.all()

        self.journal.update_result(
            records[0].timestamp,
            "TP1",
        )

        self.journal.update_result(
            records[1].timestamp,
            "SL",
        )

        summary = (
            self.system.performance_summary()
        )

        self.assertEqual(
            summary["totals"]["total"],
            2,
        )

        self.assertEqual(
            summary["win_rate"],
            50.0,
        )

    def test_no_trade_execution(self):

        forbidden = [
            "buy",
            "sell",
            "place_order",
            "execute_trade",
            "modify_order",
            "close_order",
        ]

        for name in forbidden:

            self.assertFalse(
                hasattr(
                    self.system,
                    name,
                )
            )


if __name__ == "__main__":
    unittest.main()
