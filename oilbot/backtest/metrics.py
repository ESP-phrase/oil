import numpy as np
import pandas as pd


def compute_metrics(bt_df: pd.DataFrame) -> dict:
    equity = bt_df["equity"]
    strat_returns = bt_df["strategy_returns"].dropna()

    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
    n_days = len(bt_df)
    ann_return = (1 + total_return) ** (365 / n_days) - 1 if n_days > 0 else 0.0

    sharpe = np.nan
    if len(strat_returns) > 0 and strat_returns.std() != 0:
        sharpe = (strat_returns.mean() / strat_returns.std()) * np.sqrt(365 * 24)

    max_dd = bt_df["drawdown"].min()

    win_trades = []
    in_trade = False
    entry_equity = 0.0
    for _, row in bt_df.iterrows():
        pos = row.get("position", 0)
        if pos != 0 and not in_trade:
            entry_equity = row["equity"]
            in_trade = True
        elif pos == 0 and in_trade:
            win_trades.append(1 if row["equity"] > entry_equity else 0)
            in_trade = False
    win_rate = np.mean(win_trades) if win_trades else 0.0

    return {
        "total_return_pct": round(total_return * 100, 2),
        "annual_return_pct": round(ann_return * 100, 2),
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "win_rate_pct": round(win_rate * 100, 1),
        "num_trades": len(win_trades),
    }
