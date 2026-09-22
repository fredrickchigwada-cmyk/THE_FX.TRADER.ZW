"""
THE_FX.TRADER.BOT.ZW
Stage 18G — Live Official News Feed

Sources:
- U.S. Bureau of Labor Statistics CPI RSS
- U.S. Bureau of Labor Statistics Employment Situation RSS
- Federal Reserve Monetary Policy RSS

News remains a confirmation/risk layer only.
No trade execution.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List

from core.news_intelligence import NewsIntelligence


@dataclass
class NewsFeedResult:
    source: str
    success: bool
    items: int
    error: str = ""


class LiveNewsFeed:
    FEEDS = {
        "BLS_CPI": "https://www.bls.gov/feed/cpi.rss",
        "BLS_EMPLOYMENT": "https://www.bls.gov/feed/empsit.rss",
        "FED_MONETARY": "https://www.federalreserve.gov/feeds/press_monetary.xml",
    }

    def __init__(
        self,
        news=None,
        timeout=10,
        max_age_seconds=6 * 3600,
    ):
        self.news = news or NewsIntelligence(
            max_age_seconds=max_age_seconds
        )
        self.timeout = int(timeout)
        self.last_results: Dict[str, NewsFeedResult] = {}
        self.last_refresh = 0.0

    def feed_names(self) -> List[str]:
        return list(self.FEEDS.keys())

    def fetch_one(self, name: str) -> NewsFeedResult:
        if name not in self.FEEDS:
            result = NewsFeedResult(
                source=name,
                success=False,
                items=0,
                error="UNKNOWN_FEED",
            )
            self.last_results[name] = result
            return result

        before = len(self.news.items)

        items = self.news.fetch_rss(
            self.FEEDS[name],
            source=name,
            timeout=self.timeout,
        )

        added = max(
            0,
            len(self.news.items) - before,
        )

        error = self.news.last_error

        result = NewsFeedResult(
            source=name,
            success=not bool(error),
            items=added,
            error=error,
        )

        self.last_results[name] = result

        return result

    def refresh(self) -> Dict[str, NewsFeedResult]:
        results = {}

        for name in self.FEEDS:
            results[name] = self.fetch_one(name)

        self.last_refresh = time.time()

        return results

    def fresh_xauusd_news(self):
        return self.news.fresh_items("XAUUSD")

    def xauusd_risk(self):
        return self.news.risk_assessment("XAUUSD")

    def snapshot(self):
        return {
            "feeds": {
                name: {
                    "success": result.success,
                    "items": result.items,
                    "error": result.error,
                }
                for name, result
                in self.last_results.items()
            },
            "last_refresh": self.last_refresh,
            "xauusd": self.xauusd_risk(),
        }
