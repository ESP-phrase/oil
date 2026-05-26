import itertools

import pandas as pd

from oilbot.backtest.engine import run_backtest
from oilbot.backtest.metrics import compute_metrics
from oilbot.strategy.signals import volatility_breakout_signal, headline_signal
from oilbot.config import VOLATILITY_BREAKOUT_MULTIPLIER, SIGNAL_THRESHOLD


def param_sweep(cl_df: pd.DataFrame, headline_df: pd.DataFrame = None):
    multipliers = [1.5, 2.0, 2.5, 3.0]
    thresholds = [0.3, 0.4, 0.5, 0.6]

    results = []
    for mult, thresh in itertools.product(multipliers, thresholds):
        VOLATILITY_BREAKOUT_MULTIPLIER = mult
        SIGNAL_THRESHOLD = thresh

        df = cl_df.copy()
        df["signal"] = 0.0
        for idx in df.index:
            chunk = df.loc[:idx]
            if len(chunk) < 20:
                continue
            vol_sig = volatility_breakout_signal(chunk)
            headline_val = headline_signal(0.0)
            composite = vol_sig * 0.5 + headline_val * 0.5
            df.at[idx, "signal"] = composite if abs(composite) >= thresh else 0.0

        bt = run_backtest(df, df["signal"])
        metrics = compute_metrics(bt)
        results.append({**metrics, "mult": mult, "thresh": thresh})

    return pd.DataFrame(results).sort_values("sharpe_ratio", ascending=False)
