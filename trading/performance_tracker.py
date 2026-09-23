from dataclasses import dataclass


@dataclass
class PerformanceSummary:
    total_trades: int
    wins: int
    losses: int
    breakeven: int
    win_rate: float
    total_stakes: float
    total_profit: float
    average_profit: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    current_streak: int
    streak_type: str


class PerformanceTracker:
    """Calculates performance from TradeJournal records."""

    def __init__(self, journal):
        self.journal = journal

    def calculate(self) -> PerformanceSummary:
        records = self.journal.all()

        total_trades = len(records)

        wins = sum(1 for r in records if r.result == "WIN")
        losses = sum(1 for r in records if r.result == "LOSS")
        breakeven = sum(1 for r in records if r.result == "BREAKEVEN")

        win_rate = (
            (wins / total_trades) * 100
            if total_trades
            else 0.0
        )

        total_stakes = sum(
            r.stake or 0.0
            for r in records
        )

        total_profit = sum(
            r.profit or 0.0
            for r in records
        )

        average_profit = (
            total_profit / total_trades
            if total_trades
            else 0.0
        )

        gross_profit = sum(
            max(r.profit or 0.0, 0.0)
            for r in records
        )

        gross_loss = sum(
            abs(min(r.profit or 0.0, 0.0))
            for r in records
        )

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = float("inf")
        else:
            profit_factor = 0.0

        current_streak = 0
        streak_type = "NONE"

        if records:
            latest_result = records[-1].result

            if latest_result in ("WIN", "LOSS"):
                streak_type = latest_result
                for record in reversed(records):
                    if record.result == latest_result:
                        current_streak += 1
                    else:
                        break

        return PerformanceSummary(
            total_trades=total_trades,
            wins=wins,
            losses=losses,
            breakeven=breakeven,
            win_rate=win_rate,
            total_stakes=total_stakes,
            total_profit=total_profit,
            average_profit=average_profit,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            current_streak=current_streak,
            streak_type=streak_type,
        )
