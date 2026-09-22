import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitStatus:
    limited: bool = False
    message: str = ""
    retry_after: float = 0.0
    violations: int = 0
    last_limited: Optional[float] = None


class DerivRateLimitGuard:
    """
    Protects THE_FX.TRADER.BOT.ZW from rapid Deriv
    tick-subscription retries.

    Signal-only.
    No trading or order execution.
    """

    def __init__(
        self,
        base_backoff: float = 30.0,
        max_backoff: float = 300.0,
    ):
        self.base_backoff = float(base_backoff)
        self.max_backoff = float(max_backoff)

        self.status = RateLimitStatus()

    def detect(self, message) -> bool:

        text = str(message)

        if "RateLimit" not in text and "rate limit" not in text.lower():
            return False

        self.status.limited = True
        self.status.message = text
        self.status.violations += 1
        self.status.last_limited = time.time()

        multiplier = min(
            self.status.violations,
            5,
        )

        delay = self.base_backoff * multiplier

        self.status.retry_after = min(
            delay,
            self.max_backoff,
        )

        return True

    def can_retry(
        self,
        now: Optional[float] = None,
    ) -> bool:

        if not self.status.limited:
            return True

        if now is None:
            now = time.time()

        elapsed = (
            now - self.status.last_limited
        )

        if elapsed >= self.status.retry_after:
            self.reset()
            return True

        return False

    def remaining(
        self,
        now: Optional[float] = None,
    ) -> float:

        if not self.status.limited:
            return 0.0

        if now is None:
            now = time.time()

        elapsed = (
            now - self.status.last_limited
        )

        return max(
            0.0,
            self.status.retry_after - elapsed,
        )

    def reset(self):

        self.status = RateLimitStatus()

    def snapshot(self) -> dict:

        return {
            "limited": self.status.limited,
            "message": self.status.message,
            "retry_after": self.status.retry_after,
            "violations": self.status.violations,
            "last_limited": self.status.last_limited,
            "remaining": self.remaining(),
        }
