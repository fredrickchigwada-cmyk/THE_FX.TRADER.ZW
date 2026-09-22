import unittest

from core.alert_feedback import AlertFeedback


class AlertFeedbackTest(unittest.TestCase):

    def test_default_settings(self):

        feedback = AlertFeedback()

        self.assertTrue(
            feedback.sound_enabled
        )

        self.assertTrue(
            feedback.vibration_enabled
        )

        self.assertEqual(
            feedback.vibration_pattern,
            "MEDIUM",
        )

    def test_sound_can_be_disabled(self):

        feedback = AlertFeedback()

        feedback.set_sound_enabled(
            False
        )

        self.assertFalse(
            feedback.should_play_sound()
        )

    def test_vibration_can_be_disabled(self):

        feedback = AlertFeedback()

        feedback.set_vibration_enabled(
            False
        )

        self.assertFalse(
            feedback.should_vibrate()
        )

    def test_short_pattern(self):

        feedback = AlertFeedback()

        feedback.set_vibration_pattern(
            "SHORT"
        )

        self.assertEqual(
            feedback.vibration_pattern,
            "SHORT",
        )

    def test_medium_pattern(self):

        feedback = AlertFeedback()

        feedback.set_vibration_pattern(
            "MEDIUM"
        )

        self.assertEqual(
            feedback.vibration_pattern,
            "MEDIUM",
        )

    def test_long_pattern(self):

        feedback = AlertFeedback()

        feedback.set_vibration_pattern(
            "LONG"
        )

        self.assertEqual(
            feedback.vibration_pattern,
            "LONG",
        )

    def test_invalid_pattern(self):

        feedback = AlertFeedback()

        with self.assertRaises(
            ValueError
        ):

            feedback.set_vibration_pattern(
                "INVALID"
            )

    def test_buy_feedback(self):

        feedback = AlertFeedback()

        event = feedback.build_feedback(
            direction="BUY",
            now=1000,
        )

        self.assertEqual(
            event.direction,
            "BUY",
        )

        self.assertTrue(
            event.sound
        )

        self.assertTrue(
            event.vibration
        )

    def test_sell_feedback(self):

        feedback = AlertFeedback()

        event = feedback.build_feedback(
            direction="SELL",
            now=1000,
        )

        self.assertEqual(
            event.direction,
            "SELL",
        )

    def test_disabled_feedback(self):

        feedback = AlertFeedback(
            sound_enabled=False,
            vibration_enabled=False,
        )

        event = feedback.build_feedback(
            direction="BUY",
            now=1000,
        )

        self.assertFalse(
            event.sound
        )

        self.assertFalse(
            event.vibration
        )

    def test_test_alert(self):

        feedback = AlertFeedback()

        event = feedback.test_alert(
            now=1000
        )

        self.assertEqual(
            event.event_type,
            "TEST_ALERT",
        )

        self.assertEqual(
            event.direction,
            "TEST",
        )

    def test_history(self):

        feedback = AlertFeedback()

        feedback.build_feedback(
            "BUY",
            now=1000,
        )

        feedback.build_feedback(
            "SELL",
            now=1001,
        )

        self.assertEqual(
            len(
                feedback.all_events()
            ),
            2,
        )

        self.assertEqual(
            feedback.latest().direction,
            "SELL",
        )

    def test_clear(self):

        feedback = AlertFeedback()

        feedback.test_alert(
            now=1000
        )

        feedback.clear()

        self.assertEqual(
            feedback.all_events(),
            [],
        )

    def test_settings(self):

        feedback = AlertFeedback(
            sound_enabled=False,
            vibration_enabled=True,
            vibration_pattern="LONG",
        )

        settings = feedback.settings()

        self.assertFalse(
            settings["sound_enabled"]
        )

        self.assertTrue(
            settings["vibration_enabled"]
        )

        self.assertEqual(
            settings["vibration_pattern"],
            "LONG",
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
            dir(AlertFeedback)
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
