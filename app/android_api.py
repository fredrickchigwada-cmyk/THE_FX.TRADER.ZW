from flask import Flask, jsonify

from app.trade_history_api import TradeHistoryAPI
from app.alert_api import AlertAPI
from app.settings_routes import settings_bp


def create_android_api():
    app = Flask(__name__)

    history = TradeHistoryAPI()
    alerts = AlertAPI()

    app.register_blueprint(settings_bp)

    @app.get("/api/v1/status")
    def status():
        return jsonify({
            "status": "ONLINE",
            "app": "THE_FX.TRADER.ZW",
            "version": "1.0.0",
            "symbol": "XAUUSD",
            "mode": "DEMO",
            "auto_trade": False,
            "real_trading": False,
        })

    @app.get("/api/v1/health")
    def health():
        return jsonify({
            "status": "OK",
            "service": "THE_FX.TRADER.ZW",
            "backend": "ONLINE",
        })

    @app.get("/api/v1/market")
    def market():
        return jsonify({
            "status": "OK",
            "symbol": "XAUUSD",
            "deriv_symbol": "frxXAUUSD",
            "market_data": "AVAILABLE",
        })

    @app.get("/api/v1/signal")
    def signal():
        return jsonify({
            "status": "OK",
            "symbol": "XAUUSD",
            "signal": "WAIT",
            "timeframe": "M15",
            "strength": 0,
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "risk_reward": None,
        })

    @app.get("/api/v1/trades")
    def trades():
        return jsonify({
            "status": "OK",
            "trades": history.get_trades(),
        })

    @app.get("/api/v1/performance")
    def performance():
        return jsonify({
            "status": "OK",
            "performance": history.get_performance(),
        })

    @app.get("/api/v1/alerts")
    def alert_state():
        return jsonify({
            "status": "OK",
            "alerts": alerts.snapshot(),
        })

    @app.get("/api/v1/safety")
    def safety():
        return jsonify({
            "status": "OK",
            "trade_mode": "DEMO",
            "auto_trade_enabled": False,
            "real_trading_enabled": False,
            "execution_enabled": False,
            "max_open_trades": 1,
            "risk_per_trade": 1.0,
        })

    return app


app = create_android_api()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8001,
        debug=False
    )
