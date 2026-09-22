import os
import tempfile
import unittest

from core.alert_config import AlertConfig
from core.alert_persistence import AlertPersistence
from core.persistent_alert_router import PersistentAlertRouter
from core.signal_engine import Signal


def make_signal(
    direction="BUY",
    strength=8,
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
        valid=True,
    )


class PersistentAlertRouterTest(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()

        self.path = os.path.join(
            self.temp_dir.name,
            "alert_settings.json",
        )

        persistence = AlertPersistence(
            self.path
        )

        self.system = (
            PersistentAlertRouter(
                persistence
            )
        )

    def tearDown(self):

        self.temp_dir.cleanup()

    def test_loads_default_settings(self):

        config = self.system.get_config()

        self.assertIsNotNone(
            config
        )

        self.assertTrue(
            config.alerts_enabled
        )

    def test_setting_is_saved(self):

        result = (
            self.system.set_minimum_strength(
                9
            )
        )

        self.assertTrue(result)

        self.assertTrue(
            os.path.exists(
                self.path
            )
        )

        new_system = (
            PersistentAlertRouter(
                AlertPersistence(
                    self.path
                )
            )
        )

        self.assertEqual(
            new_system.get_config().minimum_strength,
            9,
        )

    def test_buy_setting_persists(self):

        self.system.set_buy_enabled(
            False
        )

        new_system = (
            PersistentAlertRouter(
                AlertPersistence(
                    self.path
                )
            )
        )

        self.assertFalse(
            new_system.get_config().buy_enabled
        )

    def test_sell_setting_persists(self):

        self.system.set_sell_enabled(
            False
        )

        new_system = (
            PersistentAlertRouter(
                AlertPersistence(
                    self.path
                )
            )
        )

        self.assertFalse(
            new_system.get_config().sell_enabled
        )

    def test_sound_setting_persists(self):

        self.system.set_sound_enabled(
            False
        )

        new_system = (
            PersistentAlertRouter(
                AlertPersistence(
                    self.path
                )
            )
        )

        self.assertFalse(
            new_system.get_config().sound_enabled
        )

    def test_vibration_setting_persists(self):

        self.system.set_vibration_enabled(
            False
        )

        new_system = (
            PersistentAlertRouter(
                AlertPersistence(
                    self.path
                )
            )
        )

        self.assertFalse(
            new_system.get_config().vibration_enabled
        )

    def test_market_setting_persists(self):

        self.system.add_market(
            "EURUSD"
        )

        new_system = (
            PersistentAlertRouter(
                AlertPersistence(
                    self.path
                )
            )
        )

        self.assertIn(
            "EURUSD",
            new_system.get_config().selected_markets,
        )

    def test_timeframe_setting_persists(self):

        self.system.add_timeframe(
            "H4"
        )

        new_system = (
            PersistentAlertRouter(
                AlertPersistence(
                    self.path
                )
            )
        )

        self.assertIn(
            "H4",
            new_system.get_config().selected_timeframes,
        )

    def test_route_signal(self):

        result = self.system.route(
            make_signal(),
            now=1000,
        )

        self.assertEqual(
            result.status,
            "ROUTED",
        )

        self.assertIsNotNone(
            result.alert
        )

    def test_disabled_alerts_block_signal(self):

        self.system.set_alerts_enabled(
            False
        )

        result = self.system.route(
            make_signal(),
            now=1000,
        )

        self.assertEqual(
            result.status,
            "BLOCKED",
        )

        self.assertEqual(
            result.reason,
            "ALERTS_DISABLED",
        )

    def test_reload(self):

        self.system.set_minimum_strength(
            9
        )

        self.system.config.minimum_strength = 6

        config = self.system.reload()

        self.assertEqual(
            config.minimum_strength,
            9,
        )

    def test_reset(self):

        self.system.set_minimum_strength(
            9
        )

        self.assertTrue(
            self.system.reset()
        )

        self.assertEqual(
            self.system.get_config().minimum_strength,
            6,
        )

    def test_settings_path(self):

        self.assertEqual(
            self.system.settings_path(),
            os.path.abspath(
                self.path
            ),
        )

    def test_test_alert(self):

        alert, feedback = (
            self.system.test_alert(
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
            dir(PersistentAlertRouter)
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
