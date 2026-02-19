import atexit
import threading
import time
from ctypes import windll

from app.config import ColorThresholds


class ColorDetector:
    def __init__(
        self,
        thresholds: ColorThresholds,
        double_sample_gap: float,
        sample_radius_px: int = 1,
        sample_min_hits: int = 2,
    ):
        self._thresholds = thresholds
        self._double_sample_gap = double_sample_gap
        self._sample_radius_px = max(0, int(sample_radius_px))
        self._sample_min_hits = max(1, int(sample_min_hits))
        self._gdi32 = windll.gdi32
        self._user32 = windll.user32
        self._hdc_lock = threading.Lock()
        self._hdc_by_tid = {}
        atexit.register(self._release_all_cached_hdc)

    def _release_all_cached_hdc(self):
        with self._hdc_lock:
            for hdc in self._hdc_by_tid.values():
                try:
                    self._user32.ReleaseDC(None, hdc)
                except Exception:
                    pass
            self._hdc_by_tid.clear()

    def _get_cached_hdc(self):
        tid = threading.get_ident()
        with self._hdc_lock:
            hdc = self._hdc_by_tid.get(tid)
            if hdc is None:
                hdc = self._user32.GetDC(None)
                self._hdc_by_tid[tid] = hdc
            return hdc

    def get_rgb(self, px: int, py: int):
        hdc = self._user32.GetDC(None)
        try:
            pixel = self._gdi32.GetPixel(hdc, px, py)
        finally:
            self._user32.ReleaseDC(None, hdc)

        r = pixel & 0x0000FF
        g = (pixel & 0x00FF00) >> 8
        b = pixel >> 16
        return r, g, b

    def get_rgb_fast(self, px: int, py: int):
        hdc = self._get_cached_hdc()
        pixel = self._gdi32.GetPixel(hdc, px, py)
        if pixel == -1:
            return self.get_rgb(px, py)
        r = pixel & 0x0000FF
        g = (pixel & 0x00FF00) >> 8
        b = pixel >> 16
        return r, g, b

    def is_yellow(self, r: int, g: int, b: int) -> bool:
        t = self._thresholds
        return r >= t.yellow_min_r and g >= t.yellow_min_g and b <= t.yellow_max_b

    def is_blue(self, r: int, g: int, b: int) -> bool:
        t = self._thresholds
        return r <= t.blue_max_r and g <= t.blue_max_g and b >= t.blue_min_b

    def is_red(self, r: int, g: int, b: int) -> bool:
        t = self._thresholds
        return r >= t.red_min_r and g <= t.red_max_g and b <= t.red_max_b

    def color_matches_target(self, r: int, g: int, b: int, target_color: str) -> bool:
        if target_color == "黄":
            return self.is_yellow(r, g, b)
        if target_color == "蓝":
            return self.is_blue(r, g, b)
        if target_color == "红":
            return self.is_red(r, g, b)
        return False

    def match_target(self, px: int, py: int, target_color: str) -> bool:
        r1, g1, b1 = self.get_rgb(px, py)
        if not self.color_matches_target(r1, g1, b1, target_color):
            return False

        time.sleep(self._double_sample_gap)
        r2, g2, b2 = self.get_rgb(px, py)
        return self.color_matches_target(r2, g2, b2, target_color)

    def match_target_fast(self, px: int, py: int, target_color: str) -> bool:
        hits_1 = self._match_hits_fast(px, py, target_color)
        if hits_1 < self._sample_min_hits:
            return False

        time.sleep(self._double_sample_gap)
        hits_2 = self._match_hits_fast(px, py, target_color)
        return hits_2 >= self._sample_min_hits

    def _match_hits_fast(self, px: int, py: int, target_color: str) -> int:
        # Always test center first, then the surrounding neighborhood.
        points = [(px, py)]
        radius = self._sample_radius_px
        if radius > 0:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    points.append((px + dx, py + dy))

        hits = 0
        for sx, sy in points:
            r, g, b = self.get_rgb_fast(sx, sy)
            if self.color_matches_target(r, g, b, target_color):
                hits += 1
                if hits >= self._sample_min_hits:
                    return hits
        return hits

    def get_color_name(self, r: int, g: int, b: int) -> str:
        if self.is_yellow(r, g, b):
            return "黄"
        if self.is_blue(r, g, b):
            return "蓝"
        if self.is_red(r, g, b):
            return "红"
        if abs(r - g) <= 12 and abs(g - b) <= 12:
            return "灰"
        return "未知"
