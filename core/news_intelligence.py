"""
THE_FX.TRADER.BOT.ZW
Stage 18D — Market News Intelligence

News is a confirmation/risk layer only.
It NEVER creates or executes a trade.
"""

from __future__ import annotations

import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from email.utils import parsedate_to_datetime
from typing import List, Optional


@dataclass
class NewsItem:
    title: str
    summary: str = ""
    source: str = ""
    url: str = ""
    published: float = 0.0
    impact: str = "LOW"
    bias: str = "NEUTRAL"
    relevance: int = 0

    @property
    def age_seconds(self) -> float:
        if not self.published:
            return float("inf")
        return max(0.0, time.time() - self.published)

    @property
    def stale(self) -> bool:
        return self.age_seconds > 6 * 3600

    def to_dict(self):
        data = asdict(self)
        data["age_seconds"] = self.age_seconds
        data["stale"] = self.stale
        return data


class NewsIntelligence:
    """
    Analyzes market news for relevance and risk.

    Primary focus:
    XAUUSD / Gold
    USD
    Fed / interest rates
    CPI / inflation
    NFP / employment
    major economic events
    """

    DEFAULT_MAX_AGE = 6 * 3600

    HIGH_IMPACT_KEYWORDS = (
        "federal reserve",
        "fed decision",
        "fed rate",
        "interest rate decision",
        "rate decision",
        "fomc",
        "powell",
        "cpi",
        "inflation",
        "core inflation",
        "ppi",
        "nonfarm payroll",
        "non-farm payroll",
        "nfp",
        "employment report",
        "jobs report",
        "unemployment",
        "gdp",
        "recession",
        "emergency",
        "war",
        "sanctions",
        "tariff",
        "geopolitical",
    )

    MEDIUM_IMPACT_KEYWORDS = (
        "gold",
        "xau",
        "usd",
        "dollar",
        "treasury",
        "yield",
        "bond",
        "central bank",
        "economy",
        "economic data",
        "retail sales",
        "consumer confidence",
        "manufacturing",
        "services",
    )

    BULLISH_GOLD_KEYWORDS = (
        "gold rises",
        "gold gains",
        "gold climbs",
        "gold higher",
        "gold rally",
        "gold rallies",
        "gold surge",
        "gold jumps",
        "gold advances",
        "dollar falls",
        "dollar weakens",
        "usd falls",
        "usd weakens",
        "rate cut",
        "lower rates",
        "dovish",
        "safe haven demand",
    )

    BEARISH_GOLD_KEYWORDS = (
        "gold falls",
        "gold drops",
        "gold declines",
        "gold lower",
        "gold tumbles",
        "gold slides",
        "dollar rises",
        "dollar strengthens",
        "usd rises",
        "usd strengthens",
        "rate hike",
        "higher rates",
        "hawkish",
        "yields rise",
    )

    def __init__(self, max_age_seconds: int = DEFAULT_MAX_AGE):
        self.max_age_seconds = max(60, int(max_age_seconds))
        self.items: List[NewsItem] = []
        self.last_fetch = 0.0
        self.last_error = ""

    def _text(self, item: NewsItem) -> str:
        return (
            f"{item.title} "
            f"{item.summary}"
        ).lower()

    def relevance_score(self, title: str, summary: str = "") -> int:
        text = f"{title} {summary}".lower()
        score = 0

        if any(k in text for k in ("xauusd", "xau/usd", "gold")):
            score += 5

        if any(k in text for k in ("usd", "dollar", "fed", "fomc")):
            score += 3

        if any(
            k in text
            for k in (
                "cpi",
                "inflation",
                "nfp",
                "nonfarm",
                "interest rate",
                "yield",
                "treasury",
            )
        ):
            score += 2

        return min(score, 10)

    def classify_impact(self, title: str, summary: str = "") -> str:
        text = f"{title} {summary}".lower()

        if any(k in text for k in self.HIGH_IMPACT_KEYWORDS):
            return "HIGH"

        if any(k in text for k in self.MEDIUM_IMPACT_KEYWORDS):
            return "MEDIUM"

        return "LOW"

    def classify_bias(self, title: str, summary: str = "") -> str:
        text = f"{title} {summary}".lower()

        bullish = sum(
            1 for k in self.BULLISH_GOLD_KEYWORDS
            if k in text
        )
        bearish = sum(
            1 for k in self.BEARISH_GOLD_KEYWORDS
            if k in text
        )

        if bullish > bearish:
            return "BULLISH"

        if bearish > bullish:
            return "BEARISH"

        return "NEUTRAL"

    def analyze_item(self, item: NewsItem) -> NewsItem:
        item.relevance = self.relevance_score(
            item.title,
            item.summary,
        )
        item.impact = self.classify_impact(
            item.title,
            item.summary,
        )
        item.bias = self.classify_bias(
            item.title,
            item.summary,
        )
        return item

    def add(
        self,
        title: str,
        summary: str = "",
        source: str = "",
        url: str = "",
        published: Optional[float] = None,
    ) -> NewsItem:
        item = NewsItem(
            title=str(title).strip(),
            summary=str(summary).strip(),
            source=str(source).strip(),
            url=str(url).strip(),
            published=float(
                published if published is not None else time.time()
            ),
        )

        self.analyze_item(item)
        self.items.append(item)

        return item

    def fresh_items(
        self,
        symbol: str = "XAUUSD",
    ) -> List[NewsItem]:
        symbol = str(symbol).upper()

        result = []

        for item in self.items:
            if item.stale:
                continue

            if item.age_seconds > self.max_age_seconds:
                continue

            if symbol == "XAUUSD":
                if item.relevance >= 3:
                    result.append(item)
            else:
                if item.relevance >= 2:
                    result.append(item)

        return result

    def risk_assessment(
        self,
        symbol: str = "XAUUSD",
    ) -> dict:
        fresh = self.fresh_items(symbol)

        high = [
            x for x in fresh
            if x.impact == "HIGH"
        ]

        bullish = sum(
            1 for x in fresh
            if x.bias == "BULLISH"
        )

        bearish = sum(
            1 for x in fresh
            if x.bias == "BEARISH"
        )

        if high:
            risk = "HIGH"
        elif fresh:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        if bullish > bearish:
            bias = "BULLISH"
        elif bearish > bullish:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        return {
            "symbol": symbol,
            "risk": risk,
            "bias": bias,
            "fresh_items": len(fresh),
            "high_impact": len(high),
            "bullish": bullish,
            "bearish": bearish,
            "news_available": bool(fresh),
        }

    def clear(self):
        self.items.clear()

    def parse_rss(
        self,
        xml_text: str,
        source: str = "",
    ) -> List[NewsItem]:
        root = ET.fromstring(xml_text)
        parsed = []

        for node in root.iter():
            if node.tag.lower().endswith("item"):
                title = ""
                summary = ""
                url = ""
                published = 0.0

                for child in list(node):
                    tag = child.tag.lower().split("}")[-1]
                    value = (
                        child.text.strip()
                        if child.text
                        else ""
                    )

                    if tag == "title":
                        title = value
                    elif tag in ("description", "summary"):
                        summary = value
                    elif tag in ("link", "guid"):
                        if not url and value.startswith("http"):
                            url = value
                    elif tag in (
                        "pubdate",
                        "published",
                        "updated",
                    ):
                        try:
                            published = (
                                parsedate_to_datetime(
                                    value
                                ).timestamp()
                            )
                        except Exception:
                            published = 0.0

                if title:
                    parsed.append(
                        self.add(
                            title=title,
                            summary=summary,
                            source=source,
                            url=url,
                            published=published or time.time(),
                        )
                    )

        return parsed

    def fetch_rss(
        self,
        url: str,
        source: str = "",
        timeout: int = 10,
    ) -> List[NewsItem]:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    "THE_FX.TRADER.BOT.ZW/1.0"
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout,
            ) as response:
                raw = response.read()

            text = raw.decode(
                "utf-8",
                errors="replace",
            )

            result = self.parse_rss(
                text,
                source=source,
            )

            self.last_fetch = time.time()
            self.last_error = ""

            return result

        except Exception as exc:
            self.last_error = str(exc)
            return []

    def snapshot(self) -> dict:
        risk = self.risk_assessment("XAUUSD")

        return {
            "items": len(self.items),
            "fresh": len(
                self.fresh_items("XAUUSD")
            ),
            "last_fetch": self.last_fetch,
            "last_error": self.last_error,
            "xauusd": risk,
        }
