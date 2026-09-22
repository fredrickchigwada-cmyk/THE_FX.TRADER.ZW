import unittest
from unittest.mock import Mock

from core.integration_pipeline import IntegrationPipeline
from core.signal_engine import Signal


def make_signal(direction="BUY", valid=True):
    return Signal(
        symbol="XAUUSD",
        timeframe="M5",
        direction=direction,
        strength=8,
        confirmations=3,
        entry=3000.0 if direction != "WAIT" else None,
        stop_loss=2990.0 if direction == "BUY" else None,
        tp1=3010.0 if direction == "BUY" else None,
        tp2=3020.0 if direction == "BUY" else None,
        invalidation=2990.0 if direction == "BUY" else None,
        explanation="Stage 18O test signal",
        candle_confirmed=True,
        valid=valid,
    )


class TestStage18OSignalJournalAlertFlow(unittest.TestCase):

    def build_pipeline(self):
        system = Mock()
        system.emergency_stop = False

        journal_record = Mock()
        system.accept_signal.return_value = journal_record

        alert_dispatcher = Mock()
        alert_dispatcher.dispatch.return_value = True

        pipeline = IntegrationPipeline(
            system=system,
            alert_dispatcher=alert_dispatcher,
        )

        return pipeline, system, alert_dispatcher

    def test_valid_buy_is_journaled_once(self):
        pipeline, system, alert_dispatcher = self.build_pipeline()

        signal = make_signal("BUY")

        result = pipeline.process_signal(
            signal,
            news_risk="LOW",
            news_bias="NEUTRAL",
        )

        self.assertEqual(result.status, "PROCESSED")
        self.assertEqual(result.signal, "BUY")
        self.assertTrue(result.journaled)

        system.accept_signal.assert_called_once()
        alert_dispatcher.dispatch.assert_called_once_with(signal)

    def test_valid_sell_is_journaled_once(self):
        pipeline, system, alert_dispatcher = self.build_pipeline()

        signal = make_signal("SELL")

        result = pipeline.process_signal(
            signal,
            news_risk="LOW",
            news_bias="NEUTRAL",
        )

        self.assertEqual(result.status, "PROCESSED")
        self.assertEqual(result.signal, "SELL")
        self.assertTrue(result.journaled)

        system.accept_signal.assert_called_once()
        alert_dispatcher.dispatch.assert_called_once_with(signal)

    def test_wait_is_not_journaled_or_alerted(self):
        pipeline, system, alert_dispatcher = self.build_pipeline()

        signal = make_signal("WAIT")

        result = pipeline.process_signal(
            signal,
            news_risk="LOW",
            news_bias="NEUTRAL",
        )

        self.assertEqual(result.status, "PROCESSED")
        self.assertEqual(result.signal, "WAIT")
        self.assertFalse(result.journaled)
        self.assertFalse(result.alerted)

        system.accept_signal.assert_not_called()
        alert_dispatcher.dispatch.assert_not_called()

    def test_pipeline_records_directional_signal_without_runtime_validation(self):
        # IntegrationPipeline receives already-validated signals.
        # ProductionRuntime performs the valid/invalid gate upstream.
        pipeline, system, alert_dispatcher = self.build_pipeline()

        signal = make_signal("BUY", valid=False)

        result = pipeline.process_signal(
            signal,
            news_risk="LOW",
            news_bias="NEUTRAL",
        )

        self.assertEqual(result.status, "PROCESSED")
        self.assertEqual(result.signal, "BUY")
        self.assertTrue(result.journaled)
        self.assertTrue(result.alerted)

        system.accept_signal.assert_called_once()
        alert_dispatcher.dispatch.assert_called_once_with(signal)

    def test_emergency_stop_blocks_journal_and_alert(self):
        pipeline, system, alert_dispatcher = self.build_pipeline()

        system.emergency_stop = True

        signal = make_signal("BUY")

        result = pipeline.process_signal(
            signal,
            news_risk="LOW",
            news_bias="NEUTRAL",
        )

        self.assertEqual(result.status, "EMERGENCY_STOP")
        self.assertEqual(result.signal, "WAIT")
        self.assertFalse(result.journaled)
        self.assertFalse(result.alerted)

        system.accept_signal.assert_not_called()
        alert_dispatcher.dispatch.assert_not_called()

    def test_high_impact_conflicting_news_blocks_buy(self):
        pipeline, system, alert_dispatcher = self.build_pipeline()

        signal = make_signal("BUY")

        result = pipeline.process_signal(
            signal,
            news_risk="HIGH",
            news_bias="BEARISH",
        )

        self.assertEqual(result.status, "NEWS_BLOCKED")
        self.assertEqual(result.signal, "WAIT")
        self.assertFalse(result.journaled)
        self.assertFalse(result.alerted)

        system.accept_signal.assert_not_called()
        alert_dispatcher.dispatch.assert_not_called()

    def test_high_impact_conflicting_news_blocks_sell(self):
        pipeline, system, alert_dispatcher = self.build_pipeline()

        signal = make_signal("SELL")

        result = pipeline.process_signal(
            signal,
            news_risk="HIGH",
            news_bias="BULLISH",
        )

        self.assertEqual(result.status, "NEWS_BLOCKED")
        self.assertEqual(result.signal, "WAIT")
        self.assertFalse(result.journaled)
        self.assertFalse(result.alerted)

        system.accept_signal.assert_not_called()
        alert_dispatcher.dispatch.assert_not_called()

    def test_alert_dispatch_failure_does_not_duplicate_journal(self):
        pipeline, system, alert_dispatcher = self.build_pipeline()

        alert_dispatcher.dispatch.side_effect = RuntimeError(
            "simulated alert failure"
        )

        signal = make_signal("BUY")

        result = pipeline.process_signal(
            signal,
            news_risk="LOW",
            news_bias="NEUTRAL",
        )

        self.assertEqual(result.status, "PROCESSED")
        self.assertEqual(result.signal, "BUY")
        self.assertTrue(result.journaled)
        self.assertFalse(result.alerted)

        system.accept_signal.assert_called_once()
        alert_dispatcher.dispatch.assert_called_once_with(signal)


if __name__ == "__main__":
    unittest.main()
