BOT_NAME = "THE_FX.TRADER.BOT.ZW"
VERSION = "1.0.0"

CONTACT = "+263 78 455 2452"
COPYRIGHT = "© 2026 THE_FX.TRADER.BOT.ZW — All Rights Reserved"

# SAFETY: This project is signal-only.
# It does NOT place, modify, or close trades.
SIGNAL_ONLY = True

DEFAULT_TIMEFRAMES = [
    "M1",
    "M3",
    "M5",
    "M15",
    "M30",
    "H1",
    "H2",
    "H4",
    "H6",
    "H8",
    "H12",
    "D1",
    "W1",
    "MN1",
]

REQUESTED_MARKETS = [
    "XAUUSD",
    "BTCUSD",
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

MIN_SIGNAL_SCORE = 7
SIGNAL_COOLDOWN_SECONDS = 300
STALE_DATA_SECONDS = 10
