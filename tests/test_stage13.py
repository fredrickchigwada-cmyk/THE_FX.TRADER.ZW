import os
import tempfile
import unittest

from core.signal_journal import (
    SignalJournal,
    PerformanceTracker,
)


class TestStage13(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile(
            delete=False
        )
        self.temp.close()

        self.journal = SignalJournal(
            self.temp.name
        )

    def tearDown(self):
        try:
            os.remove(self.temp.name)
        except FileNotFoundError:
            pass

    def test_add_signal(self):
        record = self.journal.add(
            symbol="XAUUSD",
            timeframe="M1",
            signal="BUY",
            strength=8,
            confirmations=5,
            entry=4365.0,
            stop_loss=4362.0,
            tp1=4368.0,
            tp2=4371.0,
        )

        self.assertEqual(record.symbol, "XAUUSD")
        self.assertEqual(record.signal, "BUY")
        self.assertEqual(record.result, "PENDING")

    def test_persistence(self):
        self.journal.add(
            "XAUUSD",
            "M1",
            "BUY",
            8,
            5,
            4365,
            4362,
            4368,
            4371,
        )

        loaded = SignalJournal(
            self.temp.name
        )

        self.assertEqual(
            loaded.count(),
            1,
        )

    def test_update_result(self):
        record = self.journal.add(
            "XAUUSD",
            "M1",
            "BUY",
        )

        self.assertTrue(
            self.journal.update_result(
                record.timestamp,
                "TP1",
            )
        )

        self.assertEqual(
            self.journal.all()[0].result,
            "TP1",
        )

    def test_totals(self):
        self.journal.add(
            "XAUUSD",
            "M1",
            "BUY",
            result="TP1",
        )

        self.journal.add(
            "BTCUSD",
            "M5",
            "SELL",
            result="SL",
        )

        self.journal.add(
            "EURUSD",
            "M15",
            "WAIT",
        )

        totals = PerformanceTracker(
            self.journal
        ).totals()

        self.assertEqual(totals["total"], 3)
        self.assertEqual(totals["buy"], 1)
        self.assertEqual(totals["sell"], 1)
        self.assertEqual(totals["wait"], 1)
        self.assertEqual(totals["tp1"], 1)
        self.assertEqual(totals["sl"], 1)

    def test_win_rate(self):
        self.journal.add(
            "XAUUSD",
            "M1",
            "BUY",
            result="TP1",
        )

        self.journal.add(
            "XAUUSD",
            "M1",
            "SELL",
            result="SL",
        )

        tracker = PerformanceTracker(
            self.journal
        )

        self.assertEqual(
            tracker.win_rate(),
            50.0,
        )

    def test_no_results_means_no_win_rate(self):
        self.journal.add(
            "XAUUSD",
            "M1",
            "WAIT",
        )

        tracker = PerformanceTracker(
            self.journal
        )

        self.assertIsNone(
            tracker.win_rate()
        )

    def test_symbol_statistics(self):
        self.journal.add(
            "XAUUSD",
            "M1",
            "BUY",
            result="TP2",
        )

        stats = PerformanceTracker(
            self.journal
        ).by_symbol()

        self.assertEqual(
            stats["XAUUSD"]["signals"],
            1,
        )

        self.assertEqual(
            stats["XAUUSD"]["wins"],
            1,
        )

    def test_timeframe_statistics(self):
        self.journal.add(
            "XAUUSD",
            "M5",
            "BUY",
            result="SL",
        )

        stats = PerformanceTracker(
            self.journal
        ).by_timeframe()

        self.assertEqual(
            stats["M5"]["losses"],
            1,
        )

    def test_direction_statistics(self):
        self.journal.add(
            "XAUUSD",
            "M1",
            "SELL",
            result="TP1",
        )

        stats = PerformanceTracker(
            self.journal
        ).by_direction()

        self.assertEqual(
            stats["SELL"]["wins"],
            1,
        )

    def test_invalid_signal_rejected(self):
        with self.assertRaises(ValueError):
            self.journal.add(
                "XAUUSD",
                "M1",
                "HOLD",
            )

    def test_invalid_result_rejected(self):
        with self.assertRaises(ValueError):
            self.journal.add(
                "XAUUSD",
                "M1",
                "BUY",
                result="PROFIT",
            )

    def test_recent(self):
        self.journal.add(
            "XAUUSD",
            "M1",
            "BUY",
        )

        self.journal.add(
            "BTCUSD",
            "M5",
            "SELL",
        )

        recent = self.journal.recent(1)

        self.assertEqual(
            len(recent),
            1,
        )

        self.assertEqual(
            recent[0].symbol,
            "BTCUSD",
        )


if __name__ == "__main__":
    unittest.main()
