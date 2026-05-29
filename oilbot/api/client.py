import json
import os
import socket
from datetime import datetime, timezone

API_HOST = os.environ.get("OILBOT_API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("OILBOT_API_PORT", "5050"))

def _api_available():
    try:
        s = socket.create_connection((API_HOST, API_PORT), timeout=0.5)
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def post_trade(trade: dict):
    if not _api_available():
        return False
    import urllib.request
    data = json.dumps(trade).encode()
    req = urllib.request.Request(f"http://{API_HOST}:{API_PORT}/trade", data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False

def post_status(status: dict):
    if not _api_available():
        return False
    import urllib.request
    data = json.dumps(status).encode()
    req = urllib.request.Request(f"http://{API_HOST}:{API_PORT}/status", data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False

def post_signals(signals: dict):
    if not _api_available():
        return False
    import urllib.request
    data = json.dumps(signals).encode()
    req = urllib.request.Request(f"http://{API_HOST}:{API_PORT}/signals", data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False

def get_status() -> dict | None:
    if not _api_available():
        return None
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"http://{API_HOST}:{API_PORT}/status", timeout=2)
        return json.loads(resp.read())
    except Exception:
        return None

def get_trades() -> list:
    if not _api_available():
        return []
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"http://{API_HOST}:{API_PORT}/trades", timeout=2)
        return json.loads(resp.read())
    except Exception:
        return []
