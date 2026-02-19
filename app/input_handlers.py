import os
import time
from typing import Callable

from app.color_detector import ColorDetector
from app.config import AppConfig
from app.selector import Selector
from app.state import SharedState
from app.window_guard import WindowGuard


class InputHandlers:
    def __init__(
        self,
        config: AppConfig,
        state: SharedState,
        selector: Selector,
        window_guard: WindowGuard,
        color_detector: ColorDetector,
    ):
        self._config = config
        self._state = state
        self._selector = selector
        self._window_guard = window_guard
        self._color_detector = color_detector

    def load_coordinates(self):
        path = self._config.coordinate_file
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = f.read().split(",")
                if len(data) == 2:
                    x, y = int(data[0]), int(data[1])
                    self._state.set_xy(x, y)
                    print(f"已从文件加载取色坐标：{x}, {y}")
                    return
                print("坐标文件格式错误，使用默认坐标")
            except Exception as exc:
                print(f"加载坐标时发生错误：{exc}，使用默认坐标")
        else:
            print("未找到坐标文件，使用默认坐标")

    def save_coordinates(self):
        try:
            x, y = self._state.get_xy()
            with open(self._config.coordinate_file, "w", encoding="utf-8") as f:
                f.write(f"{x},{y}")
            print(f"已将取色坐标保存到文件：{x}, {y}")
        except Exception as exc:
            print(f"保存坐标时发生错误：{exc}")

    def should_allow_action(self) -> bool:
        if self._state.is_paused():
            return False
        return self._window_guard.is_allowed()

    def on_key_down(self, event):
        key = event.Key

        if key == "Return":
            paused_now = self._state.toggle_paused()
            print("功能已暂停" if paused_now else "功能已恢复")
            return True

        if not self.should_allow_action():
            return True

        if key in ("Lcontrol", "Rcontrol"):
            self._state.set_ctrl_pressed(True)
            return True

        if self._state.is_ctrl_pressed():
            return True

        if key == "E":
            self._selector.submit("黄", open_cycle=True)
        elif key == "W":
            if getattr(event, "is_injected", False):
                return True
            self._selector.submit("蓝", open_cycle=False)
        elif key == "A":
            self._selector.submit("红", open_cycle=True)
        elif key == "R":
            now = time.time()
            if self._state.try_handle_r_press(now, self._config.timing.r_double_press_gap):
                self._selector.submit("黄", open_cycle=True)

        return True

    def on_key_up(self, event):
        key = event.Key
        if key in ("Lcontrol", "Rcontrol"):
            self._state.set_ctrl_pressed(False)
        return True

    def on_middle_click(self, event):
        if not self.should_allow_action():
            return True

        x, y = event.Position[0], event.Position[1]
        self._state.set_xy(x, y)

        r, g, b = self._color_detector.get_rgb(x, y)
        print("当前取色坐标：", x, y, "祝您游戏愉快")
        print("当前颜色：", self._color_detector.get_color_name(r, g, b))
        self.save_coordinates()
        return True

    def should_suppress_key(self, key_name: str, is_injected: bool) -> bool:
        _ = (key_name, is_injected)
        return False
