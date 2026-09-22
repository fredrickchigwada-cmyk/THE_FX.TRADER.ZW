import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Candle:
    symbol: str
    timeframe: str
    start: int
    end: int
    open: float
    high: float
    low: float
    close: float
    volume: int = 0

    @property
    def bullish(self) -> bool:
        return self.close > self.open

    @property
    def bearish(self) -> bool:
        return self.close < self.open

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def range(self) -> float:
        return self.high - self.low


class CandleEngine:
    """
    Builds OHLC candles locally from Deriv ticks.

    SIGNAL-ONLY:
    This engine performs market-data processing only.
    It cannot place, modify, or close trades.
    """

    TIMEFRAMES = {
        "M1": 60,
        "M3": 180,
        "M5": 300,
        "M15": 900,
        "M30": 1800,
        "H1": 3600,
        "H2": 7200,
        "H4": 14400,
        "H6": 21600,
        "H8": 28800,
        "H12": 43200,
        "D1": 86400,
        "W1": 604800,
        "MN1": 2592000,
    }

    def __init__(self, max_history: int = 500):
        self.max_history = max_history

        # symbol -> timeframe -> list[Candle]
        self.history: Dict[str, Dict[str, List[Candle]]] = {}

        # symbol -> timeframe -> current unfinished candle
        self.current: Dict[str, Dict[str, Candle]] = {}

    @classmethod
    def timeframe_seconds(cls, timeframe: str) -> int:
        if timeframe not in cls.TIMEFRAMES:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}"
            )

        return cls.TIMEFRAMES[timeframe]

    @classmethod
    def candle_start(
        cls,
        epoch: float,
        timeframe: str,
    ) -> int:
        seconds = cls.timeframe_seconds(timeframe)

        # For MN1, use calendar month boundaries rather
        # than a fixed 30-day approximation.
        if timeframe == "MN1":
            value = time.gmtime(epoch)
            return int(
                time.mktime(
                    (
                        value.tm_year,
                        value.tm_mon,
                        1,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -1,
                    )
                )
            )

        return int(epoch // seconds) * seconds

    def _ensure_symbol(self, symbol: str):
        if symbol not in self.history:
            self.history[symbol] = {}

        if symbol not in self.current:
            self.current[symbol] = {}

        for timeframe in self.TIMEFRAMES:
            self.history[symbol].setdefault(
                timeframe,
                [],
            )

    def update_tick(
        self,
        symbol: str,
        price: float,
        epoch: Optional[float] = None,
    ) -> List[Candle]:
        """
        Add a tick and return any candles that were completed.
        """

        if not symbol:
            raise ValueError("Symbol cannot be empty.")

        if price <= 0:
            raise ValueError("Price must be positive.")

        if epoch is None:
            epoch = time.time()

        self._ensure_symbol(symbol)

        completed = []

        for timeframe in self.TIMEFRAMES:
            start = self.candle_start(
                epoch,
                timeframe,
            )

            seconds = self.timeframe_seconds(timeframe)
            end = start + seconds

            current = self.current[symbol].get(timeframe)

            if current is None:
                self.current[symbol][timeframe] = Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    start=start,
                    end=end,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1,
                )
                continue

            # New candle period.
            if start > current.start:

                completed_candle = current

                self.history[symbol][timeframe].append(
                    completed_candle
                )

                if len(
                    self.history[symbol][timeframe]
                ) > self.max_history:
                    self.history[symbol][timeframe] = (
                        self.history[symbol][timeframe]
                        [-self.max_history:]
                    )

                completed.append(completed_candle)

                self.current[symbol][timeframe] = Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    start=start,
                    end=end,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1,
                )

                continue

            # Same candle period.
            if start == current.start:
                current.high = max(
                    current.high,
                    price,
                )

                current.low = min(
                    current.low,
                    price,
                )

                current.close = price
                current.volume += 1

        return completed

    def get_current(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[Candle]:
        self._ensure_symbol(symbol)

        return self.current[symbol].get(timeframe)

    def get_history(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
    ) -> List[Candle]:

        self._ensure_symbol(symbol)

        candles = self.history[symbol][timeframe]

        if count is None:
            return list(candles)

        if count <= 0:
            return []

        return list(candles[-count:])

    def candle_count(
        self,
        symbol: str,
        timeframe: str,
    ) -> int:
        return len(
            self.get_history(
                symbol,
                timeframe,
            )
        )

    def clear(self):
        self.history.clear()
        self.current.clear()


if __name__ == "__main__":
    engine = CandleEngine()

    base = 1000

    prices = [
        100.0,
        101.0,
        99.0,
        102.0,
    ]

    for index, price in enumerate(prices):
        engine.update_tick(
            "TEST",
            price,
            base + index,
        )

    candle = engine.get_current(
        "TEST",
        "M1",
    )

    print("Candle engine test")
    print("------------------")
    print(f"Open : {candle.open}")
    print(f"High : {candle.high}")
    print(f"Low  : {candle.low}")
    print(f"Close: {candle.close}")
    print(f"Volume: {candle.volume}")
