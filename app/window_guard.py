import threading
import time
from typing import Optional

import psutil
import win32gui
import win32process

from app.config import AppConfig
from app.state import SharedState


class WindowGuard:
    def __init__(self, config: AppConfig, state: SharedState):
        self._config = config
        self._state = state
        self._active_event = threading.Event()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_pid: Optional[int] = None
        self._last_name: str = ""
        self._last_check_ts: float = 0.0

    def _get_process_name_cached(self, pid: int, now: float) -> str:
        if (
            self._last_pid == pid
            and (now - self._last_check_ts) <= self._config.timing.window_pid_cache_ttl
        ):
            return self._last_name

        try:
            name = psutil.Process(pid).name()
        except psutil.NoSuchProcess:
            name = ""

        self._last_pid = pid
        self._last_name = name
        self._last_check_ts = now
        return name

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=0.5)

    def refresh_active_window_state(self) -> bool:
        is_active = False
        now = time.perf_counter()
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = self._get_process_name_cached(pid, now)
            is_active = process_name.lower() == self._config.target_process_name.lower()

        self._state.update_window_activity(is_active, now)

        if is_active:
            self._active_event.set()
        else:
            self._active_event.clear()

        return is_active

    def is_allowed(self) -> bool:
        if self._active_event.is_set():
            return True

        now = time.perf_counter()
        last_true_ts = self._state.last_active_true_ts()
        if now - last_true_ts <= self._config.timing.focus_recovery_window:
            return self.refresh_active_window_state()

        return False

    def _loop(self):
        while not self._stop_event.is_set():
            is_active = self.refresh_active_window_state()
            interval = (
                self._config.timing.window_poll_active_interval
                if is_active
                else self._config.timing.window_poll_inactive_interval
            )
            self._stop_event.wait(interval)
