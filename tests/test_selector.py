import importlib
import sys
import types
import unittest

from app.config import AppConfig
from app.state import SharedState


def _import_selector_with_stubs():
    stub_color_detector = types.ModuleType("app.color_detector")
    stub_window_guard = types.ModuleType("app.window_guard")

    class _ColorDetector:
        pass

    class _WindowGuard:
        pass

    stub_color_detector.ColorDetector = _ColorDetector
    stub_window_guard.WindowGuard = _WindowGuard

    original_modules = {
        "app.color_detector": sys.modules.get("app.color_detector"),
        "app.window_guard": sys.modules.get("app.window_guard"),
        "app.selector": sys.modules.get("app.selector"),
    }

    try:
        sys.modules["app.color_detector"] = stub_color_detector
        sys.modules["app.window_guard"] = stub_window_guard
        sys.modules.pop("app.selector", None)
        return importlib.import_module("app.selector")
    finally:
        for name, module in original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class SelectorSubmitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._module = _import_selector_with_stubs()

    def _build_selector(self, click_calls):
        def click_w(is_lock_press, request_id):
            click_calls.append((is_lock_press, request_id))

        class _ColorDetector:
            pass

        class _WindowGuard:
            pass

        return self._module.Selector(
            config=AppConfig(),
            state=SharedState(),
            color_detector=_ColorDetector(),
            window_guard=_WindowGuard(),
            click_w=click_w,
            debug_log=lambda *_args: None,
            on_result=None,
        )

    def test_submit_open_cycle_false_does_not_click_w(self):
        click_calls = []
        selector = self._build_selector(click_calls)
        request_id = selector.submit("蓝", open_cycle=False)
        self.assertEqual(request_id, 1)
        self.assertEqual(click_calls, [])

    def test_submit_open_cycle_true_clicks_w_once(self):
        click_calls = []
        selector = self._build_selector(click_calls)
        request_id = selector.submit("黄", open_cycle=True)
        self.assertEqual(request_id, 1)
        self.assertEqual(click_calls, [(False, None)])


if __name__ == "__main__":
    unittest.main()
