import json
import os
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "api_state.json")

_lock = threading.Lock()

def _read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"trades": [], "status": {"capital": 100000.0, "position": 0, "entry_price": 0.0, "pnl": 0.0}, "signals": {}}

def _write_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            state = _read_state()
            self._json(state["status"])
        elif self.path == "/trades":
            state = _read_state()
            self._json(state["trades"])
        elif self.path == "/signals":
            state = _read_state()
            self._json(state["signals"])
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        data = json.loads(body) if body else {}
        with _lock:
            state = _read_state()
            if self.path == "/trade":
                state["trades"].append(data)
            elif self.path == "/status":
                state["status"].update(data)
            elif self.path == "/signals":
                state["signals"].update(data)
            _write_state(state)
        self._json({"ok": True})

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, fmt, *args):
        pass

def start_server(host="0.0.0.0", port=5050):
    server = HTTPServer((host, port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server
