from dataclasses import dataclass
from typing import Optional

from core.signal_engine import Signal


@dataclass
class RoutedAlert:
    signal: Signal
    alert: object = None
    feedback: object = None
    status: str = "BLOCKED"
    reason: str = ""


class SignalAlertRouter:
    def __init__(self, config, manager, feedback):
        self.config = config
        self.manager = manager
        self.feedback = feedback
        self._alert_history = []

    def sync_config(self):
        return self.config

    def _normalize_market(self, symbol: str) -> str:
        """Convert Deriv/API symbols to configured display market names."""
        if not symbol:
            return ""

        value = str(symbol).strip().upper()

        aliases = {
            "FRXXAUUSD": "XAUUSD",
            "XAUUSD": "XAUUSD",
            "GOLD": "XAUUSD",
            "GOLDUSD": "XAUUSD",
            "GOLD/USD": "XAUUSD",

            "R_10": "VOLATILITY 10",
            "R_25": "VOLATILITY 25",
            "R_50": "VOLATILITY 50",
            "R_75": "VOLATILITY 75",
            "R_100": "VOLATILITY 100",

            "STPRNG": "STEP INDEX",
            "STEP INDEX": "STEP INDEX",

            "BOOM500": "BOOM 500",
            "BOOM1000": "BOOM 1000",

            "CRASH500": "CRASH 500",
            "CRASH1000": "CRASH 1000",

            "FRXEURUSD": "EURUSD",
            "FRXGBPUSD": "GBPUSD",
            "FRXUSDJPY": "USDJPY",
            "FRXBTCUSD": "BTCUSD",

            "NAS100": "NAS100",
            "US30": "US30",
        }

        return aliases.get(value, value)

    def _market_enabled(self, symbol: str) -> bool:
        configured = {
            self._normalize_market(item)
            for item in self.config.selected_markets
        }

        market = self._normalize_market(symbol)
        return market in configured

    def _timeframe_enabled(self, timeframe: str) -> bool:
        return str(timeframe).upper() in {
            str(item).upper()
            for item in self.config.selected_timeframes
        }

    def route(
        self,
        signal: Signal,
        now: Optional[float] = None,
    ) -> RoutedAlert:

        self.sync_config()

        if not signal.valid:
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="INVALID_SIGNAL",
            )

        direction = str(signal.direction).upper()

        if direction not in ("BUY", "SELL"):
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="INVALID_DIRECTION",
            )

        if not self.config.alerts_enabled:
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="ALERTS_DISABLED",
            )

        if not self._market_enabled(signal.symbol):
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="MARKET_DISABLED",
            )

        if not self._timeframe_enabled(signal.timeframe):
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="TIMEFRAME_DISABLED",
            )

        if direction == "BUY" and not self.config.buy_enabled:
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="DIRECTION_DISABLED",
            )

        if direction == "SELL" and not self.config.sell_enabled:
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="DIRECTION_DISABLED",
            )

        if float(signal.strength) < float(self.config.minimum_strength):
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="STRENGTH_TOO_LOW",
            )

        try:
            alert = self.manager.create_alert(
                symbol=signal.symbol,
                timeframe=signal.timeframe,
                direction=signal.direction,
                strength=int(signal.strength),
                message=signal.explanation,
                now=now,
            )
        except TypeError:
            alert = self.manager.create_alert(
                signal.symbol,
                signal.timeframe,
                signal.direction,
                int(signal.strength),
                signal.explanation,
                now=now,
            )

        if alert is None:
            # AlertManager returns None when its cooldown/duplicate
            # protection blocks another alert.
            return RoutedAlert(
                signal=signal,
                status="BLOCKED",
                reason="ALERT_COOLDOWN",
            )

        feedback = None

        try:
            feedback = self.feedback.record_alert(alert)
        except AttributeError:
            try:
                feedback = self.feedback.record(alert)
            except AttributeError:
                feedback = None

        self._alert_history.append(alert)

        return RoutedAlert(
            signal=signal,
            alert=alert,
            feedback=feedback,
            status="ROUTED",
            reason="ALERT_ROUTED",
        )

    def alert_history(self):
        """Return successfully routed alert events."""
        return list(getattr(self, "_alert_history", []))

    def feedback_history(self):
        """Return recorded feedback events."""
        if hasattr(self.feedback, "all_events"):
            return self.feedback.all_events()

        if hasattr(self.feedback, "events"):
            events = self.feedback.events
            return list(events)

        return []

    def settings(self):
        """Return complete router configuration."""
        config = (
            self.config.settings()
            if hasattr(self.config, "settings")
            else dict(getattr(self.config, "__dict__", {}))
        )

        manager = (
            self.manager.settings()
            if hasattr(self.manager, "settings")
            else dict(getattr(self.manager, "__dict__", {}))
        )

        feedback = (
            self.feedback.settings()
            if hasattr(self.feedback, "settings")
            else dict(getattr(self.feedback, "__dict__", {}))
        )

        return {
            "config": config,
            "manager": manager,
            "feedback": feedback,
        }

    def test_alert(self, direction="BUY", now=None):
        """Create a test alert and return (alert, feedback)."""
        direction = str(direction).upper()

        alert = self.manager.create_alert(
            symbol="XAUUSD",
            timeframe="M1",
            direction=direction,
            strength=10,
            message=f"THE_FX.TRADER.BOT.ZW TEST {direction} ALERT",
            now=now,
            alert_type="TEST",
        )

        if alert is None:
            return None, None

        try:
            feedback = self.feedback.record_alert(alert)
        except AttributeError:
            feedback = self.feedback.record(alert)

        return alert, feedback

