from typing import Optional

from core.android_alert_bridge import AndroidAlertBridge
from core.persistent_alert_router import PersistentAlertRouter


class LiveAlertDispatcher:
    """
    Final bridge between the signal alert system and Android.

    Signal-only:
    This component sends notifications/feedback only.
    It has no trading execution capability.
    """

    VIBRATION_PATTERNS = {
        "SHORT": 250,
        "MEDIUM": 500,
        "LONG": 900,
    }

    def __init__(
        self,
        alert_router: Optional[PersistentAlertRouter] = None,
        android: Optional[AndroidAlertBridge] = None,
    ):

        self.alert_router = (
            alert_router
            or PersistentAlertRouter()
        )

        self.android = (
            android
            or AndroidAlertBridge()
        )

    def dispatch(
        self,
        signal,
        now=None,
    ):

        # ---------------------------------------------
        # Route through all alert filters first
        # ---------------------------------------------

        routed = self.alert_router.route(
            signal,
            now=now,
        )

        if routed.status != "ROUTED":

            return {
                "status": "BLOCKED",
                "reason": routed.reason,
                "alert": None,
                "android": None,
            }

        alert = routed.alert
        feedback = routed.feedback

        android_result = {}

        # ---------------------------------------------
        # Android notification
        # ---------------------------------------------

        android_result["notification"] = (
            self.android.notify(
                title=(
                    f"THE_FX.TRADER.BOT.ZW • "
                    f"{signal.direction}"
                ),
                content=(
                    f"{signal.symbol} "
                    f"{signal.timeframe}\n"
                    f"Strength: "
                    f"{signal.strength}/10\n"
                    f"{signal.explanation}"
                ),
                notification_id=(
                    f"fx_{signal.symbol}_"
                    f"{signal.timeframe}_"
                    f"{signal.direction}"
                ),
            )
        )

        # ---------------------------------------------
        # Vibration
        # ---------------------------------------------

        if self.alert_router.config.vibration_enabled:

            pattern = getattr(
                feedback,
                "vibration_pattern",
                "MEDIUM",
            )

            duration = (
                self.VIBRATION_PATTERNS.get(
                    str(pattern).upper(),
                    500,
                )
            )

            android_result["vibration"] = (
                self.android.vibrate(
                    duration
                )
            )

        # ---------------------------------------------
        # Custom sound
        # ---------------------------------------------

        sound_file = getattr(
            feedback,
            "sound_file",
            None,
        )

        if (
            self.alert_router.config.sound_enabled
            and sound_file
        ):

            android_result["sound"] = (
                self.android.play_sound(
                    sound_file
                )
            )

        else:

            android_result["sound"] = None

        return {
            "status": "DISPATCHED",
            "reason": "ALERT_SENT_TO_ANDROID",
            "alert": alert,
            "feedback": feedback,
            "android": android_result,
        }

    def test_android(
        self,
    ):

        notification = (
            self.android.test_notification()
        )

        vibration = (
            self.android.test_vibration()
        )

        return {
            "notification": notification,
            "vibration": vibration,
        }

    def android_available(self):

        return self.android.available()

    def settings(self):

        return self.alert_router.settings()

    def alert_history(self):

        return self.alert_router.alert_history()

    def feedback_history(self):

        return self.alert_router.feedback_history()


if __name__ == "__main__":

    dispatcher = LiveAlertDispatcher()

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 10I - Live Alert Dispatcher"
    )

    print(
        f"Android bridge available: "
        f"{dispatcher.android_available()}"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
