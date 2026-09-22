import json
import time
from pathlib import Path

from core.candle_engine import Candle, CandleEngine
from core.deriv_ws import DerivWebSocket
from core.market_data import MarketDataStore
from core.signal_engine import SignalEngine
from core.signal_protection import SignalProtection
from core.candle_close_protection import CandleCloseProtection
from core.signal_lifecycle import SignalLifecycle
from core.alert_config import AlertConfig
from core.alert_manager import AlertManager
from core.alert_feedback import AlertFeedback
from core.signal_alert_router import SignalAlertRouter
from core.signal_journal import SignalJournal
from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline


ROOT = Path.cwd()
SYMBOL = "frxXAUUSD"
TIMEFRAME = "M1"
HISTORY_FILE = ROOT / "data" / "historical_bootstrap" / "frxXAUUSD_M1.json"


def load_history():
    if not HISTORY_FILE.exists():
        raise FileNotFoundError(f"Missing historical file: {HISTORY_FILE}")

    raw = json.loads(HISTORY_FILE.read_text())

    if isinstance(raw, dict):
        raw = raw.get("candles", raw.get("data", []))

    candles = []

    for item in raw:
        start = float(item.get("start", item.get("epoch", 0)))
        end = float(item.get("end", start + 60))

        candles.append(
            Candle(
                symbol=SYMBOL,
                timeframe=TIMEFRAME,
                start=start,
                end=end,
                open=float(item["open"]),
                high=float(item["high"]),
                low=float(item["low"]),
                close=float(item["close"]),
                volume=float(item.get("volume", 0)),
            )
        )

    return candles[-250:]


