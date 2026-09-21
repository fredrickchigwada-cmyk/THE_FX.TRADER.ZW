import json
import os
import threading
import time
from datetime import datetime

import websocket

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

try:
    from jnius import autoclass
    ANDROID_AVAILABLE = True
except Exception:
    ANDROID_AVAILABLE = False


# ============================================================
# THE_FX.TRADER BOT
# EXISTING SIGNAL-ONLY SYSTEM
# ============================================================

BOT_NAME = "THE_FX.TRADER BOT"
SYMBOL = "frxXAUUSD"
DISPLAY_SYMBOL = "XAUUSD"

WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"

CONTACT = "+263 71 458 8785"

# IMPORTANT:
# Automatic trading is permanently disabled.
AUTO_TRADING = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.join(BASE_DIR, "alert_sounds")


# ============================================================
# ALERT SYSTEM
# ============================================================

class AlertSystem:

    def __init__(self):
        self.sounds = {}

        self._load_sound("BUY", "buy.wav")
        self._load_sound("SELL", "sell.wav")
        self._load_sound("STOP BUY", "stop_buy.wav")
        self._load_sound("STOP SELL", "stop_sell.wav")

    def _load_sound(self, name, filename):
        path = os.path.join(SOUND_DIR, filename)

        try:
            if os.path.exists(path):
                sound = SoundLoader.load(path)

                if sound:
                    self.sounds[name] = sound

        except Exception:
            pass

    def vibrate(self, duration=300):

        if not ANDROID_AVAILABLE:
            return

        try:
            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Context = autoclass(
                "android.content.Context"
            )

            VibrationEffect = autoclass(
                "android.os.VibrationEffect"
            )

            activity = PythonActivity.mActivity

            vibrator = activity.getSystemService(
                Context.VIBRATOR_SERVICE
            )

            effect = VibrationEffect.createOneShot(
                duration,
                VibrationEffect.DEFAULT_AMPLITUDE
            )

            vibrator.vibrate(effect)

        except Exception:

            try:
                PythonActivity = autoclass(
                    "org.kivy.android.PythonActivity"
                )

                Context = autoclass(
                    "android.content.Context"
                )

                activity = PythonActivity.mActivity

                vibrator = activity.getSystemService(
                    Context.VIBRATOR_SERVICE
                )

                vibrator.vibrate(duration)

            except Exception:
                pass

    def play(self, signal):

        sound = self.sounds.get(signal)

        if sound:

            try:
                sound.stop()
                sound.play()
            except Exception:
                pass

        if signal == "BUY":
            self.vibrate(300)

        elif signal == "SELL":
            self.vibrate(500)

        elif signal == "STOP BUY":
            self.vibrate(700)

        elif signal == "STOP SELL":
            self.vibrate(900)


# ============================================================
# TRADING BOT
# ============================================================

