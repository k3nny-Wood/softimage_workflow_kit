# SPDX-License-Identifier: GPL-3.0-or-later
"""Softimage's timeline: the current-frame box, the ruler (click or drag to scrub) and, below, the time range."""

import bpy

from .canvas import Canvas, c8, text_width

RULER_BG = c8(158, 156, 155)
RANGE_BG = c8(146, 144, 143)
TICK = c8(60, 60, 60)
FIELD = c8(50, 50, 50)


def _scene():
    return bpy.context.scene


def _set_frame(frame):
    sc = _scene()
    sc.frame_set(max(sc.frame_start, min(sc.frame_end, int(round(frame)))))


class TimelinePanel(Canvas):
    name = "Timeline"
    background = c8(150, 148, 147)

    def layout(self, width, height):
        sc = _scene()
        ws = []
        # row 1: the current frame, the ruler, the end of the range
        ws.append({"kind": "field", "x": 3, "y": 3, "w": 44, "h": 19, "label": self.edit_text + "|" if self._editing_key("frame") else str(sc.frame_current), "action": lambda c: self._edit("frame", str(sc.frame_current), self._commit_frame), "key": "frame"})
        rx, rw = 52, max(10, width - 52 - 50)
        ws.append({"kind": "ruler", "x": rx, "y": 0, "w": rw, "h": 26, "label": "", "action": True, "drag": self._scrub})
        ws.append({"kind": "field", "x": width - 46, "y": 3, "w": 44, "h": 19, "label": self.edit_text + "|" if self._editing_key("end") else str(sc.frame_end), "action": lambda c: self._edit("end", str(sc.frame_end), self._commit_end), "key": "end"})
        # row 2: the time range
        ws.append({"kind": "field", "x": 3, "y": 29, "w": 44, "h": 17, "label": self.edit_text + "|" if self._editing_key("start") else str(sc.frame_start), "action": lambda c: self._edit("start", str(sc.frame_start), self._commit_start), "key": "start"})
        ws.append({"kind": "range", "x": rx, "y": 27, "w": rw, "h": 20, "label": "", "action": None})
        ws.append({"kind": "field", "x": width - 90, "y": 29, "w": 40, "h": 17, "label": str(sc.frame_end), "action": None, "key": "end2"})
        self.widgets = ws

    # --- editing
    def _editing_key(self, key):
        return self.editing is not None and self.editing.get("key") == key

    def _edit(self, key, text, commit):
        w = next(w for w in self.widgets if w.get("key") == key)
        self.begin_edit(w, text, commit)

    @staticmethod
    def _number(text, default):
        try:
            return int(float(text))
        except ValueError:
            return default

    def _commit_frame(self, text):
        _set_frame(self._number(text, _scene().frame_current))

    def _commit_end(self, text):
        sc = _scene()
        sc.frame_end = max(sc.frame_start, self._number(text, sc.frame_end))

    def _commit_start(self, text):
        sc = _scene()
        sc.frame_start = min(sc.frame_end, self._number(text, sc.frame_start))

    def _scrub(self, context, widget, x, y):
        sc = _scene()
        span = max(1, sc.frame_end - sc.frame_start)
        t = (x - widget["x"]) / float(widget["w"])
        _set_frame(sc.frame_start + t * span)

    # --- drawing
    def draw_widget(self, p, w, state):
        sc = _scene()
        x, y, ww, h = w["x"], w["y"], w["w"], w["h"]
        k = w["kind"]
        if k == "field":
            p.round_rect(x, y, ww, h, 7, FIELD)
            p.round_outline(x, y, ww, h, 7, c8(26, 26, 26))
            p.text(x + 6, y + h * 0.5, w["label"], c8(235, 235, 235), size=12)
        elif k == "ruler":
            p.rect(x, y, ww, h, RULER_BG)
            p.rect(x, y + h - 1, ww, 1, c8(110, 108, 107))
            span = max(1, sc.frame_end - sc.frame_start)
            px_per = ww / float(span)
            step = 1
            for cand in (1, 5, 10, 25, 50, 100, 250, 500, 1000):
                step = cand
                if cand * px_per >= 34:
                    break
            for f in range(sc.frame_start, min(sc.frame_end, sc.frame_start + 6000) + 1):
                fx = x + (f - sc.frame_start) * px_per
                if (f - sc.frame_start) % step == 0:
                    p.rect(fx, y + 4, 1, h - 5, TICK)
                    p.text(fx + 3, y + 8, str(f), c8(40, 40, 40), size=11)
                elif px_per >= 3.5 and f % max(1, step // 5) == 0:
                    p.rect(fx, y + h - 8, 1, 7, c8(90, 90, 90))
            cx = x + (sc.frame_current - sc.frame_start) * px_per
            p.rect(cx, y, 2, h, c8(210, 20, 20))
            p.text(cx + 4, y + 8, str(sc.frame_current), c8(200, 20, 20), size=11, bold=True)
        elif k == "range":
            p.rect(x, y, ww, h, RANGE_BG)
            p.rect(x, y, ww, 1, c8(120, 118, 117))
            span = max(1, sc.frame_end - sc.frame_start)
            cx = x + (sc.frame_current - sc.frame_start) / float(span) * ww
            p.rect(cx - 1, y + 2, 3, h - 4, c8(60, 60, 60))
            p.text(x + 5, y + h * 0.5, str(sc.frame_start), c8(40, 40, 40), size=11)
