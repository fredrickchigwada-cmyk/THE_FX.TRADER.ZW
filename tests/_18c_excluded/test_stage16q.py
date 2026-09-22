import time

from core.deriv_rate_limit import (
    DerivRateLimitGuard,
)


print()
print("=" * 80)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16Q — DERIV RATE-LIMIT PROTECTION")
print("=" * 80)
print()

guard = DerivRateLimitGuard(
    base_backoff=30,
    max_backoff=300,
)

print("Testing normal state...")

assert guard.can_retry() is True

print("Normal retry        : ALLOWED")


print()
print("Testing Deriv RateLimit response...")

message = {
    "msg_type": "ticks",
    "error": {
        "code": "RateLimit",
        "message": (
            "You have reached the rate limit "
            "for ticks."
        ),
    },
}

detected = guard.detect(message)

assert detected is True
assert guard.status.limited is True
assert guard.status.violations == 1

print("RateLimit detected   : YES")
print(
    "Initial backoff      : "
    f"{guard.status.retry_after:.0f}s"
)


print()
print("Testing immediate retry protection...")

assert guard.can_retry() is False

print("Immediate retry      : BLOCKED")

remaining = guard.remaining()

print(
    "Remaining wait       : "
    f"{remaining:.1f}s"
)


print()
print("Testing repeated RateLimit...")

guard.detect(message)

assert guard.status.violations == 2
assert guard.status.retry_after == 60

print(
    "Second backoff       : "
    f"{guard.status.retry_after:.0f}s"
)


print()
print("Testing maximum backoff...")

for _ in range(10):
    guard.detect(message)

assert guard.status.retry_after <= 300

print(
    "Maximum backoff      : "
    f"{guard.status.retry_after:.0f}s"
)


print()
print("Testing reset...")

guard.reset()

assert guard.status.limited is False
assert guard.status.violations == 0
assert guard.can_retry() is True

print("Reset                : PASSED")
print("Retry after reset    : ALLOWED")


print()
print("=" * 80)
print(" STAGE 16Q SUMMARY")
print("=" * 80)
print()
print("RateLimit detection  : PASSED")
print("Backoff protection   : PASSED")
print("Retry blocking      : PASSED")
print("Escalating backoff  : PASSED")
print("Maximum backoff     : PASSED")
print("Reset mechanism     : PASSED")
print()
print("Automatic trading   : DISABLED")
print("Trade execution     : DISABLED")
print("Signal-only mode    : ENABLED")
print("XAUUSD priority     : ENABLED")
print("Data source         : Deriv")
print()
print("STAGE 16Q: PASSED")
print("=" * 80)
print()
print("Termux session remains open.")
