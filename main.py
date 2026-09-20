import json
import threading
import time
from datetime import datetime

import websocket

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

BOT_NAME = "THE_FX.TRADER BOT"
SYMBOL = "frxXAUUSD"
DISPLAY_SYMBOL = "XAUUSD"
WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"
CONTACT = "+263 71 458 8785"

AUTO_TRADING = False


class TradingBot:
    def __init__(self, update_callback):
        self.update_callback = update_callback
        self.running = False
        self.ws = None
        self.price = None
        self.prices = []
        self.signal = "WAIT"
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
        self.last_signal = "WAIT"
        self.signal_time = "-"

    def start(self):
        if self.running:
            return

        self.running = True
        self.update_callback("CONNECTING...")
        threading.Thread(target=self._connect, daemon=True).start()

    def stop(self):
        self.running = False

        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass

        self.update_callback("STOPPED")

    def refresh(self):
        if not self.running:
            self.start()

    def _connect(self):
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    WS_URL,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )

                self.ws.run_forever(
                    ping_interval=30,
                    ping_timeout=10
                )

            except Exception as e:
                self.update_callback(f"CONNECTION ERROR: {e}")

            if self.running:
                time.sleep(5)

    def _on_open(self, ws):
        self.update_callback("CONNECTED")

        request = {
            "ticks": SYMBOL,
            "subscribe": 1
        }

        ws.send(json.dumps(request))

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)

            if "error" in data:
                self.update_callback(
                    "DERIV: " + data["error"].get("message", "Unknown error")
                )
                return

            tick = data.get("tick")

            if not tick:
                return

            quote = float(tick["quote"])

            self.price = quote
            self.prices.append(quote)

            if len(self.prices) > 200:
                self.prices.pop(0)

            self._calculate()

        except Exception as e:
            self.update_callback(f"DATA ERROR: {e}")

    def _on_error(self, ws, error):
        self.update_callback(f"ERROR: {error}")

    def _on_close(self, ws, code, msg):
        if self.running:
            self.update_callback("RECONNECTING...")

    def _ema(self, values, period):
        if len(values) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period

        for price in values[period:]:
            ema = (price - ema) * multiplier + ema

        return ema

    def _rsi(self, values, period=14):
        if len(values) <= period:
            return None

        gains = []
        losses = []

        for i in range(1, len(values)):
            change = values[i] - values[i - 1]

            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _calculate(self):
        if len(self.prices) < 30:
            self.signal = "WAIT"
            self.update_callback("WAIT")
            return

        values = self.prices

        ema9 = self._ema(values, 9)
        ema21 = self._ema(values, 21)
        rsi = self._rsi(values, 14)

        if ema9 is None or ema21 is None or rsi is None:
            self.signal = "WAIT"
            return

        self.ema9 = f"{ema9:.2f}"
        self.ema21 = f"{ema21:.2f}"
        self.rsi = f"{rsi:.1f}"

        recent = values[-20:]
        self.support = f"{min(recent):.2f}"
        self.resistance = f"{max(recent):.2f}"

        momentum = values[-1] - values[-6]

        buy_confirmations = 0
        sell_confirmations = 0

        if ema9 > ema21:
            buy_confirmations += 1
        elif ema9 < ema21:
            sell_confirmations += 1

        if rsi > 50:
            buy_confirmations += 1
        elif rsi < 50:
            sell_confirmations += 1

        if momentum > 0:
            buy_confirmations += 1
        elif momentum < 0:
            sell_confirmations += 1

        price = values[-1]

        if buy_confirmations >= 2:
            self.signal = "BUY"
            self.entry = f"{price:.2f}"
            self.sl = f"{price * 0.997:.2f}"
            self.tp1 = f"{price * 1.003:.2f}"
            self.tp2 = f"{price * 0.006 + price:.2f}"
            self.tp3 = f"{price * 0.009 + price:.2f}"

        elif sell_confirmations >= 2:
            self.signal = "SELL"
            self.entry = f"{price:.2f}"
            self.sl = f"{price * 1.003:.2f}"
            self.tp1 = f"{price * 0.997:.2f}"
            self.tp2 = f"{price * 0.994:.2f}"
            self.tp3 = f"{price * 0.991:.2f}"

        else:
            self.signal = "WAIT"
            self.entry = "-"
            self.sl = "-"
            self.tp1 = "-"
            self.tp2 = "-"
            self.tp3 = "-"

        if self.signal != self.last_signal:
            self.last_signal = self.signal
            self.signal_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.update_callback("LIVE")


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=5,
            padding=8,
            **kwargs
        )

        self.bot = TradingBot(self.update_screen)

        self.title = Label(
            text=BOT_NAME,
            font_size="22sp",
            bold=True,
            size_hint_y=None,
            height=45
        )

        self.add_widget(self.title)

        scroll = ScrollView()

        self.info = Label(
            text="Starting...",
            font_size="15sp",
            halign="left",
            valign="top",
            size_hint_y=None
        )

        self.info.bind(
            texture_size=lambda instance, value:
            setattr(instance, "height", value[1])
        )

        scroll.add_widget(self.info)
        self.add_widget(scroll)

        buttons = BoxLayout(
            size_hint_y=None,
            height=55,
            spacing=5
        )

        start = Button(text="START")
        stop = Button(text="STOP")
        refresh = Button(text="REFRESH")

        start.bind(on_press=lambda x: self.bot.start())
        stop.bind(on_press=lambda x: self.bot.stop())
        refresh.bind(on_press=lambda x: self.bot.refresh())

        buttons.add_widget(start)
        buttons.add_widget(stop)
        buttons.add_widget(refresh)

        self.add_widget(buttons)

        Clock.schedule_interval(self.refresh_ui, 1)

    def update_screen(self, status):
        pass

    def refresh_ui(self, *args):
        bot = self.bot

        price = (
            f"{bot.price:.2f}"
            if bot.price is not None
            else "-"
        )

        self.info.text = (
            f"BOT: {BOT_NAME}\n"
            f"SYMBOL: {DISPLAY_SYMBOL}\n"
            f"AUTO TRADING: DISABLED\n\n"

            f"MARKET STATUS: {self._status()}\n"
            f"DATA STATUS: {self._data_status()}\n\n"

            f"LIVE PRICE: {price}\n"
            f"SIGNAL: {bot.signal}\n"
            f"SIGNAL TIME: {bot.signal_time}\n\n"

            f"ENTRY: {bot.entry}\n"
            f"STOP LOSS: {bot.sl}\n"
            f"TP1: {bot.tp1}\n"
            f"TP2: {bot.tp2}\n"
            f"TP3: {bot.tp3}\n\n"

            f"EMA 9: {bot.ema9}\n"
            f"EMA 21: {bot.ema21}\n"
            f"RSI 14: {bot.rsi}\n"
            f"MACD: {bot.macd}\n"
            f"ATR: {bot.atr}\n"
            f"SUPPORT: {bot.support}\n"
            f"RESISTANCE: {bot.resistance}\n\n"

            f"CONTACT: {CONTACT}\n"
            f"© THE_FX.TRADER BOT\n"
        )

    def _status(self):
        return "RUNNING" if self.bot.running else "STOPPED"

    def _data_status(self):
        return "LIVE" if self.bot.price is not None else "WAITING"


class FXTraderApp(App):
    def build(self):
        screen = MainScreen()
        screen.bot.start()
        return screen


if __name__ == "__main__":
    FXTraderApp().run()
