"""
Stage 18I — Full Multi-Market Runtime

THE_FX.TRADER.BOT.ZW

Multi-market discovery and monitoring controller.

Important:
- Deriv is the market-data source.
- XAUUSD remains the primary market.
- Signal-only.
- No trade execution.
- Unavailable/closed/stale markets never generate BUY/SELL.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

from core.market_discovery import MarketDiscovery


PRIMARY_MARKET = "XAUUSD"

REQUESTED_MARKETS = [
    "BTCUSD",
    "XAUUSD",
    "STEP INDEX",
    "VOLATILITY 75",
    "VOLATILITY 10",
    "VOLATILITY 25",
    "VOLATILITY 50",
    "VOLATILITY 100",
    "BOOM 500",
    "BOOM 1000",
    "CRASH 500",
    "CRASH 1000",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "NAS100",
    "US30",
]


@dataclass
class MarketRuntimeState:
    requested_name: str
    symbol: Optional[str] = None
    status: str = "CHECKING"
    available: bool = False
    trading_suspended: Optional[bool] = None
    exchange_is_open: Optional[bool] = None
    last_price: Optional[float] = None
    last_epoch: Optional[float] = None
    ticks: int = 0
    error: str = ""

    @property
    def stale(self) -> bool:
        if self.last_epoch is None:
            return True
        return (time.time() - self.last_epoch) > 10.0

    def snapshot(self) -> dict:
        return {
            "market": self.requested_name,
            "symbol": self.symbol,
            "status": self.status,
            "available": self.available,
            "trading_suspended": self.trading_suspended,
            "exchange_is_open": self.exchange_is_open,
            "last_price": self.last_price,
            "last_epoch": self.last_epoch,
            "ticks": self.ticks,
            "stale": self.stale,
            "error": self.error,
        }


class MultiMarketRuntime:
    """
    Safe multi-market controller.

    This class deliberately contains no trade execution methods.
    """

    PRIMARY_MARKET = PRIMARY_MARKET
    SIGNAL_ONLY = True

    def __init__(self, discovery=None):
        self.discovery = discovery or MarketDiscovery()

        self.requested_markets = list(REQUESTED_MARKETS)

        self.markets: Dict[str, MarketRuntimeState] = {
            name: MarketRuntimeState(requested_name=name)
            for name in self.requested_markets
        }

        self.last_refresh = 0.0

    # --------------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------------

    def refresh(self, response=None) -> List[MarketRuntimeState]:
        """
        Refresh discovered market information.

        If a Deriv active-symbol response is supplied, it is passed
        through the existing MarketDiscovery implementation.
        """

        if response is not None:
            self.discovery.process_response(response)

        now = time.time()
        self.last_refresh = now

        for name in self.requested_markets:
            discovered = self.discovery.get(name)

            state = self.markets[name]

            if discovered is None:
                state.symbol = None
                state.available = False
                state.status = "CHECKING"
                continue

            state.symbol = getattr(discovered, "symbol", None)
            state.available = bool(
                getattr(discovered, "available", False)
            )

            state.trading_suspended = getattr(
                discovered,
                "trading_suspended",
                None,
            )

            state.exchange_is_open = getattr(
                discovered,
                "exchange_is_open",
                None,
            )

            try:
                state.status = self.discovery.status(name)
            except Exception:
                state.status = (
                    "ACTIVE" if state.available else "UNAVAILABLE"
                )

        return list(self.markets.values())

    # --------------------------------------------------------
    # MARKET LOOKUP
    # --------------------------------------------------------

    def get(self, market: str) -> Optional[MarketRuntimeState]:
        return self.markets.get(market)

    def symbol(self, market: str) -> Optional[str]:
        state = self.get(market)

        if state is None:
            return None

        return state.symbol

    def is_available(self, market: str) -> bool:
        state = self.get(market)

        return bool(
            state
            and state.available
            and state.status not in ("CLOSED", "UNAVAILABLE")
        )

    def status(self, market: str) -> str:
        state = self.get(market)

        if state is None:
            return "CHECKING"

        return state.status

    # --------------------------------------------------------
    # TICK UPDATE
    # --------------------------------------------------------

    def update_tick(
        self,
        market: str,
        price: float,
        epoch: Optional[float] = None,
    ) -> bool:
        state = self.get(market)

        if state is None:
            return False

        if not state.available:
            return False

        if state.status == "CLOSED":
            return False

        try:
            value = float(price)
        except (TypeError, ValueError):
            return False

        if value <= 0:
            return False

        state.last_price = value
        state.last_epoch = (
            float(epoch)
            if epoch is not None
            else time.time()
        )
        state.ticks += 1

        return True

    # --------------------------------------------------------
    # DATA QUALITY
    # --------------------------------------------------------

    def data_ready(self, market: str) -> bool:
        state = self.get(market)

        if state is None:
            return False

        if not state.available:
            return False

        if state.status in ("CLOSED", "UNAVAILABLE"):
            return False

        if state.last_price is None:
            return False

        if state.last_epoch is None:
            return False

        if state.stale:
            return False

        return True

    # --------------------------------------------------------
    # SAFE SIGNAL GATE
    # --------------------------------------------------------

    def signal_allowed(self, market: str) -> bool:
        """
        Final safety gate before analysis is allowed.

        This does NOT create a signal.
        It only determines whether enough market data exists
        to permit downstream analysis.
        """

        return self.data_ready(market)

    # --------------------------------------------------------
    # SNAPSHOT
    # --------------------------------------------------------

    def snapshot(self) -> dict:
        return {
            "primary_market": self.PRIMARY_MARKET,
            "signal_only": True,
            "trade_execution": False,
            "market_count": len(self.requested_markets),
            "markets": {
                name: state.snapshot()
                for name, state in self.markets.items()
            },
        }

    def available_markets(self) -> List[str]:
        return [
            name
            for name, state in self.markets.items()
            if state.available
            and state.status not in ("CLOSED", "UNAVAILABLE")
        ]

    def unavailable_markets(self) -> List[str]:
        return [
            name
            for name, state in self.markets.items()
            if not state.available
            or state.status == "UNAVAILABLE"
        ]

    def closed_markets(self) -> List[str]:
        return [
            name
            for name, state in self.markets.items()
            if state.status == "CLOSED"
        ]
