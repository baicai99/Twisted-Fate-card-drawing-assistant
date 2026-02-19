import time
from typing import Optional

from app.color_detector import ColorDetector
from app.config import load_config
from app.input_backend import PynputBackend
from app.input_handlers import InputHandlers
from app.selector import Selector
from app.state import SharedState
from app.win_input import sendkey
from app.window_guard import WindowGuard


def build_debug_logger(enabled: bool, throttle_sec: float):
    last_ts = {}

    def debug_log(bucket: str, message: str):
        if not enabled:
            return
        now = time.time()
        if now - last_ts.get(bucket, 0.0) >= throttle_sec:
            print(message)
            last_ts[bucket] = now

    return debug_log


def build_perf_collector(enabled: bool, report_every: int):
    stats = {
        "count": 0,
        "success": 0,
        "failures": {},
        "lock_ms": [],
    }

    def on_result(result: dict):
        if not enabled:
            return

        stats["count"] += 1
        if result.get("success"):
            stats["success"] += 1
        else:
            reason = result.get("fail_reason", "unknown")
            stats["failures"][reason] = stats["failures"].get(reason, 0) + 1

        lock_ms = result.get("lock_latency_ms")
        if lock_ms is not None:
            stats["lock_ms"].append(lock_ms)

        if stats["count"] % report_every != 0:
            return

        lock_sorted = sorted(stats["lock_ms"])
        if lock_sorted:
            p50 = lock_sorted[len(lock_sorted) // 2]
            p95 = lock_sorted[int(len(lock_sorted) * 0.95)]
            avg = int(sum(lock_sorted) / len(lock_sorted))
        else:
            p50 = p95 = avg = None

        success_rate = (stats["success"] / stats["count"]) * 100.0
        print(
            "[perf] total={total} success_rate={rate:.1f}% lock_avg={avg}ms lock_p50={p50}ms lock_p95={p95}ms failures={failures}".format(
                total=stats["count"],
                rate=success_rate,
                avg=avg,
                p50=p50,
                p95=p95,
                failures=stats["failures"],
            )
        )

    return on_result


def main():
    config = load_config()
    state = SharedState()
    debug_log = build_debug_logger(config.debug_enabled, config.log_throttle_sec)
    perf_collector = build_perf_collector(config.perf_stats_enabled, config.perf_stats_report_every)

    color_detector = ColorDetector(
        config.colors,
        config.timing.double_sample_gap,
        sample_radius_px=config.timing.sample_radius_px,
        sample_min_hits=config.timing.sample_min_hits,
    )
    window_guard = WindowGuard(config, state)

    def click_w(is_lock_press: bool = False, request_id: Optional[int] = None):
        sendkey(0x11, 1)
        sendkey(0x11, 0)
        if is_lock_press and request_id is not None:
            state.update_key_send(request_id, time.perf_counter())

    selector = Selector(
        config=config,
        state=state,
        color_detector=color_detector,
        window_guard=window_guard,
        click_w=click_w,
        debug_log=debug_log,
        on_result=perf_collector,
    )

    handlers = InputHandlers(
        config=config,
        state=state,
        selector=selector,
        window_guard=window_guard,
        color_detector=color_detector,
    )

    handlers.load_coordinates()
    window_guard.start()
    selector.start()

    print("一切尽在卡牌中！光速抽牌，已经启动：E：黄牌，W：蓝牌，A：红牌，大招自动黄牌")
    x, y = state.get_xy()
    print("按下 鼠标中间滑轮按键 确定卡牌取色位置，当前位置：", x, y)
    print("按下 回车键 可暂停/恢复 功能")
    print(f'只有当进程名称为 "{config.target_process_name}" 时，功能才会激活')
    print(f"输入后端: {config.input_backend}")

    backend = PynputBackend(
        on_key_down=handlers.on_key_down,
        on_key_up=handlers.on_key_up,
        on_middle_click=handlers.on_middle_click,
        should_suppress_key=handlers.should_suppress_key,
        debug=config.debug_enabled,
    )
    backend.start()


if __name__ == "__main__":
    main()
