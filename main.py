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

        while self.running:

            try:

                self.connection_status = "CONNECTING"

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

                self.connection_status = "ERROR"

                self.update_callback(
                    f"CONNECTION ERROR: {error}"
                )

                if self.running:
                    time.sleep(5)

    # ========================================================
    # OPEN CONNECTION
    # ========================================================

    def _on_open(self, ws):

        self.connection_status = "CONNECTED"

        self.market_status = "OPEN"
        self.data_status = "LIVE"

        self.update_callback("CONNECTED")

        request = {
            "ticks": SYMBOL,
            "subscribe": 1
        }

        try:

            ws.send(
                json.dumps(request)
            )

        except Exception as error:

            self.update_callback(
                f"SEND ERROR: {error}"
            )

    # ========================================================
    # MESSAGE
    # ========================================================

    def _on_message(self, ws, message):

        try:

            data = json.loads(message)

            # ------------------------------------------------
            # DERIV ERROR
            # ------------------------------------------------

            if "error" in data:

                error_message = data["error"].get(
                    "message",
                    "Unknown Deriv error"
                )

                if "MarketIsClosed" in error_message:

                    self.market_status = "CLOSED"
                    self.data_status = "MARKET CLOSED"

                    self.signal = "WAIT"

                    self.entry = "-"
                    self.sl = "-"
                    self.tp1 = "-"
                    self.tp2 = "-"
                    self.tp3 = "-"

                    self.signal_strength = "MARKET CLOSED"

                    self.update_callback(
                        "MARKET CLOSED"
                    )

                else:

                    self.data_status = "ERROR"
                    self.market_status = "ERROR"

                    self.update_callback(
                        "DERIV: " + error_message
                    )

                return

            # ------------------------------------------------
            # TICK
            # ------------------------------------------------

            tick = data.get("tick")

            if not tick:
                return

            quote = float(
                tick["quote"]
            )

            self.price = quote

            self.last_tick_time = time.time()

            self.market_status = "OPEN"
            self.data_status = "LIVE"

            self.prices.append(quote)

            if len(self.prices) > 300:

                self.prices.pop(0)

            self._calculate()

        except Exception as error:

            self.data_status = "DATA ERROR"

            self.update_callback(
                f"DATA ERROR: {error}"
            )

    # ========================================================
    # ERROR
    # ========================================================

    def _on_error(self, ws, error):

        self.connection_status = "ERROR"

        self.update_callback(
            f"ERROR: {error}"
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def _on_close(self, ws, code, msg):

        if self.running:

            self.connection_status = "RECONNECTING"
            self.data_status = "RECONNECTING"

            self.update_callback(
                "RECONNECTING..."
            )

    # ========================================================
    # EMA
    # ========================================================

    def _ema(self, values, period):

        if len(values) < period:
            return None

        multiplier = 2 / (period + 1)

        ema = sum(
            values[:period]
        ) / period

        for price in values[period:]:

            ema = (
                (price - ema) * multiplier
            ) + ema

        return ema

    # ========================================================
    # RSI
    # ========================================================

    def _rsi(self, values, period=14):

        if len(values) <= period:
            return None

        gains = []
        losses = []

        for i in range(1, len(values)):

            change = (
                values[i] -
                values[i - 1]
            )

            if change > 0:

                gains.append(change)
                losses.append(0)

            else:

                gains.append(0)
                losses.append(
                    abs(change)
                )

        avg_gain = (
            sum(gains[-period:]) /
            period
        )

        avg_loss = (
            sum(losses[-period:]) /
            period
        )

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss

        return 100 - (
            100 / (1 + rs)
        )

    # ========================================================
    # MACD
    # ========================================================

    def _macd(self, values):

        if len(values) < 35:
            return None

        ema12 = self._ema(
            values,
            12
        )

        ema26 = self._ema(
            values,
            26
        )

        if ema12 is None:
            return None

        if ema26 is None:
            return None

        return ema12 - ema26

    # ========================================================
    # ATR
    # ========================================================

    def _atr(self, values, period=14):

        if len(values) <= period:
            return None

        ranges = []

        for i in range(1, len(values)):

            ranges.append(
                abs(
                    values[i] -
                    values[i - 1]
                )
            )

        return (
            sum(ranges[-period:]) /
            period
        )

    # ========================================================
    # CALCULATE SIGNAL
    # ========================================================

    def _calculate(self):

        # Never generate signals while closed.

        if self.market_status == "CLOSED":

            self.signal = "WAIT"
            self.signal_strength = "MARKET CLOSED"

            return

        if len(self.prices) < 35:

            self.signal = "WAIT"
            self.signal_strength = "BUILDING DATA"

            self.update_callback(
                "WAIT"
            )

            return

        values = self.prices

        price = values[-1]

        ema9 = self._ema(
            values,
            9
        )

        ema21 = self._ema(
            values,
            21
        )

        rsi = self._rsi(
            values,
            14
        )

        macd = self._macd(
            values
        )

        atr = self._atr(
            values,
            14
        )

        if (
            ema9 is None
            or ema21 is None
            or rsi is None
            or macd is None
            or atr is None
        ):

            self.signal = "WAIT"

            return

        # ----------------------------------------------------
        # INDICATORS
        # ----------------------------------------------------

        self.ema9 = f"{ema9:.2f}"
        self.ema21 = f"{ema21:.2f}"
        self.rsi = f"{rsi:.1f}"
        self.macd = f"{macd:.2f}"
        self.atr = f"{atr:.2f}"

        recent = values[-30:]

        self.support = (
            f"{min(recent):.2f}"
        )

        self.resistance = (
            f"{max(recent):.2f}"
        )

        # ----------------------------------------------------
        # MOMENTUM
        # ----------------------------------------------------

        momentum = (
            values[-1] -
            values[-6]
        )

        buy_confirmations = 0
        sell_confirmations = 0

        # EMA
        if ema9 > ema21:
            buy_confirmations += 1

        elif ema9 < ema21:
            sell_confirmations += 1

        # RSI
        if rsi > 50:
            buy_confirmations += 1

        elif rsi < 50:
            sell_confirmations += 1

        # MACD
        if macd > 0:
            buy_confirmations += 1

        elif macd < 0:
            sell_confirmations += 1

        # Momentum
        if momentum > 0:
            buy_confirmations += 1

        elif momentum < 0:
            sell_confirmations += 1

        # Price vs EMA
        if price > ema9:
            buy_confirmations += 1

        elif price < ema9:
            sell_confirmations += 1

        self.confirmations = max(
            buy_confirmations,
            sell_confirmations
        )

        if self.confirmations >= 5:

            self.signal_strength = (
                "VERY STRONG"
            )

        elif self.confirmations == 4:

            self.signal_strength = (
                "STRONG"
            )

        elif self.confirmations == 3:

            self.signal_strength = (
                "MODERATE"
            )

        elif self.confirmations == 2:

            self.signal_strength = (
                "WEAK"
            )

        else:

            self.signal_strength = (
                "WAITING"
            )

        # ----------------------------------------------------
        # NORMAL SIGNAL
        # ----------------------------------------------------

        new_signal = "WAIT"

        if buy_confirmations >= 3:

            new_signal = "BUY"

        elif sell_confirmations >= 3:

            new_signal = "SELL"

        # ----------------------------------------------------
        # STOP BUY
        # ----------------------------------------------------

        if self.last_signal == "BUY":

            bearish_reversal = (
                ema9 < ema21
                and rsi < 50
                and macd < 0
            )

            if bearish_reversal:

                new_signal = "STOP BUY"

        # ----------------------------------------------------
        # STOP SELL
        # ----------------------------------------------------

        elif self.last_signal == "SELL":

            bullish_reversal = (
                ema9 > ema21
                and rsi > 50
                and macd > 0
            )

            if bullish_reversal:

                new_signal = "STOP SELL"

        # ----------------------------------------------------
        # TRADE SETUP
        # ----------------------------------------------------

        if new_signal == "BUY":

            self.entry = (
                f"{price:.2f}"
            )

            stop_distance = max(
                atr * 1.5,
                price * 0.002
            )

            self.sl = (
                f"{price - stop_distance:.2f}"
            )

            self.tp1 = (
                f"{price + stop_distance:.2f}"
            )

            self.tp2 = (
                f"{price + stop_distance * 2:.2f}"
            )

            self.tp3 = (
                f"{price + stop_distance * 3:.2f}"
            )

        elif new_signal == "SELL":

            self.entry = (
                f"{price:.2f}"
            )

            stop_distance = max(
                atr * 1.5,
                price * 0.002
            )

            self.sl = (
                f"{price + stop_distance:.2f}"
            )

            self.tp1 = (
                f"{price - stop_distance:.2f}"
            )

            self.tp2 = (
                f"{price - stop_distance * 2:.2f}"
            )

            self.tp3 = (
                f"{price - stop_distance * 3:.2f}"
            )

        else:

            self.entry = "-"
            self.sl = "-"
            self.tp1 = "-"
            self.tp2 = "-"
            self.tp3 = "-"

        # ----------------------------------------------------
        # SIGNAL CHANGE
        # ----------------------------------------------------

        if new_signal != self.signal:

            self.previous_signal = (
                self.signal
            )

            self.signal = new_signal

            self.signal_time = (
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            self._record_signal(
                new_signal
            )

            if new_signal in (
                "BUY",
                "SELL",
                "STOP BUY",
                "STOP SELL"
            ):

                self._trigger_alert(
                    new_signal
                )

        # Remember active direction
        if new_signal in (
            "BUY",
            "SELL"
        ):

            self.last_signal = (
                new_signal
            )

        self.update_callback(
            "LIVE"
        )

    # ========================================================
    # ALERT
    # ========================================================

    def _trigger_alert(self, signal):

        if signal == self.last_alert_signal:
            return

        self.last_alert_signal = signal

        Clock.schedule_once(
            lambda dt:
            self.alerts.play(signal),
            0
        )

    # ========================================================
    # SIGNAL HISTORY
    # ========================================================

    def _record_signal(self, signal):

        if signal == "WAIT":
            return

        record = {
            "signal": signal,
            "price": (
                f"{self.price:.2f}"
                if self.price is not None
                else "-"
            ),
            "time": self.signal_time,
            "strength": (
                self.signal_strength
            ),
            "confirmations": (
                self.confirmations
            )
        }

        self.history.insert(
            0,
            record
        )

        if len(self.history) > 10:

            self.history.pop()

    # ========================================================
    # MARKET STATUS
    # ========================================================

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

        if not market_open:
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