class TradingBot:

    def __init__(self, update_callback):

        self.update_callback = update_callback

        self.running = False
        self.ws = None

        self.price = None
        self.prices = []

        self.signal = "WAIT"
        self.previous_signal = "WAIT"
        self.last_signal = "WAIT"

        self.signal_time = "-"

        self.entry = "-"
        self.sl = "-"
        self.tp1 = "-"
        self.tp2 = "-"
        self.tp3 = "-"

        self.ema9 = "-"
        self.ema21 = "-"
        self.rsi = "-"
        self.macd = "-"
        self.atr = "-"

        self.support = "-"
        self.resistance = "-"

        self.confirmations = 0
        self.signal_strength = "WAITING"

        self.market_status = "WAITING"
        self.data_status = "WAITING"
        self.connection_status = "DISCONNECTED"

        self.history = []

        self.alerts = AlertSystem()

        self.last_alert_signal = None
        self.last_tick_time = None

        # 1-minute candle engine state
        self.current_candle_minute = None
        self.current_candle_open = None
        self.current_candle_high = None
        self.current_candle_low = None
        self.current_candle_close = None
        self.candle_count = 0
        self.last_analysis_candle = None

    # ========================================================
    # START
    # ========================================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.market_status = "CONNECTING"
        self.data_status = "CONNECTING"

        self.update_callback("CONNECTING")

        threading.Thread(
            target=self._connect,
            daemon=True
        ).start()

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        self.running = False

        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass

        self.connection_status = "DISCONNECTED"
        self.market_status = "STOPPED"
        self.data_status = "OFFLINE"

        self.update_callback("STOPPED")

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(self):

        if not self.running:
            self.start()

    # ========================================================
    # CONNECTION
    # ========================================================

    def _connect(self):
        """Maintain a persistent Deriv WebSocket connection."""

        reconnect_delay = 5

        while self.running:
            try:
                self.connection_status = "CONNECTING"
                self.market_status = "CHECKING"
                self.data_status = "CONNECTING"

                self.update_callback("CONNECTING TO DERIV...")

                self.ws = websocket.WebSocketApp(
                    WS_URL,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )

                self.ws.run_forever(
                    ping_interval=30,
                    ping_timeout=10
                )

            except Exception as error:
                if not self.running:
                    break

                self.connection_status = "RECONNECTING"
                self.data_status = "RECONNECTING"
                self.update_callback(
                    f"CONNECTION ERROR: {error}"
                )

            if self.running:
                self.connection_status = "RECONNECTING"

                # Never permanently lock the bot into CLOSED.
                # Deriv's market state is checked again on every
                # new connection attempt.
                if self.market_status == "CLOSED":
                    self.data_status = "MARKET CLOSED"
                    self.update_callback(
                        "MARKET CLOSED - WAITING FOR OPEN"
                    )
                else:
                    self.data_status = "RECONNECTING"
                    self.update_callback(
                        "RECONNECTING..."
                    )

                time.sleep(reconnect_delay)

    def _on_open(self, ws):
        """Connect to Deriv and load recent 1-minute XAUUSD candles."""

        self.connection_status = "CONNECTED"
        self.market_status = "CHECKING"
        self.data_status = "LOADING CANDLES"

        self.update_callback(
            "LOADING XAUUSD 1M CANDLES..."
        )

        # Load recent 1-minute candles first.
        history_request = {
            "ticks_history": SYMBOL,
            "end": "latest",
            "count": 100,
            "style": "candles",
            "granularity": 60
        }

        # Then subscribe to live XAUUSD ticks.
        tick_request = {
            "ticks": SYMBOL,
            "subscribe": 1
        }

        try:
            ws.send(json.dumps(history_request))
            ws.send(json.dumps(tick_request))

            self.update_callback(
                "HISTORY REQUESTED - STARTING LIVE DATA..."
            )

        except Exception as error:
            self.connection_status = "ERROR"
            self.data_status = "ERROR"
            self.update_callback(
                f"SEND ERROR: {error}"
            )

    # ========================================================
    # MESSAGE
    # ========================================================

    def _on_message(self, ws, message):
        """Process Deriv WebSocket messages safely."""

        try:
            data = json.loads(message)

            # ------------------------------------------------
            # HISTORICAL 1-MINUTE CANDLES
            # ------------------------------------------------

            if data.get("msg_type") == "candles":
                candles = data.get("candles", [])

                if isinstance(candles, list) and candles:
                    closed_candles = []

                    for candle in candles[:-1]:
                        try:
                            closed_candles.append({
                                "epoch": int(candle["epoch"]),
                                "open": float(candle["open"]),
                                "high": float(candle["high"]),
                                "low": float(candle["low"]),
                                "close": float(candle["close"])
                            })
                        except (KeyError, TypeError, ValueError):
                            continue

                    if closed_candles:
                        self.prices = [
                            candle["close"]
                            for candle in closed_candles
                        ][-300:]

                        self.candle_count = len(self.prices)

                        self.market_status = "OPEN"
                        self.data_status = "HISTORICAL DATA"

                        self.update_callback(
                            f"LOADED {self.candle_count} XAUUSD 1M CANDLES"
                        )

                        # Calculate immediately using the loaded history.
                        self._calculate()

                return

            # ------------------------------------------------
            # DERIV ERROR
            # ------------------------------------------------

            if data.get("error"):
                error_data = data.get("error", {})

                error_code = error_data.get(
                    "code",
                    error_data.get("subcode", "")
                )

                error_message = error_data.get(
                    "message",
                    "Unknown Deriv error"
                )

                # IMPORTANT:
                # Deriv can return msg_type='tick' together with
                # an error when the market is closed. Therefore
                # ERROR MUST ALWAYS be handled before tick data.

                if (
                    error_code == "MarketIsClosed"
                    or error_data.get("subcode") == "MarketIsClosed"
                    or "MarketIsClosed" in error_message
                ):
                    # Deriv has confirmed that the XAUUSD
                    # tick subscription is currently unavailable.
                    # Mark it closed, but DO NOT permanently stop
                    # the bot. The reconnect loop will try again.
                    self.market_status = "CLOSED"
                    self.data_status = "MARKET CLOSED"
                    self.connection_status = "CONNECTED"

                    self.signal = "WAIT"
                    self.entry = "-"
                    self.sl = "-"
                    self.tp1 = "-"
                    self.tp2 = "-"
                    self.tp3 = "-"
                    self.signal_strength = "MARKET CLOSED"

                    self.update_callback(
                        "MARKET CLOSED - WAITING FOR OPEN"
                    )

                    # Close this WebSocket so the reconnect loop
                    # can establish a fresh subscription later.
                    try:
                        ws.close()
                    except Exception:
                        pass

                    return

                self.data_status = "ERROR"
                self.update_callback(
                    "DERIV: " + str(error_message)
                )
                return

            # ------------------------------------------------
            # ------------------------------------------------
            # LIVE 1-MINUTE CANDLE BUILDER
            # ------------------------------------------------

            tick = data.get("tick")

            if not isinstance(tick, dict):
                return

            if "quote" not in tick:
                return

            try:
                quote = float(tick["quote"])
            except (TypeError, ValueError):
                return

            epoch = tick.get("epoch")

            try:
                epoch = int(epoch) if epoch is not None else int(time.time())
            except (TypeError, ValueError):
                epoch = int(time.time())

            candle_minute = epoch // 60

            # Always update the live displayed price.
            self.price = quote
            self.last_tick_time = time.time()

            self.connection_status = "CONNECTED"
            self.market_status = "OPEN"
            self.data_status = "LIVE"

            # Start the first live candle.
            if self.current_candle_minute is None:
                self.current_candle_minute = candle_minute
                self.current_candle_open = quote
                self.current_candle_high = quote
                self.current_candle_low = quote
                self.current_candle_close = quote

                self.update_callback(
                    f"LIVE XAUUSD: {quote:.2f}"
                )
                return

            # Same minute: update the current candle.
            if candle_minute == self.current_candle_minute:
                self.current_candle_high = max(
                    self.current_candle_high,
                    quote
                )

                self.current_candle_low = min(
                    self.current_candle_low,
                    quote
                )

                self.current_candle_close = quote

                self.update_callback(
                    f"LIVE XAUUSD: {quote:.2f}"
                )
                return

            # New minute: close the previous candle.
            if candle_minute > self.current_candle_minute:

                closed_price = self.current_candle_close

                self.prices.append(closed_price)

                if len(self.prices) > 300:
                    self.prices.pop(0)

                self.candle_count = len(self.prices)

                # Start the new candle.
                self.current_candle_minute = candle_minute
                self.current_candle_open = quote
                self.current_candle_high = quote
                self.current_candle_low = quote
                self.current_candle_close = quote

                # Run the existing signal engine once per
                # completed 1-minute candle.
                self._calculate()

                self.update_callback(
                    f"NEW 1M CANDLE | XAUUSD: {quote:.2f}"
                )

                return

            # Ignore an out-of-order tick.
            return

            # ------------------------------------------------
    # ========================================================
    # ERROR
    # ========================================================

        except Exception as error:
            self.data_status = "DATA ERROR"
            self.update_callback(
                f"DATA ERROR: {error}"
            )

    def _on_error(self, ws, error):
        """Handle WebSocket errors without confusing them with market status."""

        if not self.running:
            return

        self.connection_status = "ERROR"

        # Keep CLOSED state if Deriv already confirmed the market
        # is closed. Otherwise mark the connection for retry.
        if self.market_status == "CLOSED":
            self.data_status = "MARKET CLOSED"
            self.update_callback("MARKET CLOSED")
        else:
            self.data_status = "RECONNECTING"
            self.update_callback(
                f"CONNECTION ERROR: {error}"
            )

    # ========================================================
    # CLOSE
    # ========================================================

    def _on_close(self, ws, code, msg):
        """Handle WebSocket closure and allow automatic reconnect."""

        if not self.running:
            self.connection_status = "DISCONNECTED"
            return

        self.connection_status = "RECONNECTING"

        # If Deriv previously confirmed XAUUSD is closed,
        # do not overwrite that useful state with RECONNECTING.
        if self.market_status == "CLOSED":
            self.data_status = "MARKET CLOSED"
            self.update_callback("MARKET CLOSED")
        else:
            self.data_status = "RECONNECTING"
            self.update_callback("RECONNECTING...")

    # ========================================================
    # MARKET STATUS
    # ========================================================


    # ========================================================
    # INDICATORS + SIGNAL ENGINE
    # ========================================================

    def _ema_series(self, values, period):
        if len(values) < period:
            return []

        alpha = 2.0 / (period + 1.0)
        ema = sum(values[:period]) / period
        result = [ema]

        for value in values[period:]:
            ema = (value * alpha) + (ema * (1.0 - alpha))
            result.append(ema)

        return result

    def _rsi_value(self, values, period=14):
        if len(values) < period + 1:
            return None

        gains = []
        losses = []

        for i in range(1, len(values)):
            change = values[i] - values[i - 1]
            gains.append(max(change, 0.0))
            losses.append(max(-change, 0.0))

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        for i in range(period, len(gains)):
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def _atr_value(self, values, period=14):
        if len(values) < period + 1:
            return None

        ranges = [
            abs(values[i] - values[i - 1])
            for i in range(1, len(values))
        ]

        atr = sum(ranges[:period]) / period

        for value in ranges[period:]:
            atr = ((atr * (period - 1)) + value) / period

        return atr

    def _calculate(self):
        try:
            if self.price is None:
                return

            if len(self.prices) < 35:
                self.signal = "WAIT"
                self.signal_strength = (
                    f"COLLECTING DATA {len(self.prices)}/35"
                )
                self.update_callback("COLLECTING XAUUSD DATA...")
                return

            values = list(self.prices)
            price = self.price

            # EMA 9 / 21
            ema9_series = self._ema_series(values, 9)
            ema21_series = self._ema_series(values, 21)

            if not ema9_series or not ema21_series:
                return

            ema9 = ema9_series[-1]
            ema21 = ema21_series[-1]

            self.ema9 = f"{ema9:.2f}"
            self.ema21 = f"{ema21:.2f}"

            # RSI 14
            rsi = self._rsi_value(values, 14)

            if rsi is None:
                return

            self.rsi = f"{rsi:.2f}"

            # MACD
            ema12 = self._ema_series(values, 12)
            ema26 = self._ema_series(values, 26)

            if not ema12 or not ema26:
                return

            macd = ema12[-1] - ema26[-1]
            self.macd = f"{macd:.4f}"

            # ATR
            atr = self._atr_value(values, 14)

            if atr is None:
                return

            atr = max(atr, 0.00001)
            self.atr = f"{atr:.4f}"

            # Support / resistance
            recent = values[-min(30, len(values)):]
            support = min(recent)
            resistance = max(recent)

            self.support = f"{support:.2f}"
            self.resistance = f"{resistance:.2f}"

            # Conditions
            buy_score = 0
            sell_score = 0

            if ema9 > ema21:
                buy_score += 1
            elif ema9 < ema21:
                sell_score += 1

            if values[-1] > values[-6]:
                buy_score += 1
            elif values[-1] < values[-6]:
                sell_score += 1

            if 50 <= rsi < 70:
                buy_score += 1
            elif 30 < rsi <= 50:
                sell_score += 1

            if macd > 0:
                buy_score += 1
            elif macd < 0:
                sell_score += 1

            midpoint = (support + resistance) / 2.0

            if price > midpoint:
                buy_score += 1
            elif price < midpoint:
                sell_score += 1

            self.confirmations = max(buy_score, sell_score)

            if buy_score >= 4 and buy_score > sell_score:
                direction = "BUY"
            elif sell_score >= 4 and sell_score > buy_score:
                direction = "SELL"
            else:
                direction = "WAIT"

            old_signal = self.signal
            current_signal = direction

            # Stop alerts when the opposite direction appears.
            if self.last_signal == "BUY" and direction == "SELL":
                current_signal = "STOP BUY"

            elif self.last_signal == "SELL" and direction == "BUY":
                current_signal = "STOP SELL"

            # Strength
            # STOP signals take priority over the new direction.
            if current_signal == "STOP BUY":
                self.signal_strength = "EXIT BUY"
            elif current_signal == "STOP SELL":
                self.signal_strength = "EXIT SELL"
            elif direction == "BUY":
                self.signal_strength = f"BUY {buy_score}/5"
            elif direction == "SELL":
                self.signal_strength = f"SELL {sell_score}/5"
            else:
                self.signal_strength = f"WAIT {self.confirmations}/5"

            # Trade setup
            if direction == "BUY":
                self.entry = f"{price:.2f}"

                sl = price - (atr * 1.5)
                risk = max(price - sl, 0.00001)

                self.sl = f"{sl:.2f}"
                self.tp1 = f"{price + risk:.2f}"
                self.tp2 = f"{price + (risk * 2):.2f}"
                self.tp3 = f"{price + (risk * 3):.2f}"

            elif direction == "SELL":
                self.entry = f"{price:.2f}"

                sl = price + (atr * 1.5)
                risk = max(sl - price, 0.00001)

                self.sl = f"{sl:.2f}"
                self.tp1 = f"{price - risk:.2f}"
                self.tp2 = f"{price - (risk * 2):.2f}"
                self.tp3 = f"{price - (risk * 3):.2f}"

            elif current_signal in ("STOP BUY", "STOP SELL"):
                self.entry = "-"
                self.sl = "-"
                self.tp1 = "-"
                self.tp2 = "-"
                self.tp3 = "-"

            else:
                # WAIT: show POTENTIAL setup using the stronger
                # technical direction, without treating it as confirmed.
                potential_direction = None

                if buy_score > sell_score:
                    potential_direction = "BUY"
                elif sell_score > buy_score:
                    potential_direction = "SELL"

                if potential_direction == "BUY":
                    self.entry = f"{price:.2f}"

                    sl = price - (atr * 1.5)
                    risk = max(price - sl, 0.00001)

                    self.sl = f"{sl:.2f}"
                    self.tp1 = f"{price + risk:.2f}"
                    self.tp2 = f"{price + (risk * 2):.2f}"
                    self.tp3 = f"{price + (risk * 3):.2f}"

                elif potential_direction == "SELL":
                    self.entry = f"{price:.2f}"

                    sl = price + (atr * 1.5)
                    risk = max(sl - price, 0.00001)

                    self.sl = f"{sl:.2f}"
                    self.tp1 = f"{price - risk:.2f}"
                    self.tp2 = f"{price - (risk * 2):.2f}"
                    self.tp3 = f"{price - (risk * 3):.2f}"

                else:
                    self.entry = "-"
                    self.sl = "-"
                    self.tp1 = "-"
                    self.tp2 = "-"
                    self.tp3 = "-"
                self.sl = "-"
                self.tp1 = "-"
                self.tp2 = "-"
                self.tp3 = "-"

            self.signal = current_signal

            if direction in ("BUY", "SELL"):
                self.last_signal = direction

            # Alert only when signal changes.
            if current_signal != old_signal:
                self.signal_time = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                self.history.append(
                    f"{self.signal_time} | "
                    f"{current_signal} | "
                    f"{price:.2f}"
                )

                if len(self.history) > 20:
                    self.history.pop(0)

                if current_signal != self.last_alert_signal:
                    self.alerts.play(current_signal)
                    self.last_alert_signal = current_signal

            self.update_callback(current_signal)

        except Exception as error:
            self.data_status = "CALCULATION ERROR"
            self.update_callback(
                f"CALCULATION ERROR: {error}"
            )


    def get_market_status(self):

        if self.market_status == "CLOSED":

            return "MARKET CLOSED"

        if self.running:

            return self.market_status

        return "STOPPED"


