import platform
import threading
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from pynput import keyboard, mouse

KeyCallback = Callable[["InputEvent"], bool]
MouseCallback = Callable[["InputEvent"], bool]
SuppressCallback = Callable[[str, bool], bool]

LLKHF_INJECTED = 0x10
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104


@dataclass
class InputEvent:
    type: str
    key: Optional[str] = None
    position: Optional[Tuple[int, int]] = None
    is_injected: bool = False

    @property
    def Key(self):
        return self.key

    @property
    def Position(self):
        return self.position


class InputBackend:
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


class PynputBackend(InputBackend):
    def __init__(
        self,
        on_key_down: KeyCallback,
        on_key_up: KeyCallback,
        on_middle_click: MouseCallback,
        should_suppress_key: Optional[SuppressCallback] = None,
        debug: bool = False,
    ):
        self.on_key_down = on_key_down
        self.on_key_up = on_key_up
        self.on_middle_click = on_middle_click
        self.should_suppress_key = should_suppress_key or (lambda _key, _inj: False)
        self.debug = debug

        self._keyboard_listener = None
        self._mouse_listener = None
        self._stop_event = threading.Event()
        self._is_windows = platform.system().lower().startswith("win")
        self._vk_injected = {}

    def _normalize_key(self, key) -> Optional[str]:
        if isinstance(key, keyboard.KeyCode):
            if key.char:
                return key.char.upper()
            return None

        mapping = {
            keyboard.Key.enter: "Return",
            keyboard.Key.ctrl_l: "Lcontrol",
            keyboard.Key.ctrl_r: "Rcontrol",
        }
        return mapping.get(key)

    def _vk_from_key(self, key) -> Optional[int]:
        if isinstance(key, keyboard.KeyCode):
            return key.vk
        vk_map = {
            keyboard.Key.ctrl_l: 0xA2,
            keyboard.Key.ctrl_r: 0xA3,
            keyboard.Key.enter: 0x0D,
        }
        return vk_map.get(key)

    def _build_key_event(self, event_type: str, key) -> Optional[InputEvent]:
        key_name = self._normalize_key(key)
        if key_name is None:
            return None

        vk = self._vk_from_key(key)
        is_injected = False
        if vk is not None:
            is_injected = self._vk_injected.pop(vk, False)

        return InputEvent(type=event_type, key=key_name, is_injected=is_injected)

    def _on_press(self, key):
        event = self._build_key_event("key_down", key)
        if event is None:
            return
        self.on_key_down(event)

    def _on_release(self, key):
        event = self._build_key_event("key_up", key)
        if event is None:
            return
        self.on_key_up(event)

    def _on_click(self, x, y, button, pressed):
        if button == mouse.Button.middle and pressed:
            self.on_middle_click(InputEvent(type="mouse_middle_down", position=(x, y)))

    def _win32_event_filter(self, msg, data):
        is_key_down = msg in (WM_KEYDOWN, WM_SYSKEYDOWN)
        if not is_key_down:
            return

        vk = data.vkCode
        is_injected = bool(data.flags & LLKHF_INJECTED)
        self._vk_injected[vk] = is_injected

        if is_injected:
            return

        key_name = None
        if 65 <= vk <= 90:
            key_name = chr(vk)
        elif vk == 0x0D:
            key_name = "Return"
        elif vk == 0xA2:
            key_name = "Lcontrol"
        elif vk == 0xA3:
            key_name = "Rcontrol"

        if not key_name:
            return

        if self.should_suppress_key(key_name, is_injected):
            self._keyboard_listener.suppress_event()
            if self.debug:
                print(f"[input] suppress vk={vk} key={key_name}")

    def start(self):
        if self.debug:
            print("[input] backend=pynput keymap=E/W/A/R/Return/Lcontrol/Rcontrol")

        keyboard_kwargs = {
            "on_press": self._on_press,
            "on_release": self._on_release,
        }

        if self._is_windows:
            keyboard_kwargs["win32_event_filter"] = self._win32_event_filter

        self._keyboard_listener = keyboard.Listener(**keyboard_kwargs)
        self._mouse_listener = mouse.Listener(on_click=self._on_click)
        self._keyboard_listener.start()
        self._mouse_listener.start()

        self._stop_event.wait()
        self._keyboard_listener.join()
        self._mouse_listener.join()

    def stop(self):
        self._stop_event.set()
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
