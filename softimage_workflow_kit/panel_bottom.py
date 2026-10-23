# SPDX-License-Identifier: GPL-3.0-or-later
"""The bar along the bottom of Softimage's window: the command line, the playback controls, the animation panel and the status line (with the mouse hints)."""

import bpy

from .canvas import Canvas, c8, run_op, text_width

TEXT = c8(20, 20, 20)
EDGE = c8(120, 118, 116)
FIELD = c8(50, 50, 50)


def _scene():
    return bpy.context.scene


def _op(idname, /, **kw):
    def run(context):
        run_op(idname, **kw)
    return run


def _toggle(path_obj, attr):
    def run(context):
        setattr(path_obj(), attr, not getattr(path_obj(), attr))
    return run


class BottomPanel(Canvas):
    name = "Command line / playback"

    def __init__(self):
        super().__init__()
        self.command_text = ""
        self.history = []
        self.status = "Select Objects"

    def layout(self, width, height):
        sc = _scene()
        playing = bpy.context.screen.is_animation_playing if bpy.context.screen else False
        ws = []
        # ---- the panel switcher: small layout icons
        for i in range(8):
            ws.append({"kind": "tab", "x": 4 + i * 31, "y": 3, "w": 28, "h": 24, "label": "", "icon": i, "action": None})
        # ---- the command line takes what the playback and animation panels leave
        play_w, anim_w = 437, 384
        cl_x = 260
        cl_w = max(80, width - cl_x - play_w - anim_w)
        text = self.edit_text + "|" if self.editing is not None and self.editing.get("key") == "cmd" else (self.command_text or "")
        ws.append({"kind": "cmd", "x": cl_x, "y": 5, "w": cl_w, "h": 20, "label": text, "key": "cmd", "action": self._begin_command})
        # ---- playback
        px = cl_x + cl_w + 6
        ws.append({"kind": "pill", "x": px, "y": 4, "w": 22, "h": 22, "label": "", "icon": "wave", "action": None})
        ws.append({"kind": "pill", "x": px + 28, "y": 4, "w": 22, "h": 22, "label": "", "icon": "key", "action": _op("anim.keyframe_insert")})
        ws.append({"kind": "pill", "x": px + 56, "y": 4, "w": 66, "h": 22, "label": "Playback", "action": None})
        bx = px + 130
        buttons = (("first", _op("screen.frame_jump", end=False)), ("prev", _op("screen.frame_offset", delta=-1)), ("stop", _op("screen.animation_cancel", restore_frame=False)),
                   ("play", _op("screen.animation_play")), ("last", _op("screen.frame_jump", end=True)))
        ws.append({"kind": "pill", "x": px + 130 - 38, "y": 4, "w": 16, "h": 22, "label": "", "icon": "stepl", "action": _op("screen.keyframe_jump", next=False)})
        ws.append({"kind": "pill", "x": px + 130 - 20, "y": 4, "w": 16, "h": 22, "label": "", "icon": "stepr", "action": _op("screen.keyframe_jump", next=True)})
        for i, (icon, act) in enumerate(buttons):
            ws.append({"kind": "pill", "x": bx + 4 + i * 30, "y": 4, "w": 28, "h": 22, "label": "", "icon": icon, "action": act, "on": playing and icon == "play"})
        ws.append({"kind": "pill", "x": bx + 158, "y": 4, "w": 26, "h": 22, "label": "", "icon": "loop", "action": None})
        ws.append({"kind": "pill", "x": bx + 188, "y": 4, "w": 26, "h": 22, "label": "", "icon": "audio", "action": None})
        frame_text = self.edit_text + "|" if self.editing is not None and self.editing.get("key") == "frame" else str(sc.frame_current)
        ws.append({"kind": "field", "x": bx + 218, "y": 5, "w": 42, "h": 20, "label": frame_text, "key": "frame", "action": self._begin_frame})
        ws.append({"kind": "pill", "x": bx + 264, "y": 5, "w": 30, "h": 20, "label": "All", "action": None})
        # ---- animation
        ax = width - anim_w + 4
        ws.append({"kind": "pill", "x": ax, "y": 4, "w": 72, "h": 22, "label": "Animation", "corner": True, "action": None})
        ws.append({"kind": "pill", "x": ax, "y": 28, "w": 44, "h": 19, "label": "Auto", "on": bool(sc.tool_settings.use_keyframe_insert_auto), "action": _toggle(lambda: _scene().tool_settings, "use_keyframe_insert_auto")})
        ws.append({"kind": "pill", "x": ax + 78, "y": 4, "w": 40, "h": 40, "label": "", "icon": "bigkey", "action": _op("anim.keyframe_insert")})
        ws.append({"kind": "keys", "x": ax + 124, "y": 4, "w": 160, "h": 20, "label": "Key All Keyable", "action": _op("siwk.key_all")})
        ws.append({"kind": "field", "x": ax + 124, "y": 28, "w": 160, "h": 19, "label": "", "action": None})
        # ---- the status line
        ws.append({"kind": "status", "x": 6, "y": height - 21, "w": 300, "h": 20, "label": self.status, "action": None})
        for i, (letter, text) in enumerate((("L", "Select NODE"), ("M", "Select BRANCH"), ("R", "Select TREE/CHAIN"))):
            ws.append({"kind": "hint", "x": width - 430 + i * 140, "y": height - 21, "w": 136, "h": 20, "label": text, "letter": letter, "action": None})
        self.widgets = ws

    # --- command line
    def _begin_command(self, context):
        w = next(w for w in self.widgets if w.get("key") == "cmd")
        self.begin_edit(w, "", self._run_command)

    def _run_command(self, text):
        self.command_text = text
        if text.strip():
            self.history.append(text)
            bpy.ops.siwk.run_command(text=text)

    def _begin_frame(self, context):
        w = next(w for w in self.widgets if w.get("key") == "frame")
        self.begin_edit(w, str(_scene().frame_current), lambda t: self._set_frame(t))

    @staticmethod
    def _set_frame(text):
        try:
            sc = _scene()
            sc.frame_set(max(sc.frame_start, min(sc.frame_end, int(float(text)))))
        except ValueError:
            pass

    # --- drawing
    def draw_widget(self, p, w, state):
        x, y, ww, h = w["x"], w["y"], w["w"], w["h"]
        k = w["kind"]
        if k == "tab":
            top, bottom = (c8(196, 193, 192), c8(176, 173, 172)) if state != 'normal' else (c8(188, 185, 184), c8(168, 165, 164))
            p.round_grad(x, y, ww, h, 4, top, bottom)
            p.round_outline(x, y, ww, h, 4, EDGE)
            ink = c8(60, 60, 60)
            i = w["icon"]
            if i in (0, 1, 2, 3):   # a panel on one side of a window
                rects = ((x + 5, y + 5, 7, h - 10), (x + 5, y + 5, ww - 10, 7), (x + 5, y + h - 12, ww - 10, 7), (x + ww - 12, y + 5, 7, h - 10))
                p.rect(*rects[i], ink)
            else:
                for dx in (0, 1):
                    for dy in (0, 1):
                        p.rect(x + 6 + dx * 9, y + 5 + dy * 8, 8, 7, ink)
        elif k == "cmd":
            p.round_rect(x, y, ww, h, 6, c8(60, 58, 58))
            p.round_outline(x, y, ww, h, 6, c8(30, 30, 30))
            if w["label"]:
                if self.editing is not None:
                    p.rect(x + 4, y + 3, text_width(w["label"], 12) + 4, h - 6, c8(40, 100, 200))
                p.text(x + 6, y + h * 0.5, w["label"], c8(235, 235, 235), size=12)
            p.triangle(x + ww - 14, y + h * 0.5 - 2, x + ww - 6, y + h * 0.5 - 2, x + ww - 10, y + h * 0.5 + 3, c8(200, 200, 200))
        elif k == "field":
            p.round_rect(x, y, ww, h, 8, FIELD)
            p.round_outline(x, y, ww, h, 8, c8(26, 26, 26))
            p.text(x + 7, y + h * 0.5, w["label"], c8(235, 235, 235), size=12)
        elif k == "keys":
            p.round_rect(x, y, ww, h, 4, c8(184, 181, 180))
            p.round_outline(x, y, ww, h, 4, EDGE)
            p.text(x + 6, y + h * 0.5, w["label"], TEXT, size=12)
            p.round_rect(x + ww + 4, y + 2, 14, h - 4, 3, c8(190, 40, 40))
        elif k == "pill":
            self._pill(p, w, state)
        elif k == "status":
            p.text(x, y + h * 0.5, w["label"], TEXT, size=12)
        elif k == "hint":
            p.circle(x + 8, y + h * 0.5, 7, c8(150, 148, 147))
            p.text_center(x + 1, y + h * 0.5, 14, w["letter"], c8(60, 60, 60), size=11, bold=True)
            p.text(x + 20, y + h * 0.5, w["label"], TEXT, size=12)

    @staticmethod
    def _pill(p, w, state):
        x, y, ww, h = w["x"], w["y"], w["w"], w["h"]
        on = w.get("on", False)
        if on:
            top, bottom = c8(246, 245, 244), c8(222, 220, 219)
        elif state != 'normal':
            top, bottom = c8(198, 195, 194), c8(180, 177, 176)
        else:
            top, bottom = c8(190, 187, 186), c8(168, 165, 164)
        if state == 'pressed':
            top, bottom = bottom, top
        p.round_grad(x, y, ww, h, 8, top, bottom)
        p.round_outline(x, y, ww, h, 8, EDGE)
        if w["label"]:
            p.text_center(x, y + h * 0.5, ww, w["label"], TEXT, size=12, bold=True)
        icon = w.get("icon")
        if icon:
            cx, cy = x + ww / 2.0, y + h / 2.0
            ink = c8(40, 40, 40)
            if icon == "play":
                p.triangle(cx - 4, cy - 6, cx - 4, cy + 6, cx + 6, cy, ink)
            elif icon == "stop":
                p.rect(cx - 5, cy - 5, 10, 10, ink)
            elif icon == "first":
                p.rect(cx - 7, cy - 6, 2, 12, ink); p.triangle(cx + 6, cy - 6, cx + 6, cy + 6, cx - 4, cy, ink)
            elif icon == "last":
                p.rect(cx + 5, cy - 6, 2, 12, ink); p.triangle(cx - 6, cy - 6, cx - 6, cy + 6, cx + 4, cy, ink)
            elif icon == "prev":
                p.triangle(cx + 5, cy - 6, cx + 5, cy + 6, cx - 5, cy, ink)
            elif icon in ("stepl", "stepr"):
                s = -1 if icon == "stepl" else 1
                p.triangle(cx - s * 3, cy - 5, cx - s * 3, cy + 5, cx + s * 4, cy, ink)
            elif icon == "loop":
                p.circle_outline(cx, cy, 5, ink, 1.6)
            elif icon == "audio":
                p.circle_outline(cx, cy, 5, ink, 1.6); p.rect(cx - 6, cy, 3, 5, ink); p.rect(cx + 3, cy, 3, 5, ink)
            elif icon in ("key", "bigkey"):
                r = 4 if icon == "key" else 7
                p.circle_outline(cx - r * 0.4, cy - r * 0.4, r, ink, 1.6)
                p.line(cx + r * 0.4, cy + r * 0.4, cx + r * 1.5, cy + r * 1.5, ink, 2.0)
            elif icon == "wave":
                p.circle_outline(cx, cy, 5, ink, 1.6)
        if w.get("corner"):
            p.triangle(x + 4, y + 4, x + 10, y + 4, x + 4, y + 10, c8(40, 40, 40))
