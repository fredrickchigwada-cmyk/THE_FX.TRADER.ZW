from app.oauth.routes import oauth_bp
from app.email_mode_routes import email_mode_bp
from flask import Flask, jsonify

from app.trade_history_api import TradeHistoryAPI

from app.auth_routes import auth_bp

from app.trading_mode_routes import mode_bp
app = Flask(__name__)

# Stage 32I: Deriv OAuth routes
app.register_blueprint(oauth_bp)
app.secret_key = __import__('os').environ.get('FX_SESSION_SECRET', 'THE_FX_TRADER_ZW_DEV_SESSION_SECRET')
app.register_blueprint(auth_bp)
app.register_blueprint(mode_bp)
app.register_blueprint(email_mode_bp)
history = TradeHistoryAPI()


@app.get("/api/trades")
def trades():
    return jsonify({
        "status": "OK",
        "trades": history.get_trades(),
    })


@app.get("/api/trades/<contract_id>")
def trade(contract_id):
    result = history.get_trade(contract_id)

    if result is None:
        return jsonify({
            "status": "NOT_FOUND",
            "message": "Trade not found",
        }), 404

    return jsonify({
        "status": "OK",
        "trade": result,
    })


@app.get("/api/performance")
def performance():
    return jsonify({
        "status": "OK",
        "performance": history.get_performance(),
    })


@app.get("/api/trades/<contract_id>/monitor")
def trade_monitor(contract_id):
    from deriv.auth import DerivAuthenticator
    from trading.deriv_executor import DerivExecutionClient
    from trading.contract_monitor import ContractMonitor
    from trading.trade_monitor import TradeMonitor

    client = DerivExecutionClient(DerivAuthenticator())

    try:
        client.connect()

        monitor = TradeMonitor(
            ContractMonitor(client)
        )

        snapshot = monitor.get_snapshot(
            contract_id,
            symbol="frxXAUUSD",
            side="BUY",
        )

        return jsonify({
            "status": "OK",
            "monitor": monitor.to_dict(snapshot),
        })

    except Exception as exc:
        return jsonify({
            "status": "ERROR",
            "message": str(exc),
        }), 500

    finally:
        client.disconnect()


@app.get("/api/trading/status")
def trading_status():
    return jsonify({
        "status": "OK",
        "symbol": "XAUUSD",
        "mode": "DEMO",
        "auto_trade": False,
        "real_trading": False,
        "execution_enabled": False,
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "ONLINE",
        "service": "THE_FX.TRADER.ZW",
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False,
    )
