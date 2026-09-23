from pathlib import Path
from app.oauth.routes import oauth_bp
from app.email_mode_routes import email_mode_bp
from flask import Flask, jsonify, send_file

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



# Existing THE_FX.TRADER.ZW dashboard
# Serves the dashboard already stored in frontend/index.html.
@app.get("/")
def dashboard_home():
    dashboard = Path(__file__).resolve().parent.parent / "frontend" / "index.html"

    if not dashboard.exists():
        return {
            "ok": False,
            "error": "frontend/index.html not found"
        }, 500

    return send_file(dashboard)

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



@app.post("/api/trading/preview")
def trading_preview():
    """
    Prepare a manual trade for review.

    Safety:
    - Does NOT execute a trade.
    - Does NOT call Deriv buy/sell.
    - Does NOT enable automatic trading.
    - Real execution remains protected by DerivExecutionClient.
    """
    data = request.get_json(silent=True) or {}

    signal = str(data.get("signal", "")).upper().strip()
    entry = data.get("entry")
    stop_loss = data.get("stop_loss")
    take_profit = data.get("take_profit")
    strength = data.get("strength", 0)
    timeframe = str(data.get("timeframe", "M1")).upper().strip()

    if signal not in ("BUY", "SELL"):
        return jsonify({
            "ok": False,
            "error": "Only BUY or SELL signals can be prepared."
        }), 400

    try:
        strength = float(strength)
    except (TypeError, ValueError):
        strength = 0

    if strength <= 0:
        return jsonify({
            "ok": False,
            "error": "Signal strength must be greater than zero."
        }), 400

    return jsonify({
        "ok": True,
        "status": "READY_FOR_MANUAL_CONFIRMATION",
        "symbol": "XAUUSD",
        "signal": signal,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "strength": strength,
        "timeframe": timeframe,
        "execution": "MANUAL",
        "real_trading": False,
        "order_sent": False,
        "message": "Trade prepared for explicit manual confirmation. No order was sent."
    })

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
    import os

    port = int(os.environ.get("PORT", "8000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )
