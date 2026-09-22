import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class AndroidAlertResult:
    success: bool
    action: str
    message: str


class AndroidAlertBridge:
    """
    Android notification/sound/vibration bridge for Termux.

    This component only communicates alerts to Android.
    It has NO trading or order-execution functionality.
    """

    def __init__(self, command_runner=None):
        self.command_runner = (
            command_runner or self._run_command
        )

    @staticmethod
    def _run_command(command):
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def available(self) -> bool:
        try:
            result = self.command_runner(
                ["which", "termux-notification"]
            )
            return result.returncode == 0
        except Exception:
            return False

    def notify(
        self,
        title: str,
        content: str,
        notification_id: str = "fx_trader_alert",
    ) -> AndroidAlertResult:

        command = [
            "termux-notification",
            "--id",
            notification_id,
            "--title",
            title,
            "--content",
            content,
            "--priority",
            "high",
            "--sound",
        ]

        try:
            result = self.command_runner(
                command
            )

            if result.returncode == 0:
                return AndroidAlertResult(
                    success=True,
                    action="NOTIFICATION",
                    message="Android notification sent",
                )

            return AndroidAlertResult(
                success=False,
                action="NOTIFICATION",
                message=(
                    result.stderr.strip()
                    or "Notification command failed"
                ),
            )

        except Exception as exc:

            return AndroidAlertResult(
                success=False,
                action="NOTIFICATION",
                message=str(exc),
            )

    def vibrate(
        self,
        duration_ms: int = 500,
    ) -> AndroidAlertResult:

        duration_ms = max(
            1,
            int(duration_ms),
        )

        command = [
            "termux-vibrate",
            "-d",
            str(duration_ms),
        ]

        try:
            result = self.command_runner(
                command
            )

            if result.returncode == 0:
                return AndroidAlertResult(
                    success=True,
                    action="VIBRATION",
                    message="Android vibration triggered",
                )

            return AndroidAlertResult(
                success=False,
                action="VIBRATION",
                message=(
                    result.stderr.strip()
                    or "Vibration command failed"
                ),
            )

        except Exception as exc:

            return AndroidAlertResult(
                success=False,
                action="VIBRATION",
                message=str(exc),
            )

    def play_sound(
        self,
        sound_file: Optional[str] = None,
    ) -> AndroidAlertResult:

        if not sound_file:
            return AndroidAlertResult(
                success=False,
                action="SOUND",
                message="No custom sound file specified",
            )

        command = [
            "termux-media-player",
            "play",
            sound_file,
        ]

        try:
            result = self.command_runner(
                command
            )

            if result.returncode == 0:
                return AndroidAlertResult(
                    success=True,
                    action="SOUND",
                    message="Android sound playback started",
                )

            return AndroidAlertResult(
                success=False,
                action="SOUND",
                message=(
                    result.stderr.strip()
                    or "Sound command failed"
                ),
            )

        except Exception as exc:

            return AndroidAlertResult(
                success=False,
                action="SOUND",
                message=str(exc),
            )

    def send_alert(
        self,
        direction: str,
        symbol: str,
        timeframe: str,
        strength: int,
        message: str,
        vibration_ms: Optional[int] = None,
        sound_file: Optional[str] = None,
    ):

        title = (
            f"THE_FX.TRADER.BOT.ZW • "
            f"{direction}"
        )

        content = (
            f"{symbol} {timeframe}\n"
            f"Strength: {strength}/10\n"
            f"{message}"
        )

        notification = self.notify(
            title=title,
            content=content,
            notification_id=(
                f"fx_{symbol}_{timeframe}_{direction}"
            ),
        )

        vibration = None

        if vibration_ms is not None:
            vibration = self.vibrate(
                vibration_ms
            )

        sound = None

        if sound_file:
            sound = self.play_sound(
                sound_file
            )

        return {
            "notification": notification,
            "vibration": vibration,
            "sound": sound,
        }

    def test_notification(self):

        return self.notify(
            title="THE_FX.TRADER.BOT.ZW",
            content="Test alert — Android notification working",
            notification_id="fx_test",
        )

    def test_vibration(self):

        return self.vibrate(
            500
        )


if __name__ == "__main__":

    bridge = AndroidAlertBridge()

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 10G - Android Alert Bridge"
    )

    print(
        f"Termux:API available: "
        f"{bridge.available()}"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
