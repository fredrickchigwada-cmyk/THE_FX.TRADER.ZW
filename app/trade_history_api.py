from database.trade_database import TradeDatabase
from trading.persistent_performance import PersistentPerformance


class TradeHistoryAPI:
    """Read-only interface for trades and performance."""

    def __init__(self, database=None):
        self.database = database or TradeDatabase()

    def get_trades(self):
        return self.database.all_trades()

    def get_trade(self, contract_id):
        return self.database.get_trade(contract_id)

    def get_performance(self):
        summary = PersistentPerformance(self.database).calculate()

        return {
            "total_trades": summary.total_trades,
            "wins": summary.wins,
            "losses": summary.losses,
            "breakeven": summary.breakeven,
            "win_rate": summary.win_rate,
            "total_stakes": summary.total_stakes,
            "total_profit": summary.total_profit,
            "average_profit": summary.average_profit,
            "gross_profit": summary.gross_profit,
            "gross_loss": summary.gross_loss,
            "profit_factor": summary.profit_factor,
            "current_streak": summary.current_streak,
            "streak_type": summary.streak_type,
        }

    def snapshot(self):
        return {
            "trades": self.get_trades(),
            "performance": self.get_performance(),
        }
