from typing import Optional

from core.alert_config import AlertConfig
from core.alert_feedback import AlertFeedback
from core.alert_manager import AlertManager
from core.alert_persistence import AlertPersistence
from core.signal_alert_router import SignalAlertRouter


class PersistentAlertRouter:
    """
    Persistent alert system.

    Loads alert settings at startup and saves them when changed.

    Signal-only:
    This component has no trading/execution functionality.
    """

    def __init__(
        self,
        persistence: Optional[AlertPersistence] = None,
    ):

        self.persistence = (
            persistence
            or AlertPersistence()
        )

        self.config = (
            self.persistence.load()
        )

        self.manager = AlertManager()

        self.feedback = AlertFeedback()

        self.router = SignalAlertRouter(
            config=self.config,
            manager=self.manager,
            feedback=self.feedback,
        )

        self.router.sync_config()

    # =================================================
    # SETTINGS
    # =================================================

    def get_config(self):
        return self.config

    def save(self) -> bool:
        self.router.sync_config()
        return self.persistence.save(
            self.config
        )

    def reload(self):

        self.config = (
            self.persistence.load()
        )

        self.router.config = (
            self.config
        )

        self.router.sync_config()

        return self.config

    def reset(self):

        self.config = AlertConfig()

        self.router.config = (
            self.config
        )

        self.router.sync_config()

        return self.save()

    # =================================================
    # UPDATE SETTINGS
    # =================================================

    def set_alerts_enabled(
        self,
        enabled: bool,
    ):

        self.config.alerts_enabled = bool(
            enabled
        )

        return self.save()

    def set_buy_enabled(
        self,
        enabled: bool,
    ):

        self.config.buy_enabled = bool(
            enabled
        )

        return self.save()

    def set_sell_enabled(
        self,
        enabled: bool,
    ):

        self.config.sell_enabled = bool(
            enabled
        )

        return self.save()

    def set_wait_enabled(
        self,
        enabled: bool,
    ):

        self.config.wait_enabled = bool(
            enabled
        )

        return self.save()

    def set_sound_enabled(
        self,
        enabled: bool,
    ):

        self.config.sound_enabled = bool(
            enabled
        )

        return self.save()

    def set_vibration_enabled(
        self,
        enabled: bool,
    ):

        self.config.vibration_enabled = bool(
            enabled
        )

        return self.save()

    def set_minimum_strength(
        self,
        strength: int,
    ):

        self.config.set_minimum_strength(
            strength
        )

        return self.save()

    def set_cooldown(
        self,
        seconds: float,
    ):

        self.config.set_cooldown(
            seconds
        )

        return self.save()

    def add_market(
        self,
        market: str,
    ):

        self.config.add_market(
            market
        )

        return self.save()

    def remove_market(
        self,
        market: str,
    ):

        self.config.remove_market(
            market
        )

        return self.save()

    def add_timeframe(
        self,
        timeframe: str,
    ):

        self.config.add_timeframe(
            timeframe
        )

        return self.save()

    def remove_timeframe(
        self,
        timeframe: str,
    ):

        self.config.remove_timeframe(
            timeframe
        )

        return self.save()

    # =================================================
    # SIGNAL ROUTING
    # =================================================

    def route(
        self,
        signal,
        now=None,
    ):

        return self.router.route(
            signal,
            now=now,
        )

    # =================================================
    # TEST ALERT
    # =================================================

    def test_alert(
        self,
        direction="BUY",
        now=None,
    ):

        return self.router.test_alert(
            direction=direction,
            now=now,
        )

    # =================================================
    # INFORMATION
    # =================================================

    def settings(self):

        return self.router.settings()

    def alert_history(self):

        return self.router.alert_history()

    def feedback_history(self):

        return self.router.feedback_history()

    def latest_alert(self):

        return self.router.latest_alert()

    def settings_path(self):

        return self.persistence.path()


if __name__ == "__main__":

    system = PersistentAlertRouter()

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 10F - Persistent Alert Router"
    )

    print(
        "Settings loaded: YES"
    )

    print(
        f"Settings file: {system.settings_path()}"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
