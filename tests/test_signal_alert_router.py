import unittest

from core.alert_config import AlertConfig
from core.alert_manager import AlertManager
from core.alert_feedback import AlertFeedback
from core.signal_alert_router import SignalAlertRouter
from core.signal_engine import Signal


def make_signal(
    direction="BUY",
    strength=8,
    valid=True,
    symbol="XAUUSD",
    timeframe="M1",
):

    return Signal(
        symbol=symbol,
        timeframe=timeframe,
        direction=direction,
        strength=strength,
        confirmations=5,
        entry=100.0,
        stop_loss=95.0,
        tp1=105.0,
        tp2=110.0,
        invalidation=95.0,
        explanation="test",
        candle_confirmed=True,
        valid=valid,
    )


class SignalAlertRouterTest(unittest.TestCase):

    def make_router(
        self,
        config=None,
    ):

        config = (
            config
            or AlertConfig(
                selected_markets=[
                    "XAUUSD"
                ],
                selected_timeframes=[
                    "M1"
                ],
            )
        )

        return SignalAlertRouter(
            config=config,
            manager=AlertManager(),
            feedback=AlertFeedback(),
        )

    def test_valid_buy_creates_alert(self):

        router = self.make_router()

        result = router.route(
            make_signal("BUY"),
            now=1000,
        )

        self.assertEqual(
            result.status,
            "ROUTED",
        )

        self.assertIsNotNone(
            result.alert
        )

        self.assertIsNotNone(
            result.feedback
        )

    def test_valid_sell_creates_alert(self):

        router = self.make_router()

        result = router.route(
            make_signal("SELL"),
            now=1000,
        )

        self.assertEqual(
            result.status,
            "ROUTED",
        )

        self.assertEqual(
            result.alert.direction,
            "SELL",
        )

    def test_invalid_signal_blocked(self):

        router = self.make_router()

        result = router.route(
            make_signal(
                valid=False
            ),
            now=1000,
        )

        self.assertEqual(
            result.status,
            "BLOCKED",
        )

        self.assertEqual(
            result.reason,
            "INVALID_SIGNAL",
        )

    def test_alerts_disabled(self):

        config = AlertConfig(
            alerts_enabled=False,
            selected_markets=[
                "XAUUSD"
            ],
            selected_timeframes=[
                "M1"
            ],
        )

        router = self.make_router(
            config
        )

        result = router.route(
            make_signal(),
            now=1000,
        )

        self.assertEqual(
            result.reason,
            "ALERTS_DISABLED",
        )

    def test_market_disabled(self):

        config = AlertConfig(
            selected_markets=[
                "BTCUSD"
            ],
            selected_timeframes=[
                "M1"
            ],
        )

        router = self.make_router(
            config
        )

        result = router.route(
            make_signal(),
            now=1000,
        )

        self.assertEqual(
            result.reason,
            "MARKET_DISABLED",
        )

    def test_timeframe_disabled(self):

        config = AlertConfig(
            selected_markets=[
                "XAUUSD"
            ],
            selected_timeframes=[
                "H1"
            ],
        )

        router = self.make_router(
            config
        )

        result = router.route(
            make_signal(),
            now=1000,
        )

        self.assertEqual(
            result.reason,
            "TIMEFRAME_DISABLED",
        )

    def test_strength_filter(self):

        config = AlertConfig(
            minimum_strength=9,
            selected_markets=[
                "XAUUSD"
            ],
            selected_timeframes=[
                "M1"
            ],
        )

        router = self.make_router(
            config
        )

        result = router.route(
            make_signal(
                strength=8
            ),
            now=1000,
        )

        self.assertEqual(
            result.status,
            "BLOCKED",
        )

        self.assertEqual(
            result.reason,
            "STRENGTH_TOO_LOW",
        )

    def test_buy_direction_disabled(self):

        config = AlertConfig(
            buy_enabled=False,
            selected_markets=[
                "XAUUSD"
            ],
            selected_timeframes=[
                "M1"
            ],
        )

        router = self.make_router(
            config
        )

        result = router.route(
            make_signal("BUY"),
            now=1000,
        )

        self.assertEqual(
            result.reason,
            "DIRECTION_DISABLED",
        )

    def test_sell_direction_disabled(self):

        config = AlertConfig(
            sell_enabled=False,
            selected_markets=[
                "XAUUSD"
            ],
            selected_timeframes=[
                "M1"
            ],
        )

        router = self.make_router(
            config
        )

        result = router.route(
            make_signal("SELL"),
            now=1000,
        )

        self.assertEqual(
            result.reason,
            "DIRECTION_DISABLED",
        )

    def test_duplicate_alert_blocked(self):

        router = self.make_router()

        first = router.route(
            make_signal("BUY"),
            now=1000,
        )

        second = router.route(
            make_signal("BUY"),
            now=1100,
        )

        self.assertEqual(
            first.status,
            "ROUTED",
        )

        self.assertEqual(
            second.status,
            "BLOCKED",
        )

        self.assertEqual(
            second.reason,
            "ALERT_COOLDOWN",
        )

    def test_buy_and_sell_can_alert_separately(self):

        router = self.make_router()

        buy = router.route(
            make_signal("BUY"),
            now=1000,
        )

        sell = router.route(
            make_signal("SELL"),
            now=1001,
        )

        self.assertEqual(
            buy.status,
            "ROUTED",
        )

        self.assertEqual(
            sell.status,
            "ROUTED",
        )

    def test_feedback_matches_direction(self):

        router = self.make_router()

        result = router.route(
            make_signal("SELL"),
            now=1000,
        )

        self.assertEqual(
            result.feedback.direction,
            "SELL",
        )

    def test_test_alert(self):

        router = self.make_router()

        alert, feedback = (
            router.test_alert(
                "BUY",
                now=1000,
            )
        )

        self.assertIsNotNone(
            alert
        )

        self.assertIsNotNone(
            feedback
        )

        self.assertEqual(
            alert.alert_type,
            "TEST",
        )

    def test_history(self):

        router = self.make_router()

        router.route(
            make_signal("BUY"),
            now=1000,
        )

        self.assertEqual(
            len(
                router.alert_history()
            ),
            1,
        )

        self.assertEqual(
            len(
                router.feedback_history()
            ),
            1,
        )

    def test_settings(self):

        router = self.make_router()

        settings = router.settings()

        self.assertIn(
            "config",
            settings,
        )

        self.assertIn(
            "manager",
            settings,
        )

        self.assertIn(
            "feedback",
            settings,
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
            dir(SignalAlertRouter)
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
