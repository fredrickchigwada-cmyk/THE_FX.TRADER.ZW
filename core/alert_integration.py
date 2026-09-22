from dataclasses import dataclass
from typing import Optional


@dataclass
class IntegrationResult:
    status: str
    reason: str
    signal: object = None
    protection: object = None
    dispatch: object = None


class AlertIntegration:
    """
    Stage 10J:
    Connects protected signals to the live Android alert dispatcher.

    Signal-only architecture:
    - No order placement
    - No trade modification
    - No trade closing
    """

    def __init__(self, signal_engine, dispatcher):
        self.signal_engine = signal_engine
        self.dispatcher = dispatcher

    def process(
        self,
        symbol,
        timeframe,
        candles,
        now=None,
    ):
        """
        Generate a protected signal and dispatch it only when valid.
        """

        result = self.signal_engine.evaluate(
            symbol=symbol,
            timeframe=timeframe,
            candles=candles,
            now=now,
        )

        if not isinstance(result, tuple) or len(result) != 3:
            return IntegrationResult(
                status="ERROR",
                reason="INVALID_SIGNAL_ENGINE_RESPONSE",
            )

        signal, protected, protection_status = result

        if signal is None:
            return IntegrationResult(
                status="WAIT",
                reason=protection_status,
                signal=None,
                protection=protected,
            )

        if getattr(signal, "direction", "WAIT") not in ("BUY", "SELL"):
            return IntegrationResult(
                status="WAIT",
                reason=protection_status,
                signal=signal,
                protection=protected,
            )

        if protected is None:
            return IntegrationResult(
                status="BLOCKED",
                reason=protection_status,
                signal=signal,
                protection=None,
            )

        dispatch_result = self.dispatcher.dispatch(
            signal,
            now=now,
        )

        if not isinstance(dispatch_result, dict):
            return IntegrationResult(
                status="ERROR",
                reason="INVALID_DISPATCHER_RESPONSE",
                signal=signal,
                protection=protected,
            )

        dispatch_status = dispatch_result.get("status")

        if dispatch_status == "DISPATCHED":
            return IntegrationResult(
                status="DISPATCHED",
                reason=dispatch_result.get(
                    "reason",
                    "ALERT_DISPATCHED",
                ),
                signal=signal,
                protection=protected,
                dispatch=dispatch_result,
            )

        return IntegrationResult(
            status="BLOCKED",
            reason=dispatch_result.get(
                "reason",
                "ALERT_BLOCKED",
            ),
            signal=signal,
            protection=protected,
            dispatch=dispatch_result,
        )

    def android_available(self):
        return self.dispatcher.android_available()

    def settings(self):
        return self.dispatcher.settings()

    def alert_history(self):
        return self.dispatcher.alert_history()

    def feedback_history(self):
        return self.dispatcher.feedback_history()

    def test_android(self):
        return self.dispatcher.test_android()


if __name__ == "__main__":
    print("THE_FX.TRADER.BOT.ZW")
    print("Stage 10J - End-to-End Alert Integration")
    print("Signal-only mode: ENABLED")
    print("Automatic trading: DISABLED")
