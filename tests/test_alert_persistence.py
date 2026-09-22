import json
import os
import tempfile
import unittest

from core.alert_config import AlertConfig
from core.alert_persistence import AlertPersistence


class AlertPersistenceTest(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()

        self.filepath = os.path.join(
            self.temp_dir.name,
            "alert_settings.json",
        )

        self.persistence = AlertPersistence(
            self.filepath
        )

    def tearDown(self):

        self.temp_dir.cleanup()

    def test_save_creates_file(self):

        config = AlertConfig()

        result = self.persistence.save(
            config
        )

        self.assertTrue(result)

        self.assertTrue(
            self.persistence.exists()
        )

        self.assertTrue(
            os.path.isfile(
                self.persistence.path()
            )
        )

    def test_save_and_load(self):

        config = AlertConfig(
            alerts_enabled=True,
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
                "M15",
                "H1",
            ],
        )

        self.assertTrue(
            self.persistence.save(config)
        )

        loaded = self.persistence.load()

        self.assertEqual(
            loaded.to_dict(),
            config.to_dict(),
        )

    def test_missing_file_returns_default(self):

        default = AlertConfig(
            minimum_strength=9
        )

        loaded = self.persistence.load(
            default
        )

        self.assertEqual(
            loaded.minimum_strength,
            9,
        )

    def test_invalid_json_returns_default(self):

        with open(
            self.filepath,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                "{invalid json"
            )

        default = AlertConfig(
            minimum_strength=7
        )

        loaded = self.persistence.load(
            default
        )

        self.assertEqual(
            loaded.minimum_strength,
            7,
        )

    def test_non_dictionary_json_returns_default(self):

        with open(
            self.filepath,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                ["invalid"],
                file,
            )

        default = AlertConfig(
            minimum_strength=6
        )

        loaded = self.persistence.load(
            default
        )

        self.assertEqual(
            loaded.minimum_strength,
            6,
        )

    def test_delete(self):

        config = AlertConfig()

        self.persistence.save(
            config
        )

        self.assertTrue(
            self.persistence.exists()
        )

        self.assertTrue(
            self.persistence.delete()
        )

        self.assertFalse(
            self.persistence.exists()
        )

    def test_delete_missing_file(self):

        self.assertTrue(
            self.persistence.delete()
        )

    def test_file_is_valid_json(self):

        config = AlertConfig(
            minimum_strength=8
        )

        self.persistence.save(
            config
        )

        with open(
            self.filepath,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        self.assertIsInstance(
            data,
            dict,
        )

        self.assertEqual(
            data["minimum_strength"],
            8,
        )

    def test_atomic_save_replaces_previous(self):

        first = AlertConfig(
            minimum_strength=6
        )

        second = AlertConfig(
            minimum_strength=9
        )

        self.persistence.save(
            first
        )

        self.persistence.save(
            second
        )

        loaded = self.persistence.load()

        self.assertEqual(
            loaded.minimum_strength,
            9,
        )

    def test_custom_path(self):

        custom_path = os.path.join(
            self.temp_dir.name,
            "custom.json",
        )

        persistence = AlertPersistence(
            custom_path
        )

        self.assertEqual(
            persistence.path(),
            os.path.abspath(
                custom_path
            ),
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
            dir(AlertPersistence)
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
