import numpy as np

from oilbot.strategy.signals import _atr
from oilbot.config import STOP_LOSS_ATR_MULTIPLIER


def compute_stop_price(
    entry_price: float,
    current_price: float,
    atr_value: float,
    direction: str,
) -> float:
    offset = atr_value * STOP_LOSS_ATR_MULTIPLIER
    if direction == "BUY":
        stop = current_price - offset
        if entry_price - stop > 0:
            trail = current_price - stop
            return max(stop, entry_price - trail)
        return stop
    else:
        stop = current_price + offset
        if stop - entry_price > 0:
            trail = stop - current_price
            return min(stop, entry_price + trail)
        return stop
