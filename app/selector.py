import threading
import time
from typing import Callable, Optional

from app.color_detector import ColorDetector
from app.config import AppConfig
from app.state import SharedState
from app.window_guard import WindowGuard


class Selector:
    def __init__(
        self,
        config: AppConfig,
        state: SharedState,
        color_detector: ColorDetector,
        window_guard: WindowGuard,
        click_w: Callable[[bool, Optional[int]], None],
        debug_log: Callable[[str, str], None],
        on_result: Optional[Callable[[dict], None]] = None,
    ):
        self._config = config
        self._state = state
        self._color_detector = color_detector
        self._window_guard = window_guard
        self._click_w = click_w
        self._debug_log = debug_log
        self._on_result = on_result
        self._selector_event = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)

    def start(self):
        self._worker.start()

    def submit(self, color: str) -> int:
        self._click_w(False, None)
        now = time.perf_counter()
        request_id = self._state.register_request(color, now)
        self._selector_event.set()
        self._debug_log("submit", f"提交请求 req={request_id} color={color}")
        return request_id

    def _worker_loop(self):
        while True:
            self._selector_event.wait()

            while True:
                self._selector_event.clear()
                request_id, req_color, request_start_ts = self._state.get_request_snapshot()
                if request_id == 0:
                    break

                deadline = request_start_ts + self._config.timing.select_timeout
                saw_single_match = False
                extended_once = False
                consecutive_match_count = 0
                poll_interval = self._config.timing.card_poll_interval

                while True:
                    active_request_id, paused, px, py = self._state.get_worker_snapshot_fast()
                    if active_request_id != request_id:
                        self._debug_log("worker", f"请求被覆盖 old={request_id} new={active_request_id}")
                        break

                    if paused:
                        self._log_result(self._state.record_result(request_id, False, "paused"))
                        break

                    if not self._window_guard.is_allowed():
                        self._log_result(self._state.record_result(request_id, False, "inactive_window"))
                        break

                    now = time.perf_counter()
                    if now - request_start_ts < self._config.timing.animation_grace:
                        time.sleep(poll_interval)
                        continue

                    if self._color_detector.match_target_fast(px, py, req_color):
                        consecutive_match_count += 1
                        saw_single_match = True
                        poll_interval = self._config.timing.card_poll_fast_interval
                        self._state.update_first_match(request_id, now)

                        if consecutive_match_count >= self._config.timing.match_confirm_frames:
                            self._click_w(True, request_id)
                            self._log_result(self._state.record_result(request_id, True))
                            break
                    else:
                        consecutive_match_count = 0
                        poll_interval = self._config.timing.card_poll_interval

                    if now >= deadline:
                        if saw_single_match and not extended_once:
                            deadline = now + self._config.timing.partial_match_grace
                            extended_once = True
                            self._debug_log(
                                "worker",
                                f"请求宽限 req={request_id} grace={self._config.timing.partial_match_grace}s",
                            )
                        else:
                            reason = "timeout_no_confirm" if saw_single_match else "timeout_no_match"
                            self._log_result(self._state.record_result(request_id, False, reason))
                            break

                    time.sleep(poll_interval)

                if not self._state.has_newer_request(request_id):
                    break

    def _log_result(self, result):
        if result is None:
            return

        if self._on_result is not None:
            self._on_result(result)

        if result["success"]:
            print(
                f"抽牌成功 color={result['req_color']} req={result['request_id']} "
                f"first_match={result['first_match_latency_ms']}ms lock={result['lock_latency_ms']}ms"
            )
        else:
            print(
                f"抽牌失败 color={result['req_color']} req={result['request_id']} reason={result['fail_reason']} "
                f"first_match={result['first_match_latency_ms']}ms"
            )
