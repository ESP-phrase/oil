import pandas as pd
import numpy as np

from oilbot.config import (
    INITIAL_CAPITAL,
    SLIPPAGE_TICKS,
    COMMISSION_PER_SIDE,
    MAX_POSITION_PCT,
    STOP_LOSS_ATR_MULTIPLIER,
)
from oilbot.strategy.signals import _atr


def run_backtest(
    cl_df: pd.DataFrame,
    signal_series: pd.Series,
) -> pd.DataFrame:
    df = cl_df.copy()
    df["signal"] = signal_series.reindex(df.index).fillna(0)
    df["position"] = np.where(df["signal"] > 0.5, 1, np.where(df["signal"] < -0.5, -1, 0))
    df["returns"] = df["close"].pct_change()
    df["strategy_returns"] = df["position"].shift(1) * df["returns"]
    df["strategy_returns"] = df["strategy_returns"].fillna(0)

    df["equity"] = INITIAL_CAPITAL * (1 + df["strategy_returns"]).cumprod()
    df["drawdown"] = (df["equity"] / df["equity"].cummax()) - 1

    atr = _atr(df, 14)
    df["stop_loss"] = np.where(
        df["position"] == 1,
        df["close"] - atr * STOP_LOSS_ATR_MULTIPLIER,
        df["close"] + atr * STOP_LOSS_ATR_MULTIPLIER,
    )

    return df
