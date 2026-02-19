import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class RuntimeState:
    x: int = 827
    y: int = 975
    ctrl_press: bool = False
    paused: bool = False
    last_r_time: float = 0.0
    self_w: int = 0
    request_id: int = 0
    req_color: str = "黄"
    request_start_ts: float = 0.0
    active_last_update_ts: float = 0.0
    active_last_true_ts: float = 0.0


@dataclass
class LastLatency:
    request_id: int = 0
    req_color: str = ""
    w_start_ts: float = 0.0
    first_match_ts: Optional[float] = None
    key_send_ts: Optional[float] = None
    success: bool = False
    fail_reason: str = ""


@dataclass
class LatencyStats:
    total: int = 0
    success: int = 0
    failures: Dict[str, int] = field(default_factory=dict)
    last: LastLatency = field(default_factory=LastLatency)


class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self._state = RuntimeState()
        self._latency = LatencyStats()

    def get_xy(self) -> Tuple[int, int]:
        with self._lock:
            return self._state.x, self._state.y

    def set_xy(self, x: int, y: int) -> None:
        with self._lock:
            self._state.x = x
            self._state.y = y

    def is_paused(self) -> bool:
        with self._lock:
            return self._state.paused

    def toggle_paused(self) -> bool:
        with self._lock:
            self._state.paused = not self._state.paused
            return self._state.paused

    def set_ctrl_pressed(self, pressed: bool) -> None:
        with self._lock:
            self._state.ctrl_press = pressed

    def is_ctrl_pressed(self) -> bool:
        with self._lock:
            return self._state.ctrl_press

    def increment_self_w(self) -> None:
        with self._lock:
            self._state.self_w += 1

    def consume_self_w(self) -> bool:
        with self._lock:
            if self._state.self_w > 0:
                self._state.self_w -= 1
                return True
            return False

    def self_w_count(self) -> int:
        with self._lock:
            return self._state.self_w

    def register_request(self, color: str, now: float) -> int:
        with self._lock:
            self._state.request_id += 1
            self._state.req_color = color
            self._state.request_start_ts = now

            rid = self._state.request_id
            self._latency.last = LastLatency(
                request_id=rid,
                req_color=color,
                w_start_ts=now,
                first_match_ts=None,
                key_send_ts=None,
                success=False,
                fail_reason="",
            )
            return rid

    def get_request_snapshot(self) -> Tuple[int, str, float]:
        with self._lock:
            return self._state.request_id, self._state.req_color, self._state.request_start_ts

    def get_worker_snapshot_fast(self) -> Tuple[int, bool, int, int]:
        with self._lock:
            return self._state.request_id, self._state.paused, self._state.x, self._state.y

    def has_newer_request(self, request_id: int) -> bool:
        with self._lock:
            return self._state.request_id != request_id

    def update_first_match(self, request_id: int, ts: float) -> None:
        with self._lock:
            if self._latency.last.request_id == request_id and self._latency.last.first_match_ts is None:
                self._latency.last.first_match_ts = ts

    def update_key_send(self, request_id: int, ts: float) -> None:
        with self._lock:
            if self._latency.last.request_id == request_id:
                self._latency.last.key_send_ts = ts

    def record_result(self, request_id: int, success: bool, fail_reason: str = "") -> Optional[dict]:
        with self._lock:
            last = self._latency.last
            if last.request_id != request_id:
                return None

            self._latency.total += 1
            if success:
                self._latency.success += 1
                last.success = True
                last.fail_reason = ""
            else:
                last.success = False
                last.fail_reason = fail_reason
                self._latency.failures[fail_reason] = self._latency.failures.get(fail_reason, 0) + 1

            lock_latency_ms = None
            first_match_latency_ms = None
            if last.key_send_ts:
                lock_latency_ms = int((last.key_send_ts - last.w_start_ts) * 1000)
            if last.first_match_ts:
                first_match_latency_ms = int((last.first_match_ts - last.w_start_ts) * 1000)

            return {
                "req_color": last.req_color,
                "request_id": request_id,
                "success": success,
                "fail_reason": fail_reason,
                "lock_latency_ms": lock_latency_ms,
                "first_match_latency_ms": first_match_latency_ms,
            }

    def try_handle_r_press(self, now: float, threshold_sec: float) -> bool:
        with self._lock:
            last_r = self._state.last_r_time
            if now - last_r > threshold_sec:
                self._state.last_r_time = now
                return False
            self._state.last_r_time = 0.0
            return True

    def update_window_activity(self, is_active: bool, now: float) -> None:
        with self._lock:
            self._state.active_last_update_ts = now
            if is_active:
                self._state.active_last_true_ts = now

    def last_active_true_ts(self) -> float:
        with self._lock:
            return self._state.active_last_true_ts
