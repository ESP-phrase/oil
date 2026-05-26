import pandas as pd

from oilbot.config import SIGNAL_WEIGHTS, SIGNAL_THRESHOLD
from oilbot.strategy.signals import (
    volatility_breakout_signal,
    eia_import_surprise_signal,
    eia_iran_import_signal,
    put_call_ratio_signal,
    headline_signal,
)


def compute_composite_signal(
    cl_df: pd.DataFrame,
    eia_df: pd.DataFrame,
    headline_zscore: float,
    pcr: float,
) -> tuple[float, dict[str, float]]:
    signals = {}

    signals["volatility_breakout"] = volatility_breakout_signal(cl_df)
    signals["eia_import_surprise"] = eia_import_surprise_signal(eia_df)
    signals["eia_iran_import"] = eia_iran_import_signal(eia_df)
    signals["put_call_ratio"] = put_call_ratio_signal(pcr)
    signals["iran_headline_intensity"] = headline_signal(headline_zscore)

    composite = sum(
        signals.get(name, 0.0) * weight
        for name, weight in SIGNAL_WEIGHTS.items()
    )
    composite = max(-1.0, min(1.0, composite))

    return composite, signals


def should_trade(composite: float) -> tuple[bool, str]:
    if abs(composite) >= SIGNAL_THRESHOLD:
        direction = "BUY" if composite > 0 else "SELL"
        return True, direction
    return False, ""
