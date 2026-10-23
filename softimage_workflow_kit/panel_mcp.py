# SPDX-License-Identifier: GPL-3.0-or-later
"""The MCP (Softimage's main command panel, down the right side): Select, Transform, Snap, Constrain and Edit.

Positions are measured from Softimage 2015 SP2's default layout at 100 % scale, in a panel 136 px wide, with the top-left corner as the origin.
"""

import math

import bpy

from .canvas import Canvas, c8, run_op

BG = c8(171, 168, 166)
TEXT = c8(24, 28, 40)
TEXT_OFF = c8(138, 136, 134)
EDGE = c8(124, 122, 120)
FIELD = c8(50, 50, 50)
HEADER_TOP, HEADER_BOTTOM = c8(150, 148, 146), c8(138, 136, 134)


def _w(kind, x, y, w, h, label="", **kw):
    d = {"kind": kind, "x": x, "y": y, "w": w, "h": h, "label": label, "action": kw.pop("action", None)}
    d.update(kw)
    return d


def _ob():
    return bpy.context.active_object


def _ts():
    return bpy.context.scene.tool_settings


def _op(idname, /, **kw):
    def run(context):
        run_op(idname, **kw)
    return run


def _tool(tool_id):
    return _op("wm.tool_set_by_id", name=tool_id)


def _orientation(kind):
    def run(context):
        bpy.context.scene.transform_orientation_slots[0].type = kind
    return run


