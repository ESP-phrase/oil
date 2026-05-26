from datetime import datetime, timedelta
from typing import Optional

from oilbot.config import DAILY_MAX_LOSS_PCT, COOLDOWN_MINUTES


class KillSwitch:
    def __init__(self):
        self._day_start_equity: Optional[float] = None
        self._current_equity: Optional[float] = None
        self._last_stop_time: Optional[datetime] = None
        self._stopped = False

    def update_equity(self, equity: float):
        now = datetime.utcnow()
        if self._day_start_equity is None:
            self._day_start_equity = equity
        self._current_equity = equity
        if self._stopped:
            if self._last_stop_time and (now - self._last_stop_time).total_seconds() > 86400:
                self._stopped = False
                self._day_start_equity = equity
        if self._day_start_equity and self._day_start_equity > 0:
            loss_pct = (self._day_start_equity - equity) / self._day_start_equity
            if loss_pct >= DAILY_MAX_LOSS_PCT:
                self._stopped = True
                self._last_stop_time = now

    @property
    def is_stopped(self) -> bool:
        return self._stopped

    def in_cooldown(self) -> bool:
        if self._last_stop_time is None:
            return False
        elapsed = (datetime.utcnow() - self._last_stop_time).total_seconds()
        return elapsed < COOLDOWN_MINUTES * 60

    def reset_day(self, equity: float):
        self._day_start_equity = equity
        self._stopped = False
