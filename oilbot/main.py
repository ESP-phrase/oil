import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import time
import schedule
from datetime import datetime

from oilbot.config import EIA_API_KEY
from oilbot.data.fetcher import fetch_ohlcv, fetch_eia_imports
from oilbot.data.news import headline_intensity_score
from oilbot.data.store import init_db, save_ohlcv, save_signal, save_trade
from oilbot.strategy.composite import compute_composite_signal, should_trade
from oilbot.risk.position_sizer import size_position


class PaperTrader:
    def __init__(self, capital=100_000.0):
        self.capital = capital
        self.position = 0
        self.entry_price = 0.0
        self.trades = []

    def execute(self, direction: str, price: float, conviction: float):
        if direction == "BUY" and self.position <= 0:
            qty = size_position(self.capital, price, conviction)
            self.position = qty
            self.entry_price = price
            trade = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "CL",
                "direction": "BUY",
                "quantity": qty,
                "entry_price": price,
                "reason": f"conviction={conviction:.2f}",
            }
            save_trade(trade)
            self.trades.append(trade)
            print(f"[paper] BUY {qty} CL @ ${price:.2f}")
        elif direction == "SELL" and self.position > 0:
            pnl = (price - self.entry_price) * self.position
            trade = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "CL",
                "direction": "SELL",
                "quantity": self.position,
                "entry_price": self.entry_price,
                "exit_price": price,
                "pnl": round(pnl, 2),
                "reason": f"conviction={conviction:.2f}",
            }
            save_trade(trade)
            self.trades.append(trade)
            self.capital += pnl
            print(f"[paper] SELL {self.position} CL @ ${price:.2f} | PnL: ${pnl:.2f}")
            self.position = 0
            self.entry_price = 0.0

    def status(self) -> str:
        if self.position > 0:
            return f"Long {self.position} CL @ ${self.entry_price:.2f} | Capital: ${self.capital:.2f}"
        return f"Flat | Capital: ${self.capital:.2f}"


def tick(trader: PaperTrader):
    try:
        print(f"[tick] {trader.status()}")
        cl_df = fetch_ohlcv("CL")
        if cl_df.empty:
            print("[tick] no CL data")
            return

        save_ohlcv("CL", cl_df)

        eia_df = fetch_eia_imports() if EIA_API_KEY and EIA_API_KEY != "your_eia_api_key_here" else pd.DataFrame()
        if eia_df is None or eia_df.empty:
            eia_df = pd.DataFrame()
        headline_z = headline_intensity_score()
        pcr = 0.0

        composite, signals = compute_composite_signal(cl_df, eia_df, headline_z, pcr)

        for name, val in signals.items():
            save_signal(name, val)

        trade, direction = should_trade(composite)
        if trade:
            price = float(cl_df["close"].iloc[-1])
            conviction = abs(composite)
            msg = f"{direction} CL @ ${price:.2f} | conviction: {conviction:.0%} | signals: {signals}"
            print(f"[signal] {msg}")
            trader.execute(direction, price, conviction)
        else:
            print(f"[signal] no trade (composite={composite:.3f})")
    except Exception as e:
        print(f"[tick] error: {e}")


def main():
    print("=== OilBot Paper Trading ====")
    init_db()
    trader = PaperTrader()

    schedule.every(5).minutes.do(lambda: tick(trader))

    tick(trader)
    print("Running every 5 min. Press Ctrl+C to stop.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except KeyboardInterrupt:
            print("\nShutdown.")
            break


if __name__ == "__main__":
    main()
