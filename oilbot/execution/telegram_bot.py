from typing import Optional

from oilbot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramBot:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

    def send(self, message: str):
        if not self.enabled:
            print(f"[Telegram disabled] {message}")
            return
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }, timeout=10)

    def send_signal_alert(self, direction: str, symbol: str, price: float, conviction: float, details: str):
        msg = (
            f"🚨 *SIGNAL*: {direction} {symbol} @ ${price:.2f}\n"
            f"Conviction: {conviction:.0%}\n"
            f"Details: {details}\n"
            f"Reply `exec {direction.lower()} {symbol} 1` to confirm."
        )
        self.send(msg)