class McpPanel(Canvas):
    name = "MCP"

    def __init__(self):
        super().__init__()
        self.axis_on = {}

    # ---- state read from Blender
    @staticmethod
    def _orientation_is(kind):
        return bpy.context.scene.transform_orientation_slots[0].type == kind

    @staticmethod
    def _mesh_mode(index):
        ob = _ob()
        return ob is not None and ob.mode == 'EDIT' and ob.type == 'MESH' and tuple(_ts().mesh_select_mode)[index]

    @staticmethod
    def _value_text(letter, i):
        ob = _ob()
        if ob is None:
            return ""
        if letter == "S":
            return "%.3f" % ob.scale[i]
        if letter == "R":
            return "%.3f" % math.degrees(ob.rotation_euler[i])
        return "%.3f" % ob.location[i]

    def _edit_value(self, letter, i, key):
        if _ob() is None:
            return
        w = next(w for w in self.widgets if w.get("key") == key)

        def commit(text):
            try:
                v = float(text)
            except ValueError:
                return
            o = _ob()
            if o is None:
                return
            if letter == "S":
                o.scale[i] = v
            elif letter == "R":
                o.rotation_euler[i] = math.radians(v)
            else:
                o.location[i] = v
        self.begin_edit(w, self._value_text(letter, i), commit)

    def _edit_name(self, context):
        ob = _ob()
        w = next(w for w in self.widgets if w.get("key") == "name")
        self.begin_edit(w, ob.name if ob else "", self._rename)

    @staticmethod
    def _rename(text):
        ob = _ob()
        if ob is not None and text.strip():
            ob.name = text.strip()

    @staticmethod
    def _toggle_lock(letter):
        def run(context):
            ob = _ob()
            if ob is None:
                return
            vals = getattr(ob, {"S": "lock_scale", "R": "lock_rotation", "T": "lock_location"}[letter])
            new = not all(vals)
            for i in range(3):
                vals[i] = new
        return run

    @staticmethod
    def _snap_element(kind):
        def run(context):
            ts = _ts()
            elems = set(ts.snap_elements)
            if kind in elems:
                elems.discard(kind)
            else:
                elems.add(kind)
            ts.snap_elements = elems or {kind}
        return run

    @staticmethod
    def _snap_on(kind):
        return kind in set(_ts().snap_elements)

    @staticmethod
    def _toggle_ts(attr):
        def run(context):
            setattr(_ts(), attr, not getattr(_ts(), attr))
        return run

    @staticmethod
    def _toggle_mirror(context):
        ob = _ob()
        if ob is not None and ob.type == 'MESH':
            ob.data.use_mirror_x = not ob.data.use_mirror_x

    @staticmethod
    def _pivot_cog(context):
        _ts().transform_pivot_point = 'MEDIAN_POINT'

    def _toggle_axis(self, letter, i):
        def run(context):
            self.axis_on[(letter, i)] = not self.axis_on.get((letter, i), False)
        return run

    def _value_action(self, letter, i, key):
        def run(context):
            self._edit_value(letter, i, key)
        return run

    def layout(self, width, height):
        ws = []
        ob = _ob()

        def header(y, title):
            ws.append(_w("header", 4, y, width - 5, 17, title))

        def pill(x, y, w, h, label, action=None, on=False, off=False, corner=False, **kw):
            ws.append(_w("pill", x, y, w, h, label, action=action, on=on, off=off, corner=corner, **kw))

        # ---- Select
        header(6, "Select")
        ws.append(_w("select_tool", 14, 28, 52, 52, "", action=_tool("builtin.select_box")))
        pill(72, 29, 59, 23, "Group", action=_op("siwk.group"))
        pill(72, 56, 59, 23, "Center", action=_op("view3d.snap_cursor_to_selected"))
        in_mesh = ob is not None and ob.type == 'MESH'
        pill(8, 87, 60, 25, "Object", action=_op("siwk.component_mode", mode='OBJECT'), on=bpy.context.mode == 'OBJECT')
        pill(72, 87, 59, 25, "Point", action=_op("siwk.component_mode", mode='VERT'), on=self._mesh_mode(0), off=not in_mesh)
        pill(8, 115, 60, 25, "Edge", action=_op("siwk.component_mode", mode='EDGE'), on=self._mesh_mode(1), off=not in_mesh)
        pill(72, 115, 59, 25, "Polygon", action=_op("siwk.component_mode", mode='FACE'), on=self._mesh_mode(2), off=not in_mesh)
        pill(8, 145, 123, 25, "", off=True, corner=True)
        typing_name = self.editing is not None and self.editing.get("key") == "name"
        name_text = self.edit_text + "|" if typing_name else (ob.name if ob else "")
        ws.append(_w("field", 7, 178, 124, 19, name_text, key="name", action=self._edit_name))
        ws.append(_w("field", 7, 201, 98, 18))
        ws.append(_w("arrows", 110, 200, 20, 20))
        pill(8, 226, 63, 25, "Explore", corner=True, action="SIWK_MT_explore")
        pill(75, 226, 56, 25, "Scene", action="SIWK_MT_scene_objects")
        pill(8, 254, 63, 25, "Selection", corner=True, action="SIWK_MT_selection")
        pill(75, 254, 56, 25, "Clusters", action="SIWK_MT_clusters")

        # ---- Transform: scale, rotation, translation of the active object
        header(286, "Transform")
        for gy, letter in ((315, "S"), (385, "R"), (457, "T")):
            for i, axis in enumerate("xyz"):
                key = "%s%d" % (letter, i)
                typing = self.editing is not None and self.editing.get("key") == key
                text = self.edit_text + "|" if typing else self._value_text(letter, i)
                ws.append(_w("field", 8, gy + 21 * i, 64, 18, text, key=key, action=self._value_action(letter, i, key)))
                ws.append(_w("axis", 78, gy + 21 * i, 27, 18, axis, on=self.axis_on.get((letter, i), False), action=self._toggle_axis(letter, i)))
            tool = {"S": "builtin.scale", "R": "builtin.rotate", "T": "builtin.move"}[letter]
            ws.append(_w("round", 107, gy - 4, 24, 24, letter, action=_tool(tool)))
            attr = {"S": "lock_scale", "R": "lock_rotation", "T": "lock_location"}[letter]
            ws.append(_w("lock", 113, gy + 41, 12, 18, on=ob is not None and all(getattr(ob, attr)), action=self._toggle_lock(letter)))
        pill(8, 523, 37, 24, "Global", action=_orientation('GLOBAL'), on=self._orientation_is('GLOBAL'))
        pill(50, 523, 38, 24, "Local", action=_orientation('LOCAL'), on=self._orientation_is('LOCAL'))
        pill(92, 523, 40, 24, "View", action=_orientation('VIEW'), on=self._orientation_is('VIEW'), corner=True)
        pill(8, 553, 37, 24, "Par", action=_orientation('PARENT'), on=self._orientation_is('PARENT'))
        pill(50, 553, 38, 24, "Ref", action=_orientation('CURSOR'), on=self._orientation_is('CURSOR'), corner=True)
        pill(92, 553, 40, 24, "Plane", action=_orientation('NORMAL'), on=self._orientation_is('NORMAL'), corner=True)
        pill(8, 584, 37, 24, "COG", action=self._pivot_cog, on=_ts().transform_pivot_point == 'MEDIAN_POINT')
        prop_on = _ts().use_proportional_edit_objects if bpy.context.mode == 'OBJECT' else _ts().use_proportional_edit
        pill(50, 584, 38, 24, "Prop", action=_op("siwk.proportional"), on=bool(prop_on), corner=True)
        mirror = ob is not None and ob.type == 'MESH' and ob.data.use_mirror_x
        pill(92, 584, 40, 24, "Sym", action=self._toggle_mirror, on=bool(mirror), corner=True)

        # ---- Snap
        header(620, "Snap")
        ws.append(_w("pill", 8, 646, 24, 19, "ON", flat=True, action=self._toggle_ts("use_snap"), on=bool(_ts().use_snap)))
        for i, (kind, elem) in enumerate((("point", 'VERTEX'), ("curve", 'EDGE'), ("circle", 'FACE'), ("grid", 'INCREMENT'))):
            ws.append(_w("snap", 34 + i * 24, 645, 22, 21, "", icon=kind, on=self._snap_on(elem), action=self._snap_element(elem)))

        # ---- Constrain
        header(671, "Constrain")
        pill(8, 699, 63, 25, "Parent", action=_op("object.parent_set", keep_transform=True))
        pill(75, 699, 56, 25, "Cut", action=_op("object.parent_clear", type='CLEAR_KEEP_TRANSFORM'))
        pill(8, 728, 63, 25, "CnsComp", off=True)
        pill(75, 728, 56, 25, "ChldComp", off=True)

        # ---- Edit
        header(762, "Edit")
        pill(8, 790, 63, 25, "Freeze", action=_op("siwk.freeze"))
        pill(75, 790, 50, 25, "Group", action=_op("siwk.group"))
        pill(8, 818, 63, 25, "Freeze M", action=_op("object.transform_apply"))
        pill(75, 818, 50, 25, "Immed", off=True)
        self.widgets = ws

    # ---------------------------------------------------------------------------------------------------- drawing
    def draw_widget(self, p, w, state):
        k = w["kind"]
        x, y, ww, h = w["x"], w["y"], w["w"], w["h"]
        if k == "header":
            p.vgrad(x, y, ww, h, HEADER_TOP, HEADER_BOTTOM)
            p.rect(x, y + h - 1, ww, 1, c8(110, 108, 106))
            p.triangle(x + 4, y + 5, x + 4, y + 12, x + 11, y + 12, c8(20, 20, 20))
            p.text(x + ww - 6 - p.text_width(w["label"], 14, True), y + h * 0.5, w["label"], c8(34, 34, 34), size=14, bold=True)
        elif k == "pill":
            self._pill(p, w, state)
        elif k == "field":
            p.round_rect(x, y, ww, h, 8, FIELD)
            p.round_outline(x, y, ww, h, 8, c8(26, 26, 26))
            if w["label"]:
                p.text(x + 6, y + h * 0.5, w["label"], c8(235, 235, 235), size=12)
        elif k == "axis":
            self._plain_pill(p, x, y, ww, h, 7, state != 'normal', state == 'pressed', white=w.get("on", False))
            p.text(x + 8, y + h * 0.5, w["label"], c8(40, 40, 40), size=13, bold=True)
        elif k == "round":
            p.circle_grad(x + ww / 2.0, y + h / 2.0, h / 2.0, c8(196, 193, 192), c8(170, 167, 166))
            p.circle_outline(x + ww / 2.0, y + h / 2.0, h / 2.0, EDGE)
            p.text_center(x, y + h * 0.5 + 1, ww, w["label"], c8(40, 40, 40), size=14, bold=True)
        elif k == "lock":
            p.round_rect(x, y, ww, h, 4, c8(60, 60, 60))
            p.round_rect(x + 1.5, y + 1.5, ww - 3, h - 3, 3, c8(110, 108, 106) if w.get("on") else c8(176, 173, 172))
            for i in (1, 2):
                p.rect(x + 2, y + i * h / 3.0, ww - 4, 1, c8(60, 60, 60))
        elif k == "snap":
            self._snap(p, w)
        elif k == "select_tool":
            self._select_tool(p, w, state)
        elif k == "arrows":
            cx, cy = x + ww / 2.0, y + h / 2.0
            c = c8(120, 118, 116)
            p.triangle(cx - 4, cy - 2, cx + 4, cy - 2, cx, cy - 8, c)
            p.triangle(cx - 4, cy + 1, cx + 4, cy + 1, cx, cy + 7, c)
            p.triangle(cx - 9, cy - 1, cx - 9, cy + 6, cx - 3, cy + 2.5, c)
            p.triangle(cx + 9, cy - 1, cx + 9, cy + 6, cx + 3, cy + 2.5, c)

    @staticmethod
    def _plain_pill(p, x, y, w, h, r, hot, pressed, white=False, off=False):
        if white:
            top, bottom = c8(250, 249, 248), c8(226, 224, 223)
        elif off:
            top, bottom = c8(178, 175, 174), c8(172, 169, 168)
        else:
            top, bottom = (c8(196, 193, 192), c8(178, 175, 174)) if hot else (c8(188, 185, 184), c8(168, 165, 164))
        if pressed:
            top, bottom = bottom, top
        p.round_grad(x, y, w, h, r, top, bottom)
        p.round_outline(x, y, w, h, r, c8(138, 136, 134) if off else EDGE)

    def _pill(self, p, w, state):
        x, y, ww, h = w["x"], w["y"], w["w"], w["h"]
        if w.get("flat"):
            p.text(x + 2, y + h * 0.5, w["label"], c8(30, 30, 30), size=13, bold=True)
            return
        self._plain_pill(p, x, y, ww, h, 9, state != 'normal', state == 'pressed', white=w.get("on", False), off=w.get("off", False))
        if w["label"]:
            color = TEXT_OFF if w.get("off") else TEXT
            p.text_center(x, y + h * 0.5 + 1, ww, w["label"], color, size=12, bold=True)
        if w.get("corner"):
            p.triangle(x + 4, y + 4, x + 10, y + 4, x + 4, y + 10, c8(40, 40, 40))

    @staticmethod
    def _snap(p, w):
        x, y, ww, h = w["x"], w["y"], w["w"], w["h"]
        MCP = McpPanel
        MCP._plain_pill(p, x, y, ww, h, 6, False, False, white=w.get("on", False))
        cx, cy = x + ww / 2.0, y + h / 2.0
        ink = c8(30, 30, 30)
        icon = w.get("icon")
        if icon == "point":
            p.circle(cx + 1, cy + 1, 2.5, ink)
        elif icon == "curve":
            p.circle_outline(cx - 1, cy - 2.5, 3.2, ink, 1.4)
            p.circle_outline(cx + 1, cy + 3.5, 3.2, ink, 1.4)
        elif icon == "circle":
            p.circle_outline(cx, cy, 5, ink, 1.4)
            p.circle(cx, cy, 2, ink)
        else:
            for i in (-4, 0, 4):
                p.line(cx - 5, cy + i, cx + 5, cy + i, c8(70, 70, 70))
                p.line(cx + i, cy - 5, cx + i, cy + 5, c8(70, 70, 70))
        p.triangle(x + 3, y + 3, x + 8, y + 3, x + 3, y + 8, c8(40, 40, 40))

    @staticmethod
    def _select_tool(p, w, state):
        x, y, d = w["x"], w["y"], w["w"]
        cx, cy, r = x + d / 2.0, y + d / 2.0, d / 2.0
        p.circle_grad(cx, cy, r, c8(150, 148, 146), c8(196, 194, 192))        # the dished ring
        p.circle_outline(cx, cy, r, c8(112, 110, 108), 1.5)
        p.circle_grad(cx, cy, r - 5, c8(126, 124, 122), c8(176, 174, 172))
        white = c8(246, 245, 244)
        # the pointer arrow (the classic cursor outline), tip up and to the left
        pts = [(0, 0), (0, 16), (4, 12), (7, 19), (9, 18), (6, 11), (11, 11)]
        k, ox, oy = 1.75, cx - 9.5, cy - 16

        def at(i):
            return ox + pts[i][0] * k, oy + pts[i][1] * k

        for a, b, c in ((0, 1, 2), (0, 2, 6), (2, 3, 4), (2, 4, 5), (2, 5, 6)):
            (x0, y0), (x1, y1), (x2, y2) = at(a), at(b), at(c)
            p.triangle(x0 + 1.5, y0 + 1.5, x1 + 1.5, y1 + 1.5, x2 + 1.5, y2 + 1.5, c8(96, 94, 92))   # a soft shadow
        for a, b, c in ((0, 1, 2), (0, 2, 6), (2, 3, 4), (2, 4, 5), (2, 5, 6)):
            (x0, y0), (x1, y1), (x2, y2) = at(a), at(b), at(c)
            p.triangle(x0, y0, x1, y1, x2, y2, white)
