import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimingConfig:
    window_poll_active_interval: float = 0.012
    window_poll_inactive_interval: float = 0.09
    window_pid_cache_ttl: float = 0.2
    card_poll_interval: float = 0.008
    card_poll_fast_interval: float = 0.004
    animation_grace: float = 0.0
    match_confirm_frames: int = 2
    select_timeout: float = 1.2
    partial_match_grace: float = 0.08
    focus_recovery_window: float = 0.05
    double_sample_gap: float = 0.0015
    sample_radius_px: int = 1
    sample_min_hits: int = 2
    r_double_press_gap: float = 8.0


@dataclass(frozen=True)
class ColorThresholds:
    yellow_min_r: int = 160
    yellow_min_g: int = 145
    yellow_max_b: int = 120

    blue_max_r: int = 130
    blue_max_g: int = 170
    blue_min_b: int = 145

    red_min_r: int = 155
    red_max_g: int = 130
    red_max_b: int = 130


@dataclass(frozen=True)
class AppConfig:
    coordinate_file: str = "color_coordinates.txt"
    target_process_name: str = "League of Legends.exe"
    debug_enabled: bool = False
    log_throttle_sec: float = 0.2
    perf_stats_enabled: bool = False
    perf_stats_report_every: int = 200
    input_backend: str = "pynput"
    timing: TimingConfig = field(default_factory=TimingConfig)
    colors: ColorThresholds = field(default_factory=ColorThresholds)


def load_config() -> AppConfig:
    backend = os.getenv("TF_INPUT_BACKEND", "pynput").strip().lower()
    if backend != "pynput":
        if backend == "legacy":
            print("TF_INPUT_BACKEND=legacy 已弃用，自动回退到 pynput")
        else:
            print(f"未知输入后端: {backend}，自动回退到 pynput")
        backend = "pynput"

    perf_stats_enabled = os.getenv("TF_PERF_STATS", "0").strip() in ("1", "true", "TRUE", "yes", "on")
    return AppConfig(
        input_backend=backend,
        perf_stats_enabled=perf_stats_enabled,
    )