# ============================================================
# DASHBOARD CARD
# ============================================================

    def get_state(self):
        """Return the complete dashboard state."""
        return {
            "price": f"{self.price:.2f}" if self.price is not None else "-",
            "signal": self.signal,
            "strength": self.signal_strength,
            "market_open": self.market_status,
            "data_status": self.data_status,
            "last_signal_time": self.signal_time,
            "entry": self.entry,
            "sl": self.sl,
            "tp1": self.tp1,
            "tp2": self.tp2,
            "tp3": self.tp3,
            "ema9": self.ema9,
            "ema21": self.ema21,
            "rsi": self.rsi,
            "macd": self.macd,
            "atr": self.atr,
            "support": self.support,
            "resistance": self.resistance,
            "trend": self._dashboard_trend(),
            "momentum": self._dashboard_momentum(),
            "volatility": self._dashboard_volatility(),
            "history": list(self.history),
            "confirmations": self.confirmations,
            "connection": self.connection_status,
            "market_status": self.get_market_status(),
        }

    def _dashboard_trend(self):
        if self.ema9 == "-" or self.ema21 == "-":
            return "WAITING"
        try:
            if float(self.ema9) > float(self.ema21):
                return "BULLISH"
            if float(self.ema9) < float(self.ema21):
                return "BEARISH"
        except Exception:
            pass
        return "WAITING"

    def _dashboard_momentum(self):
        if len(self.prices) < 6:
            return "WAITING"
        if self.prices[-1] > self.prices[-6]:
            return "POSITIVE"
        if self.prices[-1] < self.prices[-6]:
            return "NEGATIVE"
        return "NEUTRAL"

    def _dashboard_volatility(self):
        if self.atr == "-" or self.price is None:
            return "WAITING"
        try:
            atr = float(self.atr)
            if atr > self.price * 0.001:
                return "HIGH"
            return "NORMAL"
        except Exception:
            return "WAITING"

