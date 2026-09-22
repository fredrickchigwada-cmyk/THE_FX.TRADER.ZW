import unittest

from core.alert_config import AlertConfig


class AlertConfigTest(unittest.TestCase):

    def test_default_configuration(self):

        config = AlertConfig()

        self.assertTrue(
            config.alerts_enabled
        )

        self.assertTrue(
            config.buy_enabled
        )

        self.assertTrue(
            config.sell_enabled
        )

        self.assertFalse(
            config.wait_enabled
        )

        self.assertTrue(
            config.sound_enabled
        )

        self.assertTrue(
            config.vibration_enabled
        )

        self.assertEqual(
            config.minimum_strength,
            6,
        )

        self.assertEqual(
            config.cooldown_seconds,
            300,
        )

    def test_strength_is_clamped(self):

        config = AlertConfig(
            minimum_strength=99
        )

        self.assertEqual(
            config.minimum_strength,
            10,
        )

        config.set_minimum_strength(
            -5
        )

        self.assertEqual(
            config.minimum_strength,
            1,
        )

    def test_cooldown_cannot_be_negative(self):

        config = AlertConfig(
            cooldown_seconds=-100
        )

        self.assertEqual(
            config.cooldown_seconds,
            0,
        )

    def test_direction_settings(self):

        config = AlertConfig()

        config.set_buy_enabled(False)
        config.set_sell_enabled(False)
        config.set_wait_enabled(True)

        self.assertFalse(
            config.buy_enabled
        )

        self.assertFalse(
            config.sell_enabled
        )

        self.assertTrue(
            config.wait_enabled
        )

    def test_sound_vibration(self):

        config = AlertConfig()

        config.set_sound_enabled(False)
        config.set_vibration_enabled(False)

        self.assertFalse(
            config.sound_enabled
        )

        self.assertFalse(
            config.vibration_enabled
        )

    def test_master_switch_blocks_directions(self):

        config = AlertConfig()

        config.set_alerts_enabled(False)

        self.assertFalse(
            config.direction_enabled("BUY")
        )

        self.assertFalse(
            config.direction_enabled("SELL")
        )

    def test_markets(self):

        config = AlertConfig()

        config.set_markets([
            "XAUUSD",
            "BTCUSD",
            "XAUUSD",
        ])

        self.assertEqual(
            config.selected_markets,
            [
                "XAUUSD",
                "BTCUSD",
            ],
        )

        self.assertTrue(
            config.market_enabled("xauusd")
        )

    def test_add_remove_market(self):

        config = AlertConfig()

        config.add_market(
            "EURUSD"
        )

        self.assertTrue(
            config.market_enabled(
                "EURUSD"
            )
        )

        config.remove_market(
            "EURUSD"
        )

        self.assertFalse(
            config.market_enabled(
                "EURUSD"
            )
        )

    def test_timeframes(self):

        config = AlertConfig()

        config.set_timeframes([
            "M1",
            "M5",
            "M1",
        ])

        self.assertEqual(
            config.selected_timeframes,
            [
                "M1",
                "M5",
            ],
        )

        self.assertTrue(
            config.timeframe_enabled("m5")
        )

    def test_add_remove_timeframe(self):

        config = AlertConfig()

        config.add_timeframe(
            "H1"
        )

        self.assertTrue(
            config.timeframe_enabled(
                "H1"
            )
        )

        config.remove_timeframe(
            "H1"
        )

        self.assertFalse(
            config.timeframe_enabled(
                "H1"
            )
        )

    def test_serialization_round_trip(self):

        original = AlertConfig(
            alerts_enabled=False,
            buy_enabled=False,
            sell_enabled=True,
            wait_enabled=True,
            sound_enabled=False,
            vibration_enabled=True,
            minimum_strength=8,
            cooldown_seconds=120,
            selected_markets=[
                "XAUUSD",
                "BTCUSD",
            ],
            selected_timeframes=[
                "M1",
                "H1",
            ],
        )

        data = original.to_dict()

        restored = AlertConfig.from_dict(
            data
        )

        self.assertEqual(
            restored.to_dict(),
            data,
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
            dir(AlertConfig)
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
