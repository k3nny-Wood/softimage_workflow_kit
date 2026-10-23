# SPDX-License-Identifier: GPL-3.0-or-later
"""Softimage's menu bar: File Edit View Display Window Help, the module menus (Model Animate Render ICE Simulate), the construction mode and pass choosers and the scene search."""

import bpy

from . import menus
from .canvas import Canvas, c8, text_width

TEXT = c8(20, 20, 20)
EDGE = c8(120, 118, 116)

FIRST = ("File", "Edit", "View", "Display", "Window", "Help")
SECOND = ("Model", "Animate", "Render", "ICE", "Simulate")


class TopPanel(Canvas):
    name = "Menu Bar"

    def __init__(self):
        super().__init__()
        self.search_text = ""

    def layout(self, width, height):
        ws = []
        x = 6
        for group, gap in ((FIRST, 14), (SECOND, 0)):
            for label in group:
                w = text_width(label, 12) + 14
                ws.append({"kind": "menu", "x": x, "y": 1, "w": w, "h": height - 2, "label": label, "action": menus.TOP_MENUS[label]})
                x += w
            x += gap
        x += 30
        scene = bpy.context.scene if bpy.context.scene else None
        layer = bpy.context.view_layer.name if bpy.context.view_layer else "ViewLayer"
        ws.append({"kind": "combo", "x": x, "y": 2, "w": 196, "h": height - 4, "label": "Modeling Construction Mode", "icon": True, "action": "SIWK_MT_constr_mode"})
        x += 196 + 8
        ws.append({"kind": "combo", "x": x, "y": 2, "w": 170, "h": height - 4, "label": layer, "icon": True, "action": "SIWK_MT_passes"})
        x += 170 + 12
        label = self.edit_text + "|" if self.editing is not None else (self.search_text or "Scene Search")
        ws.append({"kind": "search", "x": x, "y": 2, "w": 150, "h": height - 4, "label": label, "idle": self.editing is None and not self.search_text, "action": self._begin_search})
        x += 150 + 8
        for i in range(4):
            ws.append({"kind": "dot", "x": x + i * 24, "y": 2, "w": 20, "h": height - 4, "label": "", "action": None, "index": i})
        self.widgets = ws

    def _begin_search(self, context):
        field = next(w for w in self.widgets if w["kind"] == "search")
        self.begin_edit(field, self.search_text, self._commit_search)

    def _commit_search(self, text):
        self.search_text = text
        if text.strip():
            bpy.ops.siwk.scene_search(text=text)

    def draw_widget(self, p, w, state):
        x, y, ww, h = w["x"], w["y"], w["w"], w["h"]
        k = w["kind"]
        if k == "menu":
            if state != 'normal':
                p.round_rect(x, y + 1, ww, h - 2, 3, c8(196, 193, 192) if state == 'hover' else c8(150, 148, 146))
                p.round_outline(x, y + 1, ww, h - 2, 3, EDGE)
            p.text_center(x, y + h * 0.5, ww, w["label"], TEXT, size=12)
        elif k == "combo":
            top, bottom = (c8(198, 195, 194), c8(180, 177, 176)) if state != 'normal' else (c8(190, 187, 186), c8(170, 167, 166))
            p.round_grad(x, y, ww, h, 4, top, bottom)
            p.round_outline(x, y, ww, h, 4, EDGE)
            if w.get("icon"):
                p.round_rect(x + 5, y + 4, 12, h - 8, 2, c8(120, 90, 130))
            p.text(x + 24, y + h * 0.5, w["label"], TEXT, size=12)
            p.triangle(x + ww - 14, y + h * 0.5 - 2, x + ww - 6, y + h * 0.5 - 2, x + ww - 10, y + h * 0.5 + 3, c8(30, 30, 30))
        elif k == "search":
            p.round_rect(x, y, ww, h, 4, c8(52, 52, 52))
            p.round_outline(x, y, ww, h, 4, c8(28, 28, 28))
            color = c8(150, 150, 150) if w.get("idle") else c8(235, 235, 235)
            p.text(x + 6, y + h * 0.5, w["label"], color, size=12)
            p.circle_outline(x + ww - 14, y + h * 0.5 - 1, 4, c8(190, 190, 190), 1.4)
            p.line(x + ww - 11, y + h * 0.5 + 2, x + ww - 7, y + h * 0.5 + 6, c8(190, 190, 190), 1.6)
        elif k == "dot":
            p.circle_grad(x + ww / 2.0, y + h / 2.0, h / 2.0 - 1, c8(200, 197, 196), c8(166, 163, 162))
            p.circle_outline(x + ww / 2.0, y + h / 2.0, h / 2.0 - 1, EDGE)
