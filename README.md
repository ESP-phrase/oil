# OilBot — Iran War Scenario Trading Dashboard

Oil trading bot focused on crude oil (CL) during the Iran conflict, with signal generation from volatility breakouts, EIA import data, and news sentiment.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in API keys
python -m oilbot.main  # paper trading bot
streamlit run oilbot/dashboard/app.py  # dashboard
```

## Signals
- Volatility breakout (ATR ratio)
- EIA crude oil import surprise
- Iran import share
- News headline intensity
- Put/call ratio (USO)

## Deployment
Deployed on Streamlit Community Cloud.
