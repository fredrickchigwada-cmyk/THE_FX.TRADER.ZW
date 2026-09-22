from dataclasses import dataclass
from typing import Dict, List

from core.candle_engine import Candle
from core.signal_engine import SignalEngine


@dataclass
class TimeframeSignal:
    timeframe: str
    direction: str
    strength: int
    confirmations: int
    valid: bool


@dataclass
class MTFResult:
    symbol: str
    final_direction: str
    strength: int
    aligned_timeframes: int
    analyzed_timeframes: int
    agreement_ratio: float
    signals: Dict[str, TimeframeSignal]
    explanation: str


class MultiTimeframeEngine:
    """
    Multi-timeframe confirmation layer.

    SIGNAL-ONLY.
    No trade execution is implemented.
    """

    DEFAULT_TIMEFRAMES = [
        "M1",
        "M3",
        "M5",
        "M15",
        "M30",
        "H1",
        "H4",
    ]

    def __init__(
        self,
        signal_engine=None,
        timeframes=None,
    ):
        self.signal_engine = (
            signal_engine or SignalEngine()
        )

        self.timeframes = (
            timeframes
            or self.DEFAULT_TIMEFRAMES
        )

    def analyze(
        self,
        symbol: str,
        candles_by_timeframe: Dict[str, List[Candle]],
    ) -> MTFResult:

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty."
            )

        signals = {}

        for timeframe in self.timeframes:

            candles = candles_by_timeframe.get(
                timeframe,
                [],
            )

            signal = self.signal_engine.generate(
                symbol,
                timeframe,
                candles,
            )

            signals[timeframe] = TimeframeSignal(
                timeframe=timeframe,
                direction=signal.direction,
                strength=signal.strength,
                confirmations=signal.confirmations,
                valid=signal.valid,
            )

        valid_signals = [
            signal
            for signal in signals.values()
            if signal.valid
            and signal.direction in {
                "BUY",
                "SELL",
            }
        ]

        if not valid_signals:
            return MTFResult(
                symbol=symbol,
                final_direction="WAIT",
                strength=0,
                aligned_timeframes=0,
                analyzed_timeframes=len(
                    signals
                ),
                agreement_ratio=0.0,
                signals=signals,
                explanation=(
                    "No valid BUY/SELL "
                    "timeframe signals."
                ),
            )

        buy_count = sum(
            signal.direction == "BUY"
            for signal in valid_signals
        )

        sell_count = sum(
            signal.direction == "SELL"
            for signal in valid_signals
        )

        total = len(valid_signals)

        if buy_count == sell_count:
            return MTFResult(
                symbol=symbol,
                final_direction="WAIT",
                strength=0,
                aligned_timeframes=0,
                analyzed_timeframes=len(
                    signals
                ),
                agreement_ratio=0.0,
                signals=signals,
                explanation=(
                    "BUY and SELL timeframe "
                    "signals are conflicting."
                ),
            )

        if buy_count > sell_count:
            direction = "BUY"
            aligned = buy_count

        else:
            direction = "SELL"
            aligned = sell_count

        agreement_ratio = aligned / total

        # Require at least 60% agreement.
        if agreement_ratio < 0.60:
            return MTFResult(
                symbol=symbol,
                final_direction="WAIT",
                strength=0,
                aligned_timeframes=aligned,
                analyzed_timeframes=len(
                    signals
                ),
                agreement_ratio=agreement_ratio,
                signals=signals,
                explanation=(
                    "Insufficient multi-timeframe "
                    "agreement."
                ),
            )

        average_strength = sum(
            signal.strength
            for signal in valid_signals
            if signal.direction == direction
        ) / aligned

        strength = round(
            average_strength * agreement_ratio
        )

        strength = max(
            0,
            min(10, strength),
        )

        # Final MTF signal still requires
        # meaningful strength.
        if strength < 6:
            return MTFResult(
                symbol=symbol,
                final_direction="WAIT",
                strength=strength,
                aligned_timeframes=aligned,
                analyzed_timeframes=len(
                    signals
                ),
                agreement_ratio=agreement_ratio,
                signals=signals,
                explanation=(
                    "Multi-timeframe agreement "
                    "exists but strength is below "
                    "the required threshold."
                ),
            )

        return MTFResult(
            symbol=symbol,
            final_direction=direction,
            strength=strength,
            aligned_timeframes=aligned,
            analyzed_timeframes=len(
                signals
            ),
            agreement_ratio=agreement_ratio,
            signals=signals,
            explanation=(
                f"{aligned}/{total} valid timeframes "
                f"agree {direction}."
            ),
        )


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Multi-Timeframe Engine"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
