import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime, timezone
import time as time_module

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from oilbot.config import EIA_API_KEY, NEWSAPI_KEY, SIGNAL_THRESHOLD
from oilbot.data.fetcher import fetch_ohlcv, fetch_eia_imports
from oilbot.data.news import headline_intensity_score, fetch_iran_headlines
from oilbot.strategy.composite import compute_composite_signal, should_trade
from oilbot.risk.position_sizer import size_position
from oilbot.api.client import get_status, get_trades

st.set_page_config(page_title="OilBot Dashboard", layout="wide")
st_autorefresh(interval=2_000, key="fastrefresh")

INITIAL_CAPITAL = 100_000.0

# ── Try to connect to local API ────────────────────────
api_status = get_status()
api_trades = get_trades()
using_api = api_status is not None

if "trader" not in st.session_state:
    st.session_state.trader = {
        "capital": INITIAL_CAPITAL,
        "position": 0,
        "entry_price": 0.0,
        "trades": [],
    }
if "last_eval" not in st.session_state:
    st.session_state.last_eval = 0.0
if "last_price_cache" not in st.session_state:
    st.session_state.last_price_cache = {}

st.title("OilBot — Iran War Scenario Dashboard")

if using_api:
    st.caption("Connected to local paper trader")
else:
    st.caption("Standalone mode (no local bot detected)")

# ── Fetch Data (cached per refresh cycle) ───────────────
@st.cache_data(ttl=30)
def get_price_data():
    result = {}
    labels = {"CL": "WTI Crude", "BZ": "Brent Crude", "RB": "RBOB Gas", "HO": "Heating Oil"}
    for key in labels:
        df = fetch_ohlcv(key)
        if df is not None and not df.empty:
            result[key] = df
    return result, labels

@st.cache_data(ttl=60)
def get_eia_data():
    if not EIA_API_KEY or "your_eia" in EIA_API_KEY:
        return pd.DataFrame()
    d = fetch_eia_imports()
    return d if d is not None and not d.empty else pd.DataFrame()

@st.cache_data(ttl=30)
def get_news_data():
    return fetch_iran_headlines(days=1), headline_intensity_score()

prices, symbol_labels = get_price_data()
eia_df = get_eia_data()
headlines, headline_z = get_news_data()
pcr = 0.0

# ── Evaluate signals every 5 min ────────────────────────
now = time_module.time()
trader = st.session_state.trader
cl_df = prices.get("CL", pd.DataFrame())
composite_val = 0.0
signal_dict = {}

if not cl_df.empty:
    composite_val, signal_dict = compute_composite_signal(cl_df, eia_df, headline_z, pcr)

    # Local mode: simulate trades in session state
    if not using_api and now - st.session_state.last_eval > 300:
        st.session_state.last_eval = now
        trade_flag, direction = should_trade(composite_val)
        if trade_flag:
            price = float(cl_df["close"].iloc[-1])
            conviction = abs(composite_val)
            qty = size_position(trader["capital"], price, conviction)

            if direction == "BUY" and trader["position"] <= 0:
                if trader["position"] < 0:
                    pnl = (trader["entry_price"] - price) * abs(trader["position"])
                    trader["capital"] += pnl
                    trader["trades"].append({
                        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "action": "COVER",
                        "qty": abs(trader["position"]),
                        "price": price,
                        "pnl": round(pnl, 2),
                    })
                trader["position"] = qty
                trader["entry_price"] = price
                trader["trades"].append({
                    "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "action": "BUY",
                    "qty": qty,
                    "price": price,
                    "pnl": "",
                })
            elif direction == "SELL" and trader["position"] >= 0:
                if trader["position"] > 0:
                    pnl = (price - trader["entry_price"]) * trader["position"]
                    trader["capital"] += pnl
                    trader["trades"].append({
                        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "action": "SELL",
                        "qty": trader["position"],
                        "price": price,
                        "pnl": round(pnl, 2),
                    })
                trader["position"] = -qty
                trader["entry_price"] = price
                trader["trades"].append({
                    "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "action": "SHORT",
                    "qty": qty,
                    "price": price,
                    "pnl": "",
                })
        st.session_state.trader = trader

# ── Use API data if available ────────────────────────────
if using_api:
    api_pos = api_status.get("position", 0)
    api_cap = api_status.get("capital", INITIAL_CAPITAL)
    api_entry = api_status.get("entry_price", 0.0)
else:
    api_pos = trader["position"]
    api_cap = trader["capital"]
    api_entry = trader["entry_price"]

trades_list = api_trades if using_api else trader["trades"]

