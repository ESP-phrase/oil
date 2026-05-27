import numpy as np
import pandas as pd
from scipy import stats

from oilbot.config import (
    VOLATILITY_LOOKBACK,
    VOLATILITY_BREAKOUT_MULTIPLIER,
    INVENTORY_STD_THRESHOLD,
)

def volatility_breakout_signal(df: pd.DataFrame) -> float:
    if df.empty or len(df) < VOLATILITY_LOOKBACK + 5:
        return 0.0
    atr_short = _atr(df, 5)
    atr_long = _atr(df, VOLATILITY_LOOKBACK)
    latest_short = atr_short.iloc[-1]
    latest_long = atr_long.iloc[-1]
    if latest_long == 0:
        return 0.0
    ratio = latest_short / latest_long
    if ratio > VOLATILITY_BREAKOUT_MULTIPLIER:
        return min((ratio - 1.0) / 2.0, 1.0)
    return 0.0

def eia_import_surprise_signal(eia_df: pd.DataFrame) -> float:
    if eia_df.empty:
        return 0.0
    total_by_month = eia_df.groupby("period")["quantity"].sum()
    changes = total_by_month.diff().dropna().values
    if len(changes) < 2:
        return 0.0
    mean = np.mean(changes)
    std = np.std(changes, ddof=1) or 1.0
    zscore = (changes[-1] - mean) / std
    if abs(zscore) < INVENTORY_STD_THRESHOLD:
        return 0.0
    return np.clip(zscore / 3.0, -1.0, 1.0)

def eia_iran_import_signal(eia_df: pd.DataFrame) -> float:
    if eia_df.empty or "originName" not in eia_df.columns:
        return 0.0
    iran = eia_df[eia_df["originName"].str.contains("Iran", case=False, na=False)]
    if iran.empty:
        return 0.0
    total = eia_df.groupby("period")["quantity"].sum()
    iran_total = iran.groupby("period")["quantity"].sum()
    share = (iran_total / total).dropna()
    if len(share) < 2:
        return 0.0
    latest = share.iloc[-1]
    avg = share.iloc[:-1].mean()
    if avg == 0:
        return 0.0
    ratio = latest / avg
    if ratio > 1.2:
        return -1.0    # Iran imports rising → Iran war risk bearish for oil prices? Actually, more Iran oil = supply = bearish
    if ratio < 0.8:
        return 1.0     # Iran imports dropping → supply tightening = bullish
    return 0.0

def put_call_ratio_signal(pcr: float) -> float:
    if pcr <= 0:
        return 0.0
    if pcr < 0.4:
        return 1.0     # extreme fear → bullish
    if pcr > 0.8:
        return -1.0    # extreme greed → bearish
    return 0.0

def headline_signal(headline_score: float) -> float:
    return max(-1.0, min(1.0, headline_score))

def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()