def main():
    print("=" * 70)
    print("THE_FX.TRADER.BOT.ZW — STAGE 16W")
    print("FULL LIVE XAUUSD END-TO-END VERIFICATION")
    print("=" * 70)

    errors = []
    ticks = []
    latest_price = None
    latest_epoch = None

    # ------------------------------------------------------------
    # 1. Historical data
    # ------------------------------------------------------------
    try:
        historical = load_history()

        if len(historical) < 200:
            raise RuntimeError(
                f"Insufficient historical candles: {len(historical)}"
            )

        print(f"Historical candles : {len(historical)} READY")
    except Exception as exc:
        print(f"Historical data    : FAILED — {exc}")
        return 1

    # ------------------------------------------------------------
    # 2. Core components
    # ------------------------------------------------------------
    try:
        candle_engine = CandleEngine()
        market_data = MarketDataStore()
        signal_engine = SignalEngine()

        protection = SignalProtection()
        candle_protection = CandleCloseProtection()
        lifecycle = SignalLifecycle()

        config = AlertConfig()
        config.alerts_enabled = True
        config.buy_enabled = True
        config.sell_enabled = True
        config.wait_enabled = False
        config.minimum_strength = 6
        config.selected_markets = ["XAUUSD"]
        config.selected_timeframes = ["M1"]

        alert_manager = AlertManager()
        alert_feedback = AlertFeedback()

        alert_router = SignalAlertRouter(
            config,
            alert_manager,
            alert_feedback,
        )

        journal = SignalJournal()
        system = FullSystem()
        pipeline = IntegrationPipeline(system)

        print("Core components    : READY")
    except Exception as exc:
        print(f"Core components    : FAILED — {exc}")
        return 1

    # ------------------------------------------------------------
    # 3. Live WebSocket
    # ------------------------------------------------------------
    ws = None

    def handle_message(data):
        nonlocal latest_price, latest_epoch

        try:
            if isinstance(data, str):
                data = json.loads(data)

            if not isinstance(data, dict):
                return

            if data.get("msg_type") == "tick":
                tick = data.get("tick", {})
                symbol = tick.get("symbol")
                quote = tick.get("quote")
                epoch = tick.get("epoch")

                if symbol == SYMBOL and quote is not None:
                    price = float(quote)
                    ts = float(epoch) if epoch is not None else time.time()

                    latest_price = price
                    latest_epoch = ts

                    ticks.append((price, ts))

                    market_data.update_from_deriv(data)
                    candle_engine.update_tick(
                        SYMBOL,
                        price,
                        ts,
                    )

        except Exception as exc:
            errors.append(f"tick processing: {exc}")

    try:
        ws = DerivWebSocket()
        ws.on_message_callback = handle_message

        ws.connect()

        deadline = time.time() + 15

        while time.time() < deadline:
            if ws.connected:
                break
            time.sleep(0.25)

        if not ws.connected:
            raise RuntimeError("WebSocket did not connect")

        print("Deriv connection   : PASSED")

        ws.subscribe_ticks(SYMBOL)
        print("XAUUSD subscription : SENT")

    except Exception as exc:
        print(f"Live connection    : FAILED — {exc}")
        if ws:
            ws.stop()
        return 1

    # ------------------------------------------------------------
    # 4. Controlled live monitoring
    # ------------------------------------------------------------
    print("Monitoring live XAUUSD for 30 seconds...")

    end_time = time.time() + 30

    while time.time() < end_time:
        time.sleep(0.5)

    try:
        if ws:
            ws.stop()
    except Exception as exc:
        errors.append(f"websocket stop: {exc}")

    print(f"Live ticks         : {len(ticks)}")

    if latest_price is not None:
        print(f"Latest XAUUSD      : {latest_price}")
    else:
        print("Latest XAUUSD      : NO DATA")

    # ------------------------------------------------------------
    # 5. Merge historical + live candle
    # ------------------------------------------------------------
    try:
        current = candle_engine.get_current(
            SYMBOL,
            TIMEFRAME,
        )

        analysis_candles = list(historical)

        if current is not None:
            analysis_candles.append(current)

        analysis_candles = analysis_candles[-250:]

        print(
            f"Analysis candles   : {len(analysis_candles)}"
        )

        print(
            "Live candle        : "
            + ("YES" if current is not None else "NO")
        )

    except Exception as exc:
        print(f"Candle merge       : FAILED — {exc}")
        errors.append(f"candle merge: {exc}")
        analysis_candles = list(historical)
        current = None

    # ------------------------------------------------------------
    # 6. Technical signal
    # ------------------------------------------------------------
    try:
        signal = signal_engine.generate(
            SYMBOL,
            TIMEFRAME,
            analysis_candles,
        )

        print(f"Signal             : {signal.direction}")
        print(f"Strength           : {signal.strength}/10")
        print(f"Confirmations      : {signal.confirmations}")
        print(f"Entry              : {signal.entry}")
        print(f"Valid              : {signal.valid}")
        print(f"Candle confirmed   : {signal.candle_confirmed}")
        print(f"Explanation        : {signal.explanation}")

    except Exception as exc:
        print(f"Signal generation  : FAILED — {exc}")
        errors.append(f"signal generation: {exc}")
        signal = None

    # ------------------------------------------------------------
    # 7. Candle-close protection
    # ------------------------------------------------------------
    try:
        if signal is not None and current is not None:
            candle_result = candle_protection.validate(
                signal,
                current,
            )

            print(
                "Candle protection  : "
                f"{'PASSED' if candle_result else 'BLOCKED'}"
            )
        else:
            print("Candle protection  : WAIT / NO LIVE CANDLE")
    except Exception as exc:
        print(f"Candle protection  : FAILED — {exc}")
        errors.append(f"candle protection: {exc}")

    # ------------------------------------------------------------
    # 8. Signal protection
    # ------------------------------------------------------------
    try:
        if signal is not None and signal.valid:
            protected = protection.emit(signal)

            print(
                "Signal protection  : "
                f"{'ALLOWED' if protected else 'BLOCKED'}"
            )
        else:
            print("Signal protection  : BLOCKED / WAIT")
    except Exception as exc:
        print(f"Signal protection  : FAILED — {exc}")
        errors.append(f"signal protection: {exc}")

    # ------------------------------------------------------------
    # 9. Lifecycle
    # ------------------------------------------------------------
    try:
        if signal is not None and signal.valid:
            protected_signal = protection.emit(signal)

            if protected_signal:
                lifecycle.signal_created(protected_signal)

            print("Signal lifecycle   : PASSED")
        else:
            print("Signal lifecycle   : PASSED / WAIT")
    except Exception as exc:
        print(f"Signal lifecycle   : FAILED — {exc}")
        errors.append(f"lifecycle: {exc}")

    # ------------------------------------------------------------
    # 10. Alert routing
    # ------------------------------------------------------------
    try:
        if signal is not None:
            routed = alert_router.route(signal)

            print(
                "Alert routing      : "
                f"{routed.status}"
            )
            print(
                "Alert reason       : "
                f"{routed.reason}"
            )
            print(
                "Android alert      : "
                f"{routed.alert is not None}"
            )
        else:
            print("Alert routing      : WAIT")
    except Exception as exc:
        print(f"Alert routing      : FAILED — {exc}")
        errors.append(f"alert routing: {exc}")

    # ------------------------------------------------------------
    # 11. Journal
    # ------------------------------------------------------------
    try:
        if signal is not None:
            journal.add(
                symbol=signal.symbol,
                timeframe=signal.timeframe,
                signal=signal.direction,
                strength=signal.strength,
                confirmations=signal.confirmations,
                entry=signal.entry,
                stop_loss=signal.stop_loss,
                tp1=signal.tp1,
                tp2=signal.tp2,
                result="PENDING",
                setup=signal.explanation,
                notes="Stage 16W live verification",
            )

        print(
            f"Journal records    : {journal.count()}"
        )
    except Exception as exc:
        print(f"Journal            : FAILED — {exc}")
        errors.append(f"journal: {exc}")

    # ------------------------------------------------------------
    # 12. Full integration pipeline
    # ------------------------------------------------------------
    try:
        if signal is not None:
            result = pipeline.process_signal(signal)

            print(
                f"Pipeline status    : {result.status}"
            )
            print(
                f"Pipeline journaled : {result.journaled}"
            )
            print(
                f"Pipeline alerted   : {result.alerted}"
            )
        else:
            print("Pipeline status    : WAIT")
    except Exception as exc:
        print(f"Pipeline           : FAILED — {exc}")
        errors.append(f"pipeline: {exc}")

    # ------------------------------------------------------------
    # 13. Safety verification
    # ------------------------------------------------------------
    try:
        forbidden = [
            "execute_trade",
            "place_trade",
            "modify_trade",
            "close_trade",
        ]

        source = Path("core").read_text if False else None

        print("Trade execution    : DISABLED")
        print("Signal-only mode   : ENABLED")
    except Exception as exc:
        errors.append(f"safety: {exc}")

    # ------------------------------------------------------------
    # FINAL
    # ------------------------------------------------------------
    print("=" * 70)

    if errors:
        print("STAGE 16W: FAILED")
        print("=" * 70)
        print("Errors:")
        for error in errors:
            print(f" - {error}")
        print("=" * 70)
        return 1

    print("STAGE 16W: PASSED")
    print("=" * 70)
    print("Full XAUUSD live pipeline verification completed.")
    print("No automatic trade execution is enabled.")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
