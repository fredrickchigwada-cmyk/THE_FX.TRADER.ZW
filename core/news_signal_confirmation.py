"""
THE_FX.TRADER.BOT.ZW
Stage 18E — News / Signal Confirmation

News is a confirmation and risk layer.
It cannot execute trades.
It cannot create a directional signal from news alone.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class NewsConfirmationResult:
    original_signal: str
    final_signal: str
    technical_strength: int
    news_risk: str
    news_bias: str
    news_confirmed: bool
    conflict: bool
    reason: str

    def to_dict(self):
        return {
            "original_signal": self.original_signal,
            "final_signal": self.final_signal,
            "technical_strength": self.technical_strength,
            "news_risk": self.news_risk,
            "news_bias": self.news_bias,
            "news_confirmed": self.news_confirmed,
            "conflict": self.conflict,
            "reason": self.reason,
        }


class NewsSignalConfirmation:
    """
    Combines an existing technical signal with news context.

    Rules:
    - WAIT technical signal remains WAIT.
    - News alone can never create BUY or SELL.
    - Matching news may confirm an existing direction.
    - Conflicting HIGH-impact news forces WAIT.
    - Conflicting MEDIUM-impact news also forces WAIT when
      the technical signal is weak.
    - LOW-impact news does not override technical analysis.
    """

    VALID_SIGNALS = {"BUY", "SELL", "WAIT"}
    VALID_BIASES = {"BULLISH", "BEARISH", "NEUTRAL"}
    VALID_RISKS = {"LOW", "MEDIUM", "HIGH"}

    def evaluate(
        self,
        signal: str,
        strength: int = 0,
        news_risk: str = "LOW",
        news_bias: str = "NEUTRAL",
    ) -> NewsConfirmationResult:

        signal = str(signal).upper()
        news_risk = str(news_risk).upper()
        news_bias = str(news_bias).upper()

        if signal not in self.VALID_SIGNALS:
            return NewsConfirmationResult(
                original_signal=signal,
                final_signal="WAIT",
                technical_strength=int(strength),
                news_risk=news_risk,
                news_bias=news_bias,
                news_confirmed=False,
                conflict=False,
                reason="INVALID_TECHNICAL_SIGNAL",
            )

        if news_risk not in self.VALID_RISKS:
            news_risk = "LOW"

        if news_bias not in self.VALID_BIASES:
            news_bias = "NEUTRAL"

        strength = max(0, min(10, int(strength)))

        # News cannot create a signal.
        if signal == "WAIT":
            return NewsConfirmationResult(
                original_signal=signal,
                final_signal="WAIT",
                technical_strength=strength,
                news_risk=news_risk,
                news_bias=news_bias,
                news_confirmed=False,
                conflict=False,
                reason="TECHNICAL_SIGNAL_WAIT",
            )

        # No directional news = no confirmation.
        if news_bias == "NEUTRAL":
            return NewsConfirmationResult(
                original_signal=signal,
                final_signal=signal,
                technical_strength=strength,
                news_risk=news_risk,
                news_bias=news_bias,
                news_confirmed=False,
                conflict=False,
                reason="NEWS_NEUTRAL_TECHNICAL_SIGNAL_RETAINED",
            )

        bullish_conflict = (
            signal == "SELL"
            and news_bias == "BULLISH"
        )

        bearish_conflict = (
            signal == "BUY"
            and news_bias == "BEARISH"
        )

        conflict = bullish_conflict or bearish_conflict

        # HIGH-impact conflicting news always forces WAIT.
        if conflict and news_risk == "HIGH":
            return NewsConfirmationResult(
                original_signal=signal,
                final_signal="WAIT",
                technical_strength=strength,
                news_risk=news_risk,
                news_bias=news_bias,
                news_confirmed=False,
                conflict=True,
                reason="HIGH_IMPACT_NEWS_CONFLICT",
            )

        # Medium-impact conflict forces WAIT for weaker signals.
        if conflict and news_risk == "MEDIUM" and strength < 8:
            return NewsConfirmationResult(
                original_signal=signal,
                final_signal="WAIT",
                technical_strength=strength,
                news_risk=news_risk,
                news_bias=news_bias,
                news_confirmed=False,
                conflict=True,
                reason="MEDIUM_IMPACT_NEWS_CONFLICT",
            )

        # Low-impact conflict does not override the technical signal.
        if conflict:
            return NewsConfirmationResult(
                original_signal=signal,
                final_signal=signal,
                technical_strength=strength,
                news_risk=news_risk,
                news_bias=news_bias,
                news_confirmed=False,
                conflict=True,
                reason="LOW_RISK_NEWS_CONFLICT_TECHNICAL_RETAINED",
            )

        # Matching news confirms the existing technical direction.
        matching = (
            (signal == "BUY" and news_bias == "BULLISH")
            or
            (signal == "SELL" and news_bias == "BEARISH")
        )

        if matching:
            return NewsConfirmationResult(
                original_signal=signal,
                final_signal=signal,
                technical_strength=strength,
                news_risk=news_risk,
                news_bias=news_bias,
                news_confirmed=True,
                conflict=False,
                reason="NEWS_CONFIRMS_TECHNICAL_SIGNAL",
            )

        return NewsConfirmationResult(
            original_signal=signal,
            final_signal=signal,
            technical_strength=strength,
            news_risk=news_risk,
            news_bias=news_bias,
            news_confirmed=False,
            conflict=False,
            reason="NEWS_NO_DIRECTIONAL_CONFIRMATION",
        )

    def evaluate_news_only(
        self,
        news_risk: str,
        news_bias: str,
    ) -> NewsConfirmationResult:
        """
        Explicitly proves that news alone cannot create BUY/SELL.
        """
        return self.evaluate(
            signal="WAIT",
            strength=0,
            news_risk=news_risk,
            news_bias=news_bias,
        )

    def no_trade_methods(self):
        return False
