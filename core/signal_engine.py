from dataclasses import dataclass
from typing import Dict, List, Optional

from core.candle_engine import Candle
from core.technical_analysis import TechnicalAnalysis


@dataclass
class Signal:
    symbol: str
    timeframe: str
    direction: str
    strength: int
    confirmations: int
    entry: Optional[float]
    stop_loss: Optional[float]
    tp1: Optional[float]
    tp2: Optional[float]
    invalidation: Optional[float]
    explanation: str
    candle_confirmed: bool
    valid: bool


class SignalEngine:
    """
    Conservative signal-quality engine.

    SIGNAL-ONLY.
    No trade execution is implemented here.
    """

    MIN_CANDLES = 200
    MIN_CONFIRMATIONS = 4
    MIN_STRENGTH = 6

    SL_ATR = 1.5
    TP1_ATR = 1.5
    TP2_ATR = 3.0

    def __init__(self):
        self.last_signals: Dict[str, Signal] = {}

    @staticmethod
    def _wait(
        symbol: str,
        timeframe: str,
        reason: str,
        price: Optional[float] = None,
        confirmations: int = 0,
    ) -> Signal:

        return Signal(
            symbol=symbol,
            timeframe=timeframe,
            direction="WAIT",
            strength=0,
            confirmations=confirmations,
            entry=price,
            stop_loss=None,
            tp1=None,
            tp2=None,
            invalidation=None,
            explanation=reason,
            candle_confirmed=False,
            valid=False,
        )

    @staticmethod
    def _strength(points: int) -> int:
        """
        Convert confirmation points to a 1-10 scale.
        """
        if points <= 0:
            return 0

        return min(10, 4 + points)

    def generate(
        self,
        symbol: str,
        timeframe: str,
        candles: List[Candle],
    ) -> Signal:

        if not symbol:
            raise ValueError("Symbol cannot be empty.")

        if not timeframe:
            raise ValueError("Timeframe cannot be empty.")

        if len(candles) < self.MIN_CANDLES:
            return self._wait(
                symbol,
                timeframe,
                f"INSUFFICIENT_DATA: "
                f"{len(candles)}/{self.MIN_CANDLES} candles",
            )

        analysis = TechnicalAnalysis.analyze(candles)

        if not analysis.get("ready"):
            return self._wait(
                symbol,
                timeframe,
                analysis.get(
                    "reason",
                    "ANALYSIS_NOT_READY",
                ),
            )

        price = analysis.get("price")
        ema50 = analysis.get("ema50")
        ema200 = analysis.get("ema200")
        rsi = analysis.get("rsi")
        atr = analysis.get("atr")
        structure = analysis.get("structure")
        support = analysis.get("support")
        resistance = analysis.get("resistance")
        momentum = analysis.get("momentum")
        candle = analysis.get("candle_confirmation")

        values = [
            price,
            ema50,
            ema200,
            rsi,
            atr,
            support,
            resistance,
            momentum,
        ]

        if any(value is None for value in values):
            return self._wait(
                symbol,
                timeframe,
                "INCOMPLETE_INDICATOR_DATA",
                price,
            )

        if price <= 0 or atr <= 0:
            return self._wait(
                symbol,
                timeframe,
                "INVALID_MARKET_DATA",
                price,
            )

        buy = 0
        sell = 0

        buy_reasons = []
        sell_reasons = []

        # ==================================================
        # 1. PRIMARY TREND — EMA 50 / EMA 200
        # ==================================================

        bullish_trend = (
            price > ema50
            and ema50 > ema200
        )

        bearish_trend = (
            price < ema50
            and ema50 < ema200
        )

        if bullish_trend:
            buy += 2
            buy_reasons.append(
                "EMA trend bullish"
            )

        elif bearish_trend:
            sell += 2
            sell_reasons.append(
                "EMA trend bearish"
            )

        # ==================================================
        # 2. RSI
        # ==================================================

        # Healthy bullish zone.
        if 52 <= rsi < 70:
            buy += 1
            buy_reasons.append(
                "RSI bullish"
            )

        # Healthy bearish zone.
        elif 30 < rsi <= 48:
            sell += 1
            sell_reasons.append(
                "RSI bearish"
            )

        # Extreme zones do NOT automatically create signals.
        elif rsi >= 70:
            buy_reasons.append(
                "RSI overbought — BUY caution"
            )

        elif rsi <= 30:
            sell_reasons.append(
                "RSI oversold — SELL caution"
            )

        # ==================================================
        # 3. MARKET STRUCTURE
        # ==================================================

        if structure == "BULLISH":
            buy += 2
            buy_reasons.append(
                "market structure bullish"
            )

        elif structure == "BEARISH":
            sell += 2
            sell_reasons.append(
                "market structure bearish"
            )

        else:
            buy_reasons.append(
                "market structure not bullish"
            )
            sell_reasons.append(
                "market structure not bearish"
            )

        # ==================================================
        # 4. MOMENTUM
        # ==================================================

        if momentum > 0:
            buy += 1
            buy_reasons.append(
                "positive momentum"
            )

        elif momentum < 0:
            sell += 1
            sell_reasons.append(
                "negative momentum"
            )

        # ==================================================
        # 5. CLOSED-CANDLE CONFIRMATION
        # ==================================================

        bullish_candle = candle in {
            "BULLISH",
            "BULLISH_REVERSAL",
        }

        bearish_candle = candle in {
            "BEARISH",
            "BEARISH_REVERSAL",
        }

        if bullish_candle:
            buy += 1
            buy_reasons.append(
                "bullish candle confirmation"
            )

        elif bearish_candle:
            sell += 1
            sell_reasons.append(
                "bearish candle confirmation"
            )

        else:
            buy_reasons.append(
                "no bullish candle confirmation"
            )
            sell_reasons.append(
                "no bearish candle confirmation"
            )

        # ==================================================
        # 6. SUPPORT / RESISTANCE PROTECTION
        # ==================================================

        distance_support = price - support
        distance_resistance = resistance - price

        near_support = (
            distance_support >= 0
            and distance_support <= atr * 0.5
        )

        near_resistance = (
            distance_resistance >= 0
            and distance_resistance <= atr * 0.5
        )

        if near_resistance:
            buy = max(0, buy - 1)
            buy_reasons.append(
                "price near resistance"
            )

        if near_support:
            sell = max(0, sell - 1)
            sell_reasons.append(
                "price near support"
            )

        # ==================================================
        # 7. RANGE FILTER
        # ==================================================

        if structure == "RANGE":

            # A ranging market needs stronger confirmation.
            range_minimum = self.MIN_CONFIRMATIONS + 1

            if buy < range_minimum and sell < range_minimum:
                return self._wait(
                    symbol,
                    timeframe,
                    (
                        "RANGE_MARKET: "
                        f"BUY={buy}, SELL={sell}; "
                        "stronger confirmation required"
                    ),
                    price,
                    max(buy, sell),
                )

        # ==================================================
        # 8. CONFLICT PROTECTION
        # ==================================================

        if buy == sell:
            return self._wait(
                symbol,
                timeframe,
                (
                    "CONFLICTING_SIGNALS: "
                    f"BUY={buy}, SELL={sell}"
                ),
                price,
                max(buy, sell),
            )

        # ==================================================
        # 9. BUY
        # ==================================================

        if (
            buy >= self.MIN_CONFIRMATIONS
            and buy > sell
        ):

            strength = self._strength(buy)

            if strength < self.MIN_STRENGTH:
                return self._wait(
                    symbol,
                    timeframe,
                    (
                        "BUY_BELOW_STRENGTH_THRESHOLD: "
                        f"{strength}/10"
                    ),
                    price,
                    buy,
                )

            stop_loss = price - (
                atr * self.SL_ATR
            )

            tp1 = price + (
                atr * self.TP1_ATR
            )

            tp2 = price + (
                atr * self.TP2_ATR
            )

            signal = Signal(
                symbol=symbol,
                timeframe=timeframe,
                direction="BUY",
                strength=strength,
                confirmations=buy,
                entry=price,
                stop_loss=stop_loss,
                tp1=tp1,
                tp2=tp2,
                invalidation=stop_loss,
                explanation="; ".join(
                    buy_reasons
                ),
                candle_confirmed=bullish_candle,
                valid=True,
            )

            self.last_signals[
                f"{symbol}:{timeframe}"
            ] = signal

            return signal

        # ==================================================
        # 10. SELL
        # ==================================================

        if (
            sell >= self.MIN_CONFIRMATIONS
            and sell > buy
        ):

            strength = self._strength(sell)

            if strength < self.MIN_STRENGTH:
                return self._wait(
                    symbol,
                    timeframe,
                    (
                        "SELL_BELOW_STRENGTH_THRESHOLD: "
                        f"{strength}/10"
                    ),
                    price,
                    sell,
                )

            stop_loss = price + (
                atr * self.SL_ATR
            )

            tp1 = price - (
                atr * self.TP1_ATR
            )

            tp2 = price - (
                atr * self.TP2_ATR
            )

            signal = Signal(
                symbol=symbol,
                timeframe=timeframe,
                direction="SELL",
                strength=strength,
                confirmations=sell,
                entry=price,
                stop_loss=stop_loss,
                tp1=tp1,
                tp2=tp2,
                invalidation=stop_loss,
                explanation="; ".join(
                    sell_reasons
                ),
                candle_confirmed=bearish_candle,
                valid=True,
            )

            self.last_signals[
                f"{symbol}:{timeframe}"
            ] = signal

            return signal

        # ==================================================
        # 11. DEFAULT WAIT
        # ==================================================

        return self._wait(
            symbol,
            timeframe,
            (
                "INSUFFICIENT_CONFIRMATION: "
                f"BUY={buy}, SELL={sell}"
            ),
            price,
            max(buy, sell),
        )


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Signal Quality Engine"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