# ── Price Cards ──────────────────────────────────────────
cols = st.columns(4)
for col, key in zip(cols, symbol_labels):
    df = prices.get(key)
    if df is not None and not df.empty:
        price = float(df["close"].iloc[-1])
        prev = float(df["close"].iloc[-2]) if len(df) > 1 else price
        change = price - prev
        pct = (change / prev) * 100 if prev else 0
        arrow = "▲" if change > 0 else "▼"
        col.metric(
            label=symbol_labels[key],
            value=f"${price:.2f}",
            delta=f"{arrow} ${abs(change):.2f} ({pct:+.2f}%)",
            delta_color="normal",
        )

# ── Signals Row ──────────────────────────────────────────
st.subheader("Composite Signal")
if signal_dict:
    sig_cols = st.columns(len(signal_dict) + 1)
    for i, (name, val) in enumerate(signal_dict.items()):
        val_f = float(val)
        with sig_cols[i]:
            color = "#00c853" if val_f > 0.2 else "#ff1744" if val_f < -0.2 else "#ffc107"
            st.metric(label=name.replace("_", " ").title(), value=f"{val_f:+.2f}", delta_color="off")
            st.progress(min(abs(val_f), 1.0))
    with sig_cols[-1]:
        comp = float(composite_val)
        label = "BUY" if comp > SIGNAL_THRESHOLD else "SELL" if comp < -SIGNAL_THRESHOLD else "HOLD"
        color = "#00c853" if label == "BUY" else "#ff1744" if label == "SELL" else "#ffc107"
        st.markdown(f"<h3 style='color:{color}; text-align:center;'>{label}</h3>", unsafe_allow_html=True)
        st.metric(label="Composite", value=f"{comp:+.3f}", delta_color="off")

# ── Price Chart ──────────────────────────────────────────
st.subheader("WTI Crude (CL=F) — Last 60 Days")
if not cl_df.empty:
    recent = cl_df.tail(1440)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent["close"],
        mode="lines", name="CL Close",
        line=dict(color="#1f77b4", width=2),
    ))
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), hovermode="x unified")
    st.plotly_chart(fig, width="stretch")

# ── EIA Imports ──────────────────────────────────────────
st.subheader("EIA Crude Oil Imports")
if eia_df is not None and not eia_df.empty:
    total = eia_df.groupby("period")["quantity"].sum().reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=total["period"], y=total["quantity"], name="Total Imports", marker_color="#4caf50"))
    if "originName" in eia_df.columns and "Iran" in eia_df["originName"].unique():
        iran = eia_df[eia_df["originName"].str.contains("Iran", case=False)]
        iran_total = iran.groupby("period")["quantity"].sum().reset_index()
        fig2.add_trace(go.Scatter(x=iran_total["period"], y=iran_total["quantity"], name="Iran Imports", mode="lines+markers", line=dict(color="#ff1744", width=2)))
    fig2.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig2, width="stretch")
else:
    st.info("Set EIA_API_KEY in .env to see import data")

# ── News Headlines ────────────────────────────────────────
st.subheader("Iran / Oil Headlines")
if headlines:
    for a in headlines[:10]:
        title = a.get("title", "")
        url = a.get("url", "")
        source = a.get("source", {}).get("name", "")
        st.markdown(f"- [{title}]({url}) *({source})*")
else:
    st.info("Set NEWSAPI_KEY in .env to see headlines")

# ── Live PnL ─────────────────────────────────────────────
st.subheader("Live PnL (updates every 2s)")
current_price = float(cl_df["close"].iloc[-1]) if not cl_df.empty else 0

if trades_list:
    realized = sum(float(t.get("pnl", 0) or 0) for t in trades_list if t.get("pnl") != "" and t.get("pnl") is not None)
    open_pnl = 0.0
    if api_pos != 0 and current_price:
        entry = api_entry
        pos = api_pos
        open_pnl = (current_price - entry) * pos if pos > 0 else (entry - current_price) * abs(pos)
    total_pnl = realized + open_pnl
    wins = sum(1 for t in trades_list if t.get("pnl") not in ("", None, 0) and float(t.get("pnl", 0) or 0) > 0)
    total_closed = sum(1 for t in trades_list if t.get("pnl") not in ("", None))
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Open PnL", f"${open_pnl:.2f}")
    col_b.metric("Realized PnL", f"${realized:.2f}")
    col_c.metric("Total PnL", f"${total_pnl:.2f}")
    col_d.metric("Win Rate", f"{win_rate:.0f}%")

    pos_label = f"Long {api_pos}" if api_pos > 0 else f"Short {abs(api_pos)}" if api_pos < 0 else "Flat"
    st.caption(f"Position: {pos_label} CL @ ${api_entry:.2f} | Capital: ${api_cap:.2f}")

    df_trades = pd.DataFrame(trades_list)
    st.dataframe(df_trades, width="stretch")
else:
    st.info("No trades yet. Waiting for signal threshold to be crossed.")

st.caption(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
