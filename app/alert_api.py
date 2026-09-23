from alerts.alert_engine import AlertEngine
from alerts.alert_settings import AlertSettings


class AlertAPI:
    """Read-only alert state interface for the Android UI."""

    def __init__(self):
        self.settings = AlertSettings()

        self.engine = AlertEngine(
            enabled=self.settings.alerts_enabled,
            sound_enabled=self.settings.sound_enabled,
            vibration_enabled=self.settings.vibration_enabled,
        )

    def settings_snapshot(self):
        return self.settings.to_dict()

    def alerts(self):
        return [
            alert.to_dict()
            for alert in self.engine.all()
        ]

    def snapshot(self):
        return {
            "settings": self.settings_snapshot(),
            "count": self.engine.count(),
            "alerts": self.alerts(),
        }
