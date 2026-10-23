# SPDX-License-Identifier: GPL-3.0-or-later
"""The module toolbar down the left side of Softimage: the module chooser (Model / Animate / Render / Simulate) and the groups of menu buttons.

Measured from Softimage 2015 SP2 at 100 % scale: the panel is ~106 px wide, the chooser is 22 px high, group headers 17 px, buttons 24 px on a 29 px pitch.
The groups and button names are those of the Animate module as Softimage shows them.
"""

from . import menus
from .canvas import Canvas, c8

HEADER_GREEN = c8(128, 168, 147)
COMBO_GREEN = c8(133, 167, 145)
TEXT = c8(22, 22, 22)
EDGE = c8(120, 118, 116)

MODULES = {
    "Animate": [
        ("Get", ["Primitive", "Material", "Property"]),
        ("Create", ["Parameter", "Curve", "Path", "Skeleton", "Character"]),
        ("Deform", ["Shape", "Envelope", "Deform"]),
        ("Actions", ["Store", "Apply", "Templates"]),
        ("Tools", ["Plot", "Devices", "Import/Export", "MOTOR"]),
    ],
    "Model": [
        ("Get", ["Primitive", "Material", "Property"]),
        ("Create", ["Curve", "Surface", "Poly. Mesh", "Model"]),
        ("Modify", ["Curve", "Surface", "Poly. Mesh", "Transform", "Component"]),
        ("Constr. Mode", ["Modeling", "Prim. Shape", "Animation", "Sec. Shape"]),
    ],
    "Render": [
        ("Get", ["Primitive", "Material", "Property"]),
        ("Create", ["Light", "Camera", "Pass"]),
        ("Render", ["Frame", "Sequence", "Region", "Options"]),
    ],
    "Simulate": [
        ("Get", ["Primitive", "Material", "Property"]),
        ("Create", ["Rigid Body", "Cloth", "Fluid", "Particles"]),
        ("Tools", ["Bake", "Clear"]),
    ],
}


class LeftPanel(Canvas):
    name = "Toolbar Panel"

    def __init__(self, module="Animate"):
        super().__init__()
        self.module = module

    def layout(self, width, height):
        W = width
        ws = []
        ws.append({"kind": "combo", "x": 3, "y": 5, "w": W - 6, "h": 21, "label": self.module, "action": "SIWK_MT_modules"})
        y = 36
        for group, buttons in MODULES.get(self.module, []):
            ws.append({"kind": "header", "x": 0, "y": y, "w": W, "h": 17, "label": group, "action": None})
            y += 17 + 6
            for label in buttons:
                ws.append({"kind": "button", "x": 3, "y": y, "w": W - 6, "h": 24, "label": label, "action": menus.flyout_id(label) if label in menus.LEFT_FLYOUTS else None})
                y += 29
            y += 2
        self.widgets = ws

    def draw_widget(self, p, w, state):
        x, y, ww, h = w["x"], w["y"], w["w"], w["h"]
        if w["kind"] == "header":
            p.rect(x, y, ww, h, HEADER_GREEN)
            p.rect(x, y + h - 1, ww, 1, c8(110, 146, 128))
            p.text(x + 5, y + h * 0.5, w["label"], TEXT, size=12, bold=True)
        elif w["kind"] == "combo":
            p.round_grad(x, y, ww, h, 7, c8(146, 181, 159), COMBO_GREEN)
            p.round_outline(x, y, ww, h, 7, c8(96, 128, 108))
            p.text(x + 6, y + h * 0.5, w["label"], TEXT, size=13, bold=True)
            ax = x + ww - 15
            p.triangle(ax, y + 8, ax + 8, y + 8, ax + 4, y + 14, c8(30, 50, 40))
        else:
            hot = state != 'normal'
            top, bottom = (c8(196, 193, 192), c8(178, 175, 174)) if hot else (c8(189, 186, 185), c8(166, 163, 162))
            if state == 'pressed':
                top, bottom = bottom, top
            p.round_grad(x, y, ww, h, 10, top, bottom)
            p.round_outline(x, y, ww, h, 10, EDGE)
            p.text_center(x, y + h * 0.5, ww, w["label"], TEXT, size=12, bold=True)
            p.triangle(x + ww - 10, y + h - 5, x + ww - 4, y + h - 5, x + ww - 4, y + h - 11, c8(40, 40, 40))
