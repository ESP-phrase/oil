import time
from typing import Optional

from ib_insync import IB, Contract, Order, Trade

from oilbot.config import IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID


class IBKRClient:
    def __init__(self):
        self.ib = IB()

    def connect(self) -> bool:
        try:
            self.ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
            return True
        except Exception as e:
            print(f"IBKR connect failed: {e}")
            return False

    def disconnect(self):
        self.ib.disconnect()

    def is_connected(self) -> bool:
        return self.ib.isConnected()

    def place_market_order(self, symbol: str, quantity: int, action: str) -> Optional[Trade]:
        contract = Contract(symbol=symbol, secType="FUT", exchange="CME", currency="USD")
        order = Order(action=action, totalQuantity=quantity, orderType="MKT")
        trade = self.ib.placeOrder(contract, order)
        return trade

    def get_account_summary(self) -> dict:
        summary = {}
        for acct in self.ib.accountSummary():
            summary[acct.tag] = float(acct.value) if acct.currency == "BASE" else acct.value
        return summary
