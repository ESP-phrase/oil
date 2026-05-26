import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from oilbot.config import EIA_API_KEY, NEWSAPI_KEY, SYMBOLS
from oilbot.data.fetcher import fetch_ohlcv, fetch_eia_imports
from oilbot.data.news import headline_intensity_score, fetch_iran_headlines
from oilbot.strategy.composite import compute_composite_signal, should_trade

st.set_page_config(page_title="OilBot Dashboard", layout="wide")

st_autorefresh(interval=60_000, key="refresh")

st.title("OilBot — Iran War Scenario Dashboard")

# ── Price Cards ──────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
symbols = {"CL": "WTI Crude", "BZ": "Brent Crude", "RB": "RBOB Gas", "HO": "Heating Oil"}

for col, key in zip([col1, col2, col3, col4], symbols):
    with col:
        df = fetch_ohlcv(key)
        if not df.empty:
            price = float(df["close"].iloc[-1])
            prev = float(df["close"].iloc[-2]) if len(df) > 1 else price
            change = price - prev
            pct = (change / prev) * 100 if prev else 0
            arrow = "▲" if change > 0 else "▼"
            color = "#00c853" if change > 0 else "#ff1744"
            st.metric(
                label=symbols[key],
                value=f"${price:.2f}",
                delta=f"{arrow} ${abs(change):.2f} ({pct:+.2f}%)",
                delta_color="normal",
            )

# ── Signals Row ──────────────────────────────────────────
st.subheader("Composite Signal")

cl_df = fetch_ohlcv("CL")
eia_df = fetch_eia_imports() if EIA_API_KEY and "your_eia" not in EIA_API_KEY else pd.DataFrame()
if eia_df is None or eia_df.empty:
    eia_df = pd.DataFrame()
headline_z = headline_intensity_score()
pcr = 0.0

composite, signals = compute_composite_signal(cl_df, eia_df, headline_z, pcr)
trade, direction = should_trade(composite)

sig_cols = st.columns(len(signals) + 1)
for i, (name, val) in enumerate(signals.items()):
    with sig_cols[i]:
        color = "#00c853" if val > 0.2 else "#ff1744" if val < -0.2 else "#ffc107"
        st.metric(label=name.replace("_", " ").title(), value=f"{val:+.2f}", delta_color="off")
        st.progress(min(abs(val), 1.0))

with sig_cols[-1]:
    comp_color = "#00c853" if composite > 0.3 else "#ff1744" if composite < -0.3 else "#ffc107"
    st.markdown(
        f"<h3 style='color:{comp_color}; text-align:center;'>{'BUY' if composite > 0.3 else 'SELL' if composite < -0.3 else 'HOLD'}</h3>",
        unsafe_allow_html=True,
    )
    st.metric(label="Composite", value=f"{composite:+.3f}", delta_color="off")

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
    fig.update_layout(
        height=400, margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title=None, yaxis_title="Price ($)",
        hovermode="x unified",
    )
    st.plotly_chart(fig, width="stretch")

# ── EIA Imports ──────────────────────────────────────────
st.subheader("EIA Crude Oil Imports")
if eia_df is not None and not eia_df.empty:
    total = eia_df.groupby("period")["quantity"].sum().reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=total["period"], y=total["quantity"],
        name="Total Imports", marker_color="#4caf50",
    ))
    if "originName" in eia_df.columns and "Iran" in eia_df["originName"].unique():
        iran = eia_df[eia_df["originName"].str.contains("Iran", case=False)]
        iran_total = iran.groupby("period")["quantity"].sum().reset_index()
        fig2.add_trace(go.Scatter(
            x=iran_total["period"], y=iran_total["quantity"],
            name="Iran Imports", mode="lines+markers",
            line=dict(color="#ff1744", width=2),
        ))
    fig2.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig2, width="stretch")
else:
    st.info("Set EIA_API_KEY in .env to see import data")

# ── News Headlines ────────────────────────────────────────
st.subheader("Iran / Oil Headlines")
headlines = fetch_iran_headlines(days=1)
if headlines:
    for a in headlines[:10]:
        title = a.get("title", "")
        url = a.get("url", "")
        source = a.get("source", {}).get("name", "")
        st.markdown(f"- [{title}]({url}) *({source})*")
else:
    st.info("Set NEWSAPI_KEY in .env to see headlines")

# ── Paper Trading Portfolio ───────────────────────────────
st.subheader("Paper Trading")
try:
    from oilbot.data.store import load_trades
    trades_df = load_trades(limit=20)
    if not trades_df.empty:
        total_pnl = trades_df["pnl"].sum() if "pnl" in trades_df.columns else 0
        win_rate = (trades_df["pnl"] > 0).mean() * 100 if "pnl" in trades_df.columns else 0
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total PnL", f"${total_pnl:.2f}")
        col_b.metric("Win Rate", f"{win_rate:.0f}%")
        col_c.metric("Trades", len(trades_df))
        st.dataframe(trades_df.drop(columns=["id"], errors="ignore"), width="stretch")
    else:
        st.info("No paper trades yet. Run `python main.py` to start.")
except Exception as e:
    st.info(f"No trade history yet")

st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
