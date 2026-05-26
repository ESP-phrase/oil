from datetime import datetime, timedelta
from typing import Optional

import requests
import numpy as np
import pandas as pd

from oilbot.config import NEWSAPI_KEY, HEADLINE_LOOKBACK_DAYS

IRAN_KEYWORDS = ["Iran", "Iranian", "Tehran", "IRGC", "oil", "crude", "sanctions",
                 "Strait of Hormuz", "OPEC", "war", "strike", "drone",
                 "missile", "nuclear", "refinery", "tanker"]

POSITIVE_WORDS = {"attack", "strike", "drone", "missile", "disruption",
                  "blockade", "sanctions", "surge", "spike"}
NEGATIVE_WORDS = {"ceasefire", "diplomacy", "talks", "truce", "de-escalation",
                  "calm", "stable"}

def fetch_iran_headlines(days: int = HEADLINE_LOOKBACK_DAYS) -> list[dict]:
    if not NEWSAPI_KEY:
        return []
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = (
        "https://newsapi.org/v2/everything"
        f"?q=Iran+oil&from={from_date}"
        f"&sortBy=publishedAt&language=en&pageSize=100"
        f"&apiKey={NEWSAPI_KEY}"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json().get("articles", [])

def compute_sentiment_score(articles: list[dict]) -> float:
    if not articles:
        return 0.0
    scores = []
    for a in articles:
        text = (a.get("title", "") + " " + (a.get("description", "") or "")).lower()
        pos = sum(1 for w in POSITIVE_WORDS if w in text)
        neg = sum(1 for w in NEGATIVE_WORDS if w in text)
        scores.append((pos - neg) / max(pos + neg, 1))
    return float(np.mean(scores))

def headline_intensity_score() -> float:
    articles = fetch_iran_headlines()
    if not articles:
        return 0.0
    intensities = []
    for a in articles:
        text = (a.get("title", "") + " " + (a.get("description", "") or "")).lower()
        intensities.append(sum(1 for kw in IRAN_KEYWORDS if kw.lower() in text))
    series = pd.Series(intensities)
    mean = series.mean()
    std = series.std() or 1.0
    latest = series.iloc[0]
    return (latest - mean) / std
