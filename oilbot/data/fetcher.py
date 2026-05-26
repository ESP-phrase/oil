import pandas as pd
import yfinance as yf
from oilbot.config import SYMBOLS, YAHOO_PERIOD, YAHOO_INTERVAL

def fetch_ohlcv(symbol_key: str) -> pd.DataFrame:
    ticker = SYMBOLS[symbol_key]
    df = yf.download(ticker, period=YAHOO_PERIOD, interval=YAHOO_INTERVAL, auto_adjust=True, progress=False)
    if df.empty:
        return df
    cols = []
    for c in df.columns:
        if isinstance(c, tuple):
            cols.append(c[0].lower())
        else:
            cols.append(c.lower())
    df.columns = cols
    df.index.name = "timestamp"
    expected = {"open", "high", "low", "close", "volume"}
    if not expected.issubset(df.columns):
        df.columns = ["open", "high", "low", "close", "volume"][: len(df.columns)]
    return df

def fetch_all_ohlcv() -> dict[str, pd.DataFrame]:
    return {key: fetch_ohlcv(key) for key in SYMBOLS}

def fetch_eia_imports() -> pd.DataFrame:
    import requests
    from oilbot.config import EIA_API_KEY
    url = (
        "https://api.eia.gov/v2/crude-oil-imports/data/"
        f"?api_key={EIA_API_KEY}"
        "&frequency=monthly"
        "&data[0]=quantity"
        "&sort[0][column]=period"
        "&sort[0][direction]=desc"
        "&offset=0&length=5000"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    records = resp.json()["response"]["data"]
    df = pd.DataFrame(records)
    df["period"] = pd.to_datetime(df["period"])
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    return df.sort_values("period").reset_index(drop=True)

def fetch_eia_inventory() -> pd.DataFrame:
    import warnings
    warnings.warn("fetch_eia_inventory is deprecated, use fetch_eia_imports", DeprecationWarning, stacklevel=2)
    return fetch_eia_imports()
