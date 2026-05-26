import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from oilbot.config import EIA_API_KEY, NEWSAPI_KEY, SYMBOLS
from oilbot.data.fetcher import fetch_ohlcv, fetch_eia_imports
from oilbot.data.news import headline_intensity_score, fetch_iran_headlines
from oilbot.strategy.composite import compute_composite_signal, should_trade

st.set_page_config(page_title="OilBot Dashboard", layout="wide")

st_autorefresh(interval=2_000, key="fastrefresh")

st.title("OilBot — Iran War Scenario Dashboard")


@st.cache_data(ttl=30)
def get_prices():
    return {key: fetch_ohlcv(key) for key in {"CL": "WTI Crude", "BZ": "Brent Crude", "RB": "RBOB Gas", "HO": "Heating Oil"}}


@st.cache_data(ttl=60)
def get_eia():
    if not EIA_API_KEY or "your_eia" in EIA_API_KEY:
        return pd.DataFrame()
    d = fetch_eia_imports()
    return d if d is not None and not d.empty else pd.DataFrame()


@st.cache_data(ttl=30)
def get_headlines():
    return fetch_iran_headlines(days=1)


@st.cache_data(ttl=30)
def get_headline_z():
    return headline_intensity_score()


prices = get_prices()

col1, col2, col3, col4 = st.columns(4)
symbol_labels = {"CL": "WTI Crude", "BZ": "Brent Crude", "RB": "RBOB Gas", "HO": "Heating Oil"}
for col, key in zip([col1, col2, col3, col4], symbol_labels):
    with col:
        df = prices.get(key)
        if df is not None and not df.empty:
            price = float(df["close"].iloc[-1])
            prev = float(df["close"].iloc[-2]) if len(df) > 1 else price
            change = price - prev
            pct = (change / prev) * 100 if prev else 0
            arrow = "▲" if change > 0 else "▼"
            st.metric(
                label=symbol_labels[key],
                value=f"${price:.2f}",
                delta=f"{arrow} ${abs(change):.2f} ({pct:+.2f}%)",
                delta_color="normal",
            )

# ── Signals Row ──────────────────────────────────────────
st.subheader("Composite Signal")
cl_df = prices.get("CL", pd.DataFrame())
eia_df = get_eia()
headline_z = get_headline_z()
pcr = 0.0

if cl_df is not None and not cl_df.empty:
    composite, signals = compute_composite_signal(cl_df, eia_df, headline_z, pcr)
    trade, direction = should_trade(composite)

    sig_cols = st.columns(len(signals) + 1)
    for i, (name, val) in enumerate(signals.items()):
        with sig_cols[i]:
            val_f = float(val)
            color = "#00c853" if val_f > 0.2 else "#ff1744" if val_f < -0.2 else "#ffc107"
            st.metric(label=name.replace("_", " ").title(), value=f"{val_f:+.2f}", delta_color="off")
            st.progress(min(abs(val_f), 1.0))

    with sig_cols[-1]:
        comp_color = "#00c853" if composite > 0.3 else "#ff1744" if composite < -0.3 else "#ffc107"
        st.markdown(
            f"<h3 style='color:{comp_color}; text-align:center;'>{'BUY' if composite > 0.3 else 'SELL' if composite < -0.3 else 'HOLD'}</h3>",
            unsafe_allow_html=True,
        )
        st.metric(label="Composite", value=f"{composite:+.3f}", delta_color="off")

    # ── Price Chart ──────────────────────────────────────────
    st.subheader("WTI Crude (CL=F) — Last 60 Days")
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
headlines = get_headlines()
if headlines:
    for a in headlines[:10]:
        title = a.get("title", "")
        url = a.get("url", "")
        source = a.get("source", {}).get("name", "")
        st.markdown(f"- [{title}]({url}) *({source})*")
else:
    st.info("Set NEWSAPI_KEY in .env to see headlines")

# ── Live PnL ─────────────────────────────────────────────
st.subheader("📊 Live PnL (updates every 2s)")
try:
    from oilbot.data.store import load_trades
    trades_df = load_trades(limit=20)
    if not trades_df.empty:
        current_price = float(cl_df["close"].iloc[-1]) if cl_df is not None and not cl_df.empty else 0
        live_pnl = 0.0
        open_pnl = 0.0
        realized_pnl = 0.0
        open_positions = []
        for _, t in trades_df.iterrows():
            pnl = t.get("pnl")
            entry = t.get("entry_price")
            qty = t.get("quantity", 0)
            direction = t.get("direction", "")
            exit_p = t.get("exit_price")
            if pd.notna(pnl) and pnl is not None:
                realized_pnl += float(pnl)
            elif pd.notna(exit_p) and exit_p is not None and pd.notna(entry):
                realized_pnl += float(exit_p - entry) * float(qty) if direction == "BUY" else float(entry - exit_p) * float(qty)
            elif pd.notna(entry) and current_price:
                p = float(current_price)
                e = float(entry)
                q = float(qty)
                upnl = (p - e) * q if direction == "SELL" else (e - p) * q
                open_pnl += upnl
                open_positions.append(f"{direction} {q:.0f} @ ${e:.2f}")

        live_pnl = realized_pnl + open_pnl
        total_trades = len(trades_df)
        wins = sum(1 for _, t in trades_df.iterrows() if pd.notna(t.get("pnl")) and float(t["pnl"]) > 0)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        col_a, col_b, col_c, col_d = st.columns(4)
        pnl_color = "normal" if live_pnl >= 0 else "inverse"
        col_a.metric("Open PnL", f"${open_pnl:.2f}", delta_color=pnl_color)
        col_b.metric("Realized PnL", f"${realized_pnl:.2f}", delta_color=pnl_color)
        col_c.metric("Total PnL", f"${live_pnl:.2f}", delta=f"{'▲' if live_pnl >= 0 else '▼'} ${abs(live_pnl):.2f}", delta_color=pnl_color)
        col_d.metric("Win Rate", f"{win_rate:.0f}%")

        if open_positions:
            for pos in open_positions:
                st.caption(f"Open: {pos}")

        st.dataframe(trades_df.drop(columns=["id"], errors="ignore"), width="stretch")
    else:
        st.info("No paper trades yet. Run `python -m oilbot.main` to start.")
except Exception as e:
    st.info(f"No trade history yet")

st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
