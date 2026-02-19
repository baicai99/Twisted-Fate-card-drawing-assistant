import importlib
import sys
import types
import unittest

from app.config import AppConfig
from app.state import SharedState


def _import_input_handlers_with_stubs():
    stub_color_detector = types.ModuleType("app.color_detector")
    stub_selector = types.ModuleType("app.selector")
    stub_window_guard = types.ModuleType("app.window_guard")

    class _ColorDetector:
        def get_rgb(self, _x, _y):
            return 0, 0, 0

        def get_color_name(self, _r, _g, _b):
            return "未知"

    class _Selector:
        pass

    class _WindowGuard:
        def is_allowed(self):
            return True

    stub_color_detector.ColorDetector = _ColorDetector
    stub_selector.Selector = _Selector
    stub_window_guard.WindowGuard = _WindowGuard

    original_modules = {
        "app.color_detector": sys.modules.get("app.color_detector"),
        "app.selector": sys.modules.get("app.selector"),
        "app.window_guard": sys.modules.get("app.window_guard"),
        "app.input_handlers": sys.modules.get("app.input_handlers"),
    }

    try:
        sys.modules["app.color_detector"] = stub_color_detector
        sys.modules["app.selector"] = stub_selector
        sys.modules["app.window_guard"] = stub_window_guard
        sys.modules.pop("app.input_handlers", None)
        return importlib.import_module("app.input_handlers")
    finally:
        for name, module in original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class _FakeSelector:
    def __init__(self):
        self.calls = []

    def submit(self, color, open_cycle=True):
        self.calls.append((color, open_cycle))
        return len(self.calls)


class _FakeWindowGuard:
    def is_allowed(self):
        return True


class _FakeColorDetector:
    def get_rgb(self, _x, _y):
        return 0, 0, 0

    def get_color_name(self, _r, _g, _b):
        return "未知"


class _Event:
    def __init__(self, key, is_injected=False):
        self.Key = key
        self.is_injected = is_injected


class InputHandlersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._module = _import_input_handlers_with_stubs()

    def _build_handlers(self):
        return self._module.InputHandlers(
            config=AppConfig(),
            state=SharedState(),
            selector=_FakeSelector(),
            window_guard=_FakeWindowGuard(),
            color_detector=_FakeColorDetector(),
        )

    def test_physical_w_submits_blue_without_open_cycle(self):
        handlers = self._build_handlers()
        handlers.on_key_down(_Event("W", is_injected=False))
        self.assertEqual(handlers._selector.calls, [("蓝", False)])

    def test_injected_w_is_ignored(self):
        handlers = self._build_handlers()
        handlers.on_key_down(_Event("W", is_injected=True))
        self.assertEqual(handlers._selector.calls, [])

    def test_e_a_and_r_submit_with_open_cycle(self):
        handlers = self._build_handlers()
        handlers.on_key_down(_Event("E"))
        handlers.on_key_down(_Event("A"))
        handlers.on_key_down(_Event("R"))
        handlers.on_key_down(_Event("R"))
        self.assertEqual(
            handlers._selector.calls,
            [("黄", True), ("红", True), ("黄", True)],
        )


if __name__ == "__main__":
    unittest.main()
