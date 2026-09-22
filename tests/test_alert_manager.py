import unittest

from core.alert_manager import AlertManager


class AlertManagerTest(unittest.TestCase):

    def test_buy_alert_allowed(self):

        manager = AlertManager(
            minimum_strength=6
        )

        result = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="BUY",
            strength=8,
            message="BUY signal",
            now=1000,
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            result.direction,
            "BUY",
        )

    def test_sell_alert_allowed(self):

        manager = AlertManager(
            minimum_strength=6
        )

        result = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="SELL",
            strength=8,
            message="SELL signal",
            now=1000,
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            result.direction,
            "SELL",
        )

    def test_wait_disabled_by_default(self):

        manager = AlertManager()

        result = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="WAIT",
            strength=10,
            message="WAIT",
            now=1000,
        )

        self.assertIsNone(result)

    def test_direction_can_be_enabled(self):

        manager = AlertManager()

        manager.set_direction_enabled(
            "WAIT",
            True,
        )

        result = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="WAIT",
            strength=10,
            message="WAIT",
            now=1000,
        )

        self.assertIsNotNone(result)

    def test_minimum_strength_blocks(self):

        manager = AlertManager(
            minimum_strength=8
        )

        result = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="BUY",
            strength=7,
            message="BUY",
            now=1000,
        )

        self.assertIsNone(result)

    def test_cooldown_blocks_duplicate(self):

        manager = AlertManager(
            cooldown_seconds=300
        )

        first = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="BUY",
            strength=8,
            message="BUY",
            now=1000,
        )

        second = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="BUY",
            strength=9,
            message="BUY again",
            now=1100,
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_cooldown_expires(self):

        manager = AlertManager(
            cooldown_seconds=300
        )

        manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="BUY",
            strength=8,
            message="BUY",
            now=1000,
        )

        result = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="BUY",
            strength=8,
            message="BUY again",
            now=1301,
        )

        self.assertIsNotNone(result)

    def test_buy_and_sell_have_separate_cooldowns(self):

        manager = AlertManager(
            cooldown_seconds=300
        )

        buy = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="BUY",
            strength=8,
            message="BUY",
            now=1000,
        )

        sell = manager.create_alert(
            symbol="frxXAUUSD",
            timeframe="M1",
            direction="SELL",
            strength=8,
            message="SELL",
            now=1001,
        )

        self.assertIsNotNone(buy)
        self.assertIsNotNone(sell)

    def test_test_alert(self):

        manager = AlertManager()

        result = manager.test_alert(
            "BUY",
            now=1000,
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            result.alert_type,
            "TEST",
        )
        self.assertEqual(
            result.symbol,
            "TEST",
        )

    def test_latest_event(self):

        manager = AlertManager()

        manager.create_alert(
            "frxXAUUSD",
            "M1",
            "BUY",
            8,
            "BUY",
            now=1000,
        )

        latest = manager.latest()

        self.assertIsNotNone(latest)
        self.assertEqual(
            latest.direction,
            "BUY",
        )

    def test_clear(self):

        manager = AlertManager()

        manager.create_alert(
            "frxXAUUSD",
            "M1",
            "BUY",
            8,
            "BUY",
            now=1000,
        )

        manager.clear()

        self.assertEqual(
            manager.all_events(),
            [],
        )

    def test_settings(self):

        manager = AlertManager(
            buy_enabled=True,
            sell_enabled=False,
            wait_enabled=True,
            minimum_strength=7,
            cooldown_seconds=120,
        )

        settings = manager.settings()

        self.assertTrue(
            settings["buy_enabled"]
        )

        self.assertFalse(
            settings["sell_enabled"]
        )

        self.assertTrue(
            settings["wait_enabled"]
        )

        self.assertEqual(
            settings["minimum_strength"],
            7,
        )

        self.assertEqual(
            settings["cooldown_seconds"],
            120,
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
            dir(AlertManager)
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
