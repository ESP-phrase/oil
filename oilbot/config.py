import os
from dotenv import load_dotenv

load_dotenv()

# ── Symbols ──────────────────────────────────────────────
SYMBOLS = {
    "CL": "CL=F",      # WTI Crude Oil
    "BZ": "BZ=F",      # Brent Crude Oil
    "RB": "RB=F",      # RBOB Gasoline
    "HO": "HO=F",      # Heating Oil
    "USO": "USO",      # USO ETF (for options/PCR)
}

# ── Data ─────────────────────────────────────────────────
YAHOO_PERIOD = "2y"
YAHOO_INTERVAL = "1h"

EIA_API_KEY = os.getenv("EIA_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

DB_PATH = os.getenv("OILBOT_DB", "oilbot.db")

# ── Strategy weights ─────────────────────────────────────
SIGNAL_WEIGHTS = {
    "volatility_breakout": 0.25,
    "iran_headline_intensity": 0.25,
    "eia_import_surprise": 0.20,
    "eia_iran_import": 0.15,
    "put_call_ratio": 0.15,
}

SIGNAL_THRESHOLD = 0.5   # absolute composite score to trigger
HEADLINE_LOOKBACK_DAYS = 30
VOLATILITY_LOOKBACK = 20
VOLATILITY_BREAKOUT_MULTIPLIER = 2.0
INVENTORY_STD_THRESHOLD = 1.0

# ── Risk ─────────────────────────────────────────────────
MAX_POSITION_PCT = 0.02        # 2% of capital per trade
DAILY_MAX_LOSS_PCT = 0.03     # 3% → kill switch
STOP_LOSS_ATR_MULTIPLIER = 2.5
COOLDOWN_MINUTES = 60
FLATTEN_BEFORE_FRIDAY_CLOSE = True

# ── Backtest ─────────────────────────────────────────────
SLIPPAGE_TICKS = 2
COMMISSION_PER_SIDE = 2.50     # IBKR micros
INITIAL_CAPITAL = 100_000.0

# ── Execution ────────────────────────────────────────────
IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IBKR_PORT", "7497"))    # 7497 = paper, 7496 = live
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "1"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
