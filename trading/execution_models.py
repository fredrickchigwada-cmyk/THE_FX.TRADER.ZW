from dataclasses import dataclass
from typing import Literal, Optional


Side = Literal["BUY", "SELL"]


@dataclass
class TradeRequest:
    symbol: str
    side: Side
    amount: float
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: str = "M15"
    demo: bool = True


@dataclass
class Position:
    position_id: str
    symbol: str
    side: Side
    amount: float
    entry: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    timeframe: str
    status: str = "OPEN"
    exit_price: Optional[float] = None
    close_reason: Optional[str] = None
