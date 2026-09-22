from typing import Dict, List, Optional

from core.candle_engine import Candle


class TechnicalAnalysis:
    """
    Technical-analysis calculations for
    THE_FX.TRADER.BOT.ZW.

    SIGNAL-ONLY:
    This module calculates market conditions only.
    It cannot place, modify, or close trades.
    """

    @staticmethod
    def closes(candles: List[Candle]) -> List[float]:
        return [float(c.close) for c in candles]

    @staticmethod
    def ema(
        values: List[float],
        period: int,
    ) -> Optional[float]:

        if period <= 0:
            raise ValueError("EMA period must be positive.")

        if len(values) < period:
            return None

        multiplier = 2.0 / (period + 1)

        result = sum(values[:period]) / period

        for value in values[period:]:
            result = (
                (value - result) * multiplier
                + result
            )

        return result

    @staticmethod
    def rsi(
        values: List[float],
        period: int = 14,
    ) -> Optional[float]:

        if period <= 0:
            raise ValueError("RSI period must be positive.")

        if len(values) < period + 1:
            return None

        gains = []
        losses = []

        for i in range(1, period + 1):
            change = values[i] - values[i - 1]

            if change > 0:
                gains.append(change)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(change))

        average_gain = sum(gains) / period
        average_loss = sum(losses) / period

        for i in range(period + 1, len(values)):
            change = values[i] - values[i - 1]

            gain = max(change, 0.0)
            loss = max(-change, 0.0)

            average_gain = (
                (average_gain * (period - 1))
                + gain
            ) / period

            average_loss = (
                (average_loss * (period - 1))
                + loss
            ) / period

        if average_loss == 0:
            return 100.0

        relative_strength = (
            average_gain / average_loss
        )

        return 100.0 - (
            100.0 / (1.0 + relative_strength)
        )

    @staticmethod
    def true_ranges(
        candles: List[Candle],
    ) -> List[float]:

        if not candles:
            return []

        ranges = []

        previous_close = None

        for candle in candles:

            high = float(candle.high)
            low = float(candle.low)
            close = float(candle.close)

            if previous_close is None:
                true_range = high - low

            else:
                true_range = max(
                    high - low,
                    abs(high - previous_close),
                    abs(low - previous_close),
                )

            ranges.append(true_range)
            previous_close = close

        return ranges

    @classmethod
    def atr(
        cls,
        candles: List[Candle],
        period: int = 14,
    ) -> Optional[float]:

        if period <= 0:
            raise ValueError("ATR period must be positive.")

        ranges = cls.true_ranges(candles)

        if len(ranges) < period:
            return None

        return sum(
            ranges[-period:]
        ) / period

    @staticmethod
    def market_structure(
        candles: List[Candle],
        lookback: int = 5,
    ) -> str:

        if lookback <= 0:
            raise ValueError(
                "Lookback must be positive."
            )

        if len(candles) < lookback + 1:
            return "INSUFFICIENT_DATA"

        recent = candles[-(lookback + 1):]

        highs = [c.high for c in recent]
        lows = [c.low for c in recent]

        higher_highs = all(
            highs[i] >= highs[i - 1]
            for i in range(1, len(highs))
        )

        higher_lows = all(
            lows[i] >= lows[i - 1]
            for i in range(1, len(lows))
        )

        lower_highs = all(
            highs[i] <= highs[i - 1]
            for i in range(1, len(highs))
        )

        lower_lows = all(
            lows[i] <= lows[i - 1]
            for i in range(1, len(lows))
        )

        if higher_highs and higher_lows:
            return "BULLISH"

        if lower_highs and lower_lows:
            return "BEARISH"

        return "RANGE"

    @staticmethod
    def support_resistance(
        candles: List[Candle],
        lookback: int = 20,
    ) -> Dict[str, Optional[float]]:

        if not candles:
            return {
                "support": None,
                "resistance": None,
            }

        recent = candles[-lookback:]

        support = min(
            candle.low
            for candle in recent
        )

        resistance = max(
            candle.high
            for candle in recent
        )

        return {
            "support": float(support),
            "resistance": float(resistance),
        }

    @staticmethod
    def momentum(
        values: List[float],
        period: int = 5,
    ) -> Optional[float]:

        if period <= 0:
            raise ValueError(
                "Momentum period must be positive."
            )

        if len(values) <= period:
            return None

        previous = values[-period - 1]
        current = values[-1]

        if previous == 0:
            return None

        return (
            (current - previous)
            / previous
        ) * 100.0

    @staticmethod
    def candle_confirmation(
        candles: List[Candle],
    ) -> str:

        if len(candles) < 2:
            return "INSUFFICIENT_DATA"

        previous = candles[-2]
        current = candles[-1]

        if current.bullish and previous.bearish:
            if current.close > previous.open:
                return "BULLISH_REVERSAL"

        if current.bearish and previous.bullish:
            if current.close < previous.open:
                return "BEARISH_REVERSAL"

        if current.bullish:
            return "BULLISH"

        if current.bearish:
            return "BEARISH"

        return "NEUTRAL"

    @classmethod
    def analyze(
        cls,
        candles: List[Candle],
    ) -> Dict:

        if not candles:
            return {
                "ready": False,
                "reason": "NO_DATA",
            }

        values = cls.closes(candles)

        ema50 = cls.ema(
            values,
            50,
        )

        ema200 = cls.ema(
            values,
            200,
        )

        rsi = cls.rsi(
            values,
            14,
        )

        atr = cls.atr(
            candles,
            14,
        )

        structure = cls.market_structure(
            candles,
        )

        levels = cls.support_resistance(
            candles,
        )

        momentum = cls.momentum(
            values,
        )

        confirmation = cls.candle_confirmation(
            candles,
        )

        return {
            "ready": True,
            "price": values[-1],
            "ema50": ema50,
            "ema200": ema200,
            "rsi": rsi,
            "atr": atr,
            "structure": structure,
            "support": levels["support"],
            "resistance": levels["resistance"],
            "momentum": momentum,
            "candle_confirmation": confirmation,
        }