class Card(BoxLayout):

    def __init__(
        self,
        title,
        value="-",
        **kwargs
    ):

        super().__init__(
            orientation="vertical",
            padding=dp(8),
            spacing=dp(2),
            size_hint_y=None,
            height=dp(72),
            **kwargs
        )

        with self.canvas.before:

            Color(
                0.08,
                0.09,
                0.12,
                1
            )

            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(10)]
            )

        self.bind(
            pos=self._update_background,
            size=self._update_background
        )

        self.title = Label(
            text=title,
            font_size="11sp",
            bold=True,
            size_hint_y=None,
            height=dp(22)
        )

        self.value = Label(
            text=value,
            font_size="16sp",
            bold=True
        )

        self.add_widget(
            self.title
        )

        self.add_widget(
            self.value
        )

    def _update_background(self, *args):

        self.background.pos = self.pos
        self.background.size = self.size


# ============================================================
# MAIN SCREEN
# ============================================================


class MainScreen(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(6),
            padding=dp(8),
            **kwargs
        )

        self.bot = TradingBot(self.update_screen)

        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(78)
        )

        header.add_widget(Label(
            text=BOT_NAME,
            font_size=dp(24),
            bold=True
        ))

        header.add_widget(Label(
            text="AUTO TRADING: DISABLED",
            font_size=dp(14),
            bold=True
        ))

        self.add_widget(header)

        self.signal_label = Label(
            text="WAIT",
            font_size=dp(38),
            bold=True,
            size_hint_y=None,
            height=dp(70)
        )

        self.signal_info = Label(
            text="Waiting for XAUUSD market data...",
            size_hint_y=None,
            height=dp(35)
        )

        self.add_widget(self.signal_label)
        self.add_widget(self.signal_info)

        status_row = BoxLayout(
            size_hint_y=None,
            height=dp(45),
            spacing=dp(4)
        )

        self.buy_btn = Button(
            text="BUY",
            disabled=True
        )

        self.sell_btn = Button(
            text="SELL",
            disabled=True
        )

        self.stop_buy_btn = Button(
            text="STOP BUY",
            disabled=True
        )

        self.stop_sell_btn = Button(
            text="STOP SELL",
            disabled=True
        )

        status_row.add_widget(self.buy_btn)
        status_row.add_widget(self.sell_btn)
        status_row.add_widget(self.stop_buy_btn)
        status_row.add_widget(self.stop_sell_btn)

        self.add_widget(status_row)

        scroll = ScrollView(
            do_scroll_x=False
        )

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=dp(5),
            size_hint_y=None
        )

        content.bind(
            minimum_height=content.setter("height")
        )

        # ----------------------------------------------------
        # MARKET
        # ----------------------------------------------------

        content.add_widget(Label(
            text="MARKET",
            bold=True,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30)
        ))

        market_grid = GridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(100)
        )

        self.price_label = Label(
            text="PRICE\n---"
        )

        self.market_label = Label(
            text="MARKET\nCONNECTING..."
        )

        self.data_label = Label(
            text="DATA\nWAITING..."
        )

        self.time_label = Label(
            text="SIGNAL TIME\n---"
        )

        market_grid.add_widget(self.price_label)
        market_grid.add_widget(self.market_label)
        market_grid.add_widget(self.data_label)
        market_grid.add_widget(self.time_label)

        content.add_widget(market_grid)

        # ----------------------------------------------------
        # TRADE SETUP
        # ----------------------------------------------------

        content.add_widget(Label(
            text="TRADE SETUP",
            bold=True,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30)
        ))

        setup_grid = GridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(150)
        )

        self.entry_label = Label(text="ENTRY\n---")
        self.sl_label = Label(text="STOP LOSS\n---")
        self.tp1_label = Label(text="TP1\n---")
        self.tp2_label = Label(text="TP2\n---")
        self.tp3_label = Label(text="TP3\n---")
        self.rr_label = Label(text="RISK / REWARD\n---")

        setup_grid.add_widget(self.entry_label)
        setup_grid.add_widget(self.sl_label)
        setup_grid.add_widget(self.tp1_label)
        setup_grid.add_widget(self.tp2_label)
        setup_grid.add_widget(self.tp3_label)
        setup_grid.add_widget(self.rr_label)

        content.add_widget(setup_grid)

        # ----------------------------------------------------
        # INDICATORS
        # ----------------------------------------------------

        content.add_widget(Label(
            text="INDICATORS",
            bold=True,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30)
        ))

        indicator_grid = GridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(150)
        )

        self.ema_label = Label(text="EMA 9 / 21\n---")
        self.rsi_label = Label(text="RSI 14\n---")
        self.macd_label = Label(text="MACD\n---")
        self.atr_label = Label(text="ATR\n---")
        self.support_label = Label(text="SUPPORT\n---")
        self.resistance_label = Label(text="RESISTANCE\n---")

        indicator_grid.add_widget(self.ema_label)
        indicator_grid.add_widget(self.rsi_label)
        indicator_grid.add_widget(self.macd_label)
        indicator_grid.add_widget(self.atr_label)
        indicator_grid.add_widget(self.support_label)
        indicator_grid.add_widget(self.resistance_label)

        content.add_widget(indicator_grid)

        # ----------------------------------------------------
        # MARKET CONDITIONS
        # ----------------------------------------------------

        content.add_widget(Label(
            text="MARKET CONDITIONS",
            bold=True,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30)
        ))

        self.condition_label = Label(
            text=(
                "Trend: ---\n"
                "Momentum: ---\n"
                "Volatility: ---\n"
                "Strength: ---"
            ),
            size_hint_y=None,
            height=dp(85)
        )

        content.add_widget(self.condition_label)

        # ----------------------------------------------------
        # SIGNAL HISTORY
        # ----------------------------------------------------

        content.add_widget(Label(
            text="SIGNAL HISTORY",
            bold=True,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30)
        ))

        self.history_label = Label(
            text="No signals yet.",
            size_hint_y=None,
            height=dp(140),
            halign="left",
            valign="top"
        )

        self.history_label.bind(
            width=lambda instance, value:
            setattr(instance, "text_size", (value, None))
        )

        content.add_widget(self.history_label)

        scroll.add_widget(content)
        self.add_widget(scroll)

        # ----------------------------------------------------
        # CONTROLS
        # ----------------------------------------------------

        controls = BoxLayout(
            size_hint_y=None,
            height=dp(45),
            spacing=dp(5)
        )

        start_btn = Button(text="START")
        stop_btn = Button(text="STOP")
        refresh_btn = Button(text="REFRESH")

        start_btn.bind(
            on_press=lambda instance: self.bot.start()
        )

        stop_btn.bind(
            on_press=lambda instance: self.bot.stop()
        )

        refresh_btn.bind(
            on_press=lambda instance: self.refresh_ui()
        )

        controls.add_widget(start_btn)
        controls.add_widget(stop_btn)
        controls.add_widget(refresh_btn)

        self.add_widget(controls)

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        self.add_widget(Label(
            text=(
                "XAUUSD • DERIV LIVE DATA\n"
                "Contact: +263 71 458 8785\n"
                "© THE_FX.TRADER BOT"
            ),
            font_size=dp(10),
            size_hint_y=None,
            height=dp(55)
        ))

        Clock.schedule_interval(
            self.refresh_ui,
            1
        )

        # Automatically connect to Deriv when the app opens.
        # START/STOP buttons remain available for manual control.
        Clock.schedule_once(
            lambda dt: self.bot.start(),
            0.5
        )

    def update_screen(self, data=None):
        self.refresh_ui()

    def refresh_ui(self, *args):

        try:
            data = self.bot.get_state()
        except Exception:
            return

        if not data:
            return

        def fmt(value):
            if value is None:
                return "---"

            try:
                return f"{float(value):.2f}"
            except Exception:
                return str(value)

        price = data.get("price")
        signal = data.get("signal", "WAIT")
        strength = data.get("strength", 0)

        if price is not None:
            self.price_label.text = (
                f"PRICE\n{fmt(price)}"
            )

        market_open = data.get(
            "market_open",
            True
        )

        if market_open != "OPEN":
            self.market_label.text = (
                "MARKET\nCLOSED"
            )

            self.signal_label.text = "WAIT"

            self.signal_info.text = (
                "MARKET CLOSED"
            )

        else:
            self.market_label.text = (
                "MARKET\nOPEN"
            )

            self.signal_label.text = signal

            self.signal_info.text = (
                f"Confirmation: {strength}"
            )

        self.data_label.text = (
            "DATA\n" +
            str(
                data.get(
                    "data_status",
                    "WAITING"
                )
            )
        )

        self.time_label.text = (
            "SIGNAL TIME\n" +
            str(
                data.get(
                    "last_signal_time",
                    "---"
                )
            )
        )

        self.entry_label.text = (
            f"ENTRY\n{fmt(data.get('entry'))}"
        )

        self.sl_label.text = (
            f"STOP LOSS\n{fmt(data.get('sl'))}"
        )

        self.tp1_label.text = (
            f"TP1\n{fmt(data.get('tp1'))}"
        )

        self.tp2_label.text = (
            f"TP2\n{fmt(data.get('tp2'))}"
        )

        self.tp3_label.text = (
            f"TP3\n{fmt(data.get('tp3'))}"
        )

        self.rr_label.text = (
            "RISK / REWARD\nATR BASED"
        )

        self.ema_label.text = (
            f"EMA 9 / 21\n"
            f"{fmt(data.get('ema9'))} / "
            f"{fmt(data.get('ema21'))}"
        )

        self.rsi_label.text = (
            f"RSI 14\n{fmt(data.get('rsi'))}"
        )

        self.macd_label.text = (
            f"MACD\n{fmt(data.get('macd'))}"
        )

        self.atr_label.text = (
            f"ATR\n{fmt(data.get('atr'))}"
        )

        self.support_label.text = (
            f"SUPPORT\n{fmt(data.get('support'))}"
        )

        self.resistance_label.text = (
            f"RESISTANCE\n{fmt(data.get('resistance'))}"
        )

        self.condition_label.text = (
            f"Trend: {data.get('trend', '---')}\n"
            f"Momentum: {data.get('momentum', '---')}\n"
            f"Volatility: {data.get('volatility', '---')}\n"
            f"Strength: {strength}"
        )

        history = data.get(
            "history",
            []
        )

        if history:
            self.history_label.text = "\n".join(
                str(item)
                for item in history[-8:]
            )
        else:
            self.history_label.text = (
                "No signals yet."
            )


# ============================================================
# APPLICATION
# ============================================================

class FXTraderApp(App):

    def build(self):
        self.title = BOT_NAME
        return MainScreen()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    FXTraderApp().run()

