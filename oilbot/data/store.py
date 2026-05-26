import pandas as pd
from sqlalchemy import create_engine, text
from oilbot.config import DB_PATH

_engine = create_engine(f"sqlite:///{DB_PATH}")

def init_db():
    with _engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                symbol TEXT,
                timestamp TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (symbol, timestamp)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS signals (
                timestamp TEXT,
                signal_name TEXT,
                value REAL,
                PRIMARY KEY (timestamp, signal_name)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                direction TEXT,
                quantity REAL,
                entry_price REAL,
                exit_price REAL,
                exit_timestamp TEXT,
                pnl REAL,
                reason TEXT
            )
        """))

def save_ohlcv(symbol: str, df: pd.DataFrame):
    if df.empty:
        return
    df = df.reset_index().copy()
    df["symbol"] = symbol
    records = []
    for _, row in df.iterrows():
        records.append({
            "ts": str(row["timestamp"]),
            "o": float(row["open"]),
            "h": float(row["high"]),
            "l": float(row["low"]),
            "c": float(row["close"]),
            "v": int(row["volume"]),
            "sym": symbol,
        })
    with _engine.begin() as conn:
        conn.execute(
            text("""INSERT OR REPLACE INTO ohlcv
                (timestamp, open, high, low, close, volume, symbol)
                VALUES (:ts, :o, :h, :l, :c, :v, :sym)"""),
            records,
        )

def load_ohlcv(symbol: str) -> pd.DataFrame:
    return pd.read_sql(
        f"SELECT * FROM ohlcv WHERE symbol = '{symbol}' ORDER BY timestamp",
        _engine, index_col="timestamp", parse_dates=["timestamp"]
    )

def save_signal(name: str, value: float):
    import datetime
    with _engine.begin() as conn:
        conn.execute(
            text("INSERT OR REPLACE INTO signals (timestamp, signal_name, value) VALUES (:ts, :name, :val)"),
            {"ts": datetime.datetime.utcnow().isoformat(), "name": name, "val": value},
        )

def save_trade(trade: dict):
    pd.DataFrame([trade]).to_sql("trades", _engine, if_exists="append", index=False)

def load_trades(limit: int = 20) -> pd.DataFrame:
    return pd.read_sql(
        f"SELECT * FROM trades ORDER BY timestamp DESC LIMIT {limit}",
        _engine,
    )
