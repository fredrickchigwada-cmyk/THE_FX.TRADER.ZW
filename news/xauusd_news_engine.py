from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class NewsEvent:
    title: str
    source: str
    published_at: str
    impact: str = "LOW"
    currency: str = "USD"
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class XAUUSDNewsEngine:
    """
    XAUUSD-focused news intelligence.

    News may:
      - confirm an existing technical signal
      - weaken/conflict with an existing signal
      - force WAIT during conflicting high-impact events

    News must NEVER create BUY/SELL by itself.
    """

    ALLOWED_IMPACTS = {"LOW", "MEDIUM", "HIGH"}

    def __init__(self):
        self.events: List[NewsEvent] = []

    def add_event(self, event: NewsEvent):
        if event.currency.upper() not in {"USD", "XAU", "GLOBAL"}:
            return False

        event.impact = event.impact.upper()

        if event.impact not in self.ALLOWED_IMPACTS:
            raise ValueError("Invalid news impact")

        self.events.append(event)
        return True

    def set_events(self, events: List[NewsEvent]):
        self.events = []
        for event in events:
            self.add_event(event)

    def get_events(self):
        return [event.to_dict() for event in self.events]

    def classify_market_effect(self, event: NewsEvent):
        """
        Informational classification only.

        USD-strengthening news can pressure gold.
        USD-weakening news can support gold.
        Neutral/unclear events remain NEUTRAL.
        """
        text = event.title.lower()

        bearish_terms = (
            "hawkish",
            "rate hike",
            "interest rate increase",
            "strong jobs",
            "strong employment",
            "inflation rises",
            "higher inflation",
            "usd strengthens",
        )

        bullish_terms = (
            "dovish",
            "rate cut",
            "interest rate decrease",
            "weak jobs",
            "weak employment",
            "inflation falls",
            "lower inflation",
            "usd weakens",
        )

        if any(term in text for term in bearish_terms):
            return "BEARISH_XAUUSD"

        if any(term in text for term in bullish_terms):
            return "BULLISH_XAUUSD"

        return "NEUTRAL"

    def analyze_signal(self, signal: str):
        """
        Filters an EXISTING technical signal.
        News never generates a signal.
        """
        signal = signal.upper()

        if signal not in {"BUY", "SELL", "WAIT"}:
            raise ValueError("Signal must be BUY, SELL or WAIT")

        high_impact = [
            event for event in self.events
            if event.impact == "HIGH"
        ]

        effects = [
            self.classify_market_effect(event)
            for event in high_impact
        ]

        if signal == "WAIT":
            return {
                "signal": "WAIT",
                "news_status": "NEWS_NEUTRAL",
                "reason": "Technical engine already returned WAIT",
            }

        if not high_impact:
            return {
                "signal": signal,
                "news_status": "NEWS_NEUTRAL",
                "reason": "No high-impact XAUUSD/USD news currently available",
            }

        conflict = (
            (signal == "BUY" and "BEARISH_XAUUSD" in effects)
            or
            (signal == "SELL" and "BULLISH_XAUUSD" in effects)
        )

        if conflict:
            return {
                "signal": "WAIT",
                "news_status": "NEWS_CONFLICT_HIGH_IMPACT",
                "reason": "High-impact news conflicts with technical signal",
            }

        return {
            "signal": signal,
            "news_status": "NEWS_SUPPORTIVE_OR_NEUTRAL",
            "reason": "No conflicting high-impact news detected",
        }

    def status(self):
        high = sum(e.impact == "HIGH" for e in self.events)
        medium = sum(e.impact == "MEDIUM" for e in self.events)
        low = sum(e.impact == "LOW" for e in self.events)

        return {
            "instrument": "XAUUSD",
            "events": len(self.events),
            "high_impact": high,
            "medium_impact": medium,
            "low_impact": low,
            "engine": "READY",
        }
