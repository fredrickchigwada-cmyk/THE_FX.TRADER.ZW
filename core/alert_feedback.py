import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FeedbackEvent:
    direction: str
    sound: bool
    vibration: bool
    vibration_pattern: str
    timestamp: float
    event_type: str = "SIGNAL"


class AlertFeedback:
    """
    Controls sound and vibration decisions for alerts.

    SIGNAL-ONLY:
    This module provides alert feedback only.
    It cannot place, modify, or close trades.
    """

    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"

    VALID_PATTERNS = {
        SHORT,
        MEDIUM,
        LONG,
    }

    def __init__(
        self,
        sound_enabled: bool = True,
        vibration_enabled: bool = True,
        vibration_pattern: str = MEDIUM,
    ):
        self.sound_enabled = bool(
            sound_enabled
        )

        self.vibration_enabled = bool(
            vibration_enabled
        )

        self.vibration_pattern = (
            vibration_pattern.upper()
        )

        if (
            self.vibration_pattern
            not in self.VALID_PATTERNS
        ):
            self.vibration_pattern = (
                self.MEDIUM
            )

        self.events: List[
            FeedbackEvent
        ] = []

    # ================================================
    # SETTINGS
    # ================================================

    def set_sound_enabled(
        self,
        enabled: bool,
    ):

        self.sound_enabled = bool(
            enabled
        )

    def set_vibration_enabled(
        self,
        enabled: bool,
    ):

        self.vibration_enabled = bool(
            enabled
        )

    def set_vibration_pattern(
        self,
        pattern: str,
    ):

        pattern = str(
            pattern
        ).upper()

        if pattern not in self.VALID_PATTERNS:
            raise ValueError(
                "Vibration pattern must be "
                "SHORT, MEDIUM, or LONG."
            )

        self.vibration_pattern = pattern

    # ================================================
    # FEEDBACK DECISION
    # ================================================

    def should_play_sound(
        self,
    ) -> bool:

        return self.sound_enabled

    def should_vibrate(
        self,
    ) -> bool:

        return self.vibration_enabled

    def build_feedback(
        self,
        direction: str,
        now: Optional[float] = None,
        event_type: str = "SIGNAL",
    ) -> FeedbackEvent:

        if now is None:
            now = time.time()

        direction = str(
            direction
        ).upper()

        event = FeedbackEvent(
            direction=direction,
            sound=self.should_play_sound(),
            vibration=self.should_vibrate(),
            vibration_pattern=(
                self.vibration_pattern
            ),
            timestamp=now,
            event_type=event_type,
        )

        self.events.append(event)

        return event

    # ================================================
    # TEST FEEDBACK
    # ================================================

    def test_sound(
        self,
        now: Optional[float] = None,
    ) -> FeedbackEvent:

        return self.build_feedback(
            direction="TEST",
            now=now,
            event_type="TEST_SOUND",
        )

    def test_vibration(
        self,
        now: Optional[float] = None,
    ) -> FeedbackEvent:

        return self.build_feedback(
            direction="TEST",
            now=now,
            event_type="TEST_VIBRATION",
        )

    def test_alert(
        self,
        now: Optional[float] = None,
    ) -> FeedbackEvent:

        return self.build_feedback(
            direction="TEST",
            now=now,
            event_type="TEST_ALERT",
        )

    # ================================================
    # HISTORY
    # ================================================

    def record(self, alert):
        """Record feedback for an alert using its direction."""
        direction = getattr(alert, "direction", None)

        if direction is None:
            direction = getattr(alert, "signal", None)

        if hasattr(direction, "direction"):
            direction = direction.direction

        if direction is None:
            direction = "WAIT"

        return self.build_feedback(
            str(direction).upper(),
            now=getattr(alert, "timestamp", None),
            event_type=getattr(alert, "alert_type", "SIGNAL"),
        )

    def record_alert(self, alert):
        """Compatibility method used by SignalAlertRouter."""
        return self.record(alert)

    def all_events(
        self,
    ) -> List[FeedbackEvent]:

        return list(self.events)

    def latest(
        self,
    ) -> Optional[FeedbackEvent]:

        if not self.events:
            return None

        return self.events[-1]

    def clear(self):

        self.events.clear()

    # ================================================
    # STATUS
    # ================================================

    def settings(self) -> dict:

        return {
            "sound_enabled":
                self.sound_enabled,

            "vibration_enabled":
                self.vibration_enabled,

            "vibration_pattern":
                self.vibration_pattern,
        }


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 10C - Alert Feedback"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
