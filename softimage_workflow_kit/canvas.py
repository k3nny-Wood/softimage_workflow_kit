# SPDX-License-Identifier: GPL-3.0-or-later
"""Custom-drawn panels. Blender's own widgets cannot look like Softimage's, so the Softimage panels are drawn by the kit into "canvas" areas:
an area of an editor nobody else uses (the Spreadsheet), with its header and side regions hidden, covered by a draw handler that paints the whole region
and a keymap that sends the mouse to the panel under it.

A Canvas subclass lays out its widgets (rectangles with the top-left corner as the origin, as Softimage's panels are measured) and draws them with a Painter.
"""

import math
import os

import blf
import bpy
import gpu
from bpy.types import Operator
from gpu_extras.batch import batch_for_shader

HOST_SPACE = bpy.types.SpaceSpreadsheet
HOST_TYPE = 'SPREADSHEET'

_registry = {}   # area pointer -> Canvas
_handle = None
_fonts = {}


# ---------------------------------------------------------------------------------------------------------------- fonts

def font(bold=False):
    """The Windows Tahoma family Softimage's panels use; Blender's default font when it is not there."""
    key = "bold" if bold else "regular"
    if key not in _fonts:
        fid = 0
        for name in (("tahomabd.ttf", "segoeuib.ttf") if bold else ("tahoma.ttf", "segoeui.ttf")):
            path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
            if os.path.exists(path):
                fid = blf.load(path)
                break
        _fonts[key] = fid
    return _fonts[key]


def text_width(s, size=12, bold=False):
    fid = font(bold)
    blf.size(fid, size)
    return blf.dimensions(fid, s)[0]


# ---------------------------------------------------------------------------------------------------------------- painter

def c8(r, g, b, a=255):
    return (r / 255.0, g / 255.0, b / 255.0, a / 255.0)


class Painter:
    """Draws in pixels with the origin at the TOP-left of the region (y grows downward), the way Softimage's panels are specified."""

    def __init__(self, region):
        self.w, self.h = region.width, region.height
        self._flat = gpu.shader.from_builtin('UNIFORM_COLOR')
        self._smooth = gpu.shader.from_builtin('SMOOTH_COLOR')

    def _y(self, y):
        return self.h - y

    def _fan(self, pts, color):
        batch = batch_for_shader(self._flat, 'TRI_FAN', {"pos": pts})
        self._flat.bind()
        self._flat.uniform_float("color", color)
        batch.draw(self._flat)

    def rect(self, x, y, w, h, color):
        self._fan([(x, self._y(y)), (x + w, self._y(y)), (x + w, self._y(y + h)), (x, self._y(y + h))], color)

    def vgrad(self, x, y, w, h, top, bottom):
        pts = [(x, self._y(y)), (x + w, self._y(y)), (x + w, self._y(y + h)), (x, self._y(y + h))]
        cols = [top, top, bottom, bottom]
        batch = batch_for_shader(self._smooth, 'TRI_FAN', {"pos": pts, "color": cols})
        self._smooth.bind()
        batch.draw(self._smooth)

    @staticmethod
    def _round_pts(x, y, w, h, r, seg=7):
        r = min(r, w / 2.0, h / 2.0)
        pts = []
        corners = ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180))
        for cx, cy, start in corners:
            for i in range(seg + 1):
                a = math.radians(start + 90.0 * i / seg)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def round_rect(self, x, y, w, h, r, color):
        pts = [(px, self._y(py)) for px, py in self._round_pts(x, y, w, h, r)]
        self._fan(pts, color)

    def round_grad(self, x, y, w, h, r, top, bottom):
        pts = self._round_pts(x, y, w, h, r)
        cols = []
        for _px, py in pts:
            t = (py - y) / float(h) if h else 0.0
            cols.append(tuple(top[i] + (bottom[i] - top[i]) * t for i in range(4)))
        batch = batch_for_shader(self._smooth, 'TRI_FAN', {"pos": [(px, self._y(py)) for px, py in pts], "color": cols})
        self._smooth.bind()
        batch.draw(self._smooth)

    def round_outline(self, x, y, w, h, r, color, width=1.0):
        pts = [(px, self._y(py)) for px, py in self._round_pts(x, y, w, h, r)]
        pts.append(pts[0])
        batch = batch_for_shader(self._flat, 'LINE_STRIP', {"pos": pts})
        gpu.state.line_width_set(width)
        self._flat.bind()
        self._flat.uniform_float("color", color)
        batch.draw(self._flat)
        gpu.state.line_width_set(1.0)

    def circle(self, cx, cy, r, color, seg=28):
        pts = [(cx, self._y(cy))] + [(cx + r * math.cos(2 * math.pi * i / seg), self._y(cy + r * math.sin(2 * math.pi * i / seg))) for i in range(seg + 1)]
        self._fan(pts, color)

    def circle_grad(self, cx, cy, r, top, bottom, seg=28):
        pts = [(cx, cy)] + [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg + 1)]
        cols = []
        for _px, py in pts:
            t = (py - (cy - r)) / (2.0 * r)
            cols.append(tuple(top[i] + (bottom[i] - top[i]) * t for i in range(4)))
        batch = batch_for_shader(self._smooth, 'TRI_FAN', {"pos": [(px, self._y(py)) for px, py in pts], "color": cols})
        self._smooth.bind()
        batch.draw(self._smooth)

    def circle_outline(self, cx, cy, r, color, width=1.0, seg=28):
        pts = [(cx + r * math.cos(2 * math.pi * i / seg), self._y(cy + r * math.sin(2 * math.pi * i / seg))) for i in range(seg + 1)]
        batch = batch_for_shader(self._flat, 'LINE_STRIP', {"pos": pts})
        gpu.state.line_width_set(width)
        self._flat.bind()
        self._flat.uniform_float("color", color)
        batch.draw(self._flat)
        gpu.state.line_width_set(1.0)

    def line(self, x0, y0, x1, y1, color, width=1.0):
        batch = batch_for_shader(self._flat, 'LINES', {"pos": [(x0, self._y(y0)), (x1, self._y(y1))]})
        gpu.state.line_width_set(width)
        self._flat.bind()
        self._flat.uniform_float("color", color)
        batch.draw(self._flat)
        gpu.state.line_width_set(1.0)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        self._fan([(x0, self._y(y0)), (x1, self._y(y1)), (x2, self._y(y2))], color)

    def text(self, x, y, s, color, size=12, bold=False):
        """x, y: the left end of the text and the middle of its line."""
        fid = font(bold)
        blf.size(fid, size)
        _w, th = blf.dimensions(fid, "Ag")
        blf.position(fid, x, self._y(y) - th * 0.5 + 1, 0)
        blf.color(fid, *color)
        blf.draw(fid, s)

    def text_width(self, s, size=12, bold=False):
        fid = font(bold)
        blf.size(fid, size)
        return blf.dimensions(fid, s)[0]

    def text_center(self, x, y, w, s, color, size=12, bold=False):
        self.text(x + (w - self.text_width(s, size, bold)) * 0.5, y, s, color, size, bold)


# ---------------------------------------------------------------------------------------------------------------- canvases

def sig(w):
    """A widget's identity across redraws (the layout is rebuilt every time, so the dictionaries themselves change)."""
    return None if w is None else (w["kind"], w.get("label"), w.get("key"), w["x"], w["y"])


class Canvas:
    """A panel that fills a canvas area. Subclasses fill `self.widgets` in layout() and draw them in draw()."""
    name = "Canvas"
    background = c8(171, 168, 166)

    def __init__(self):
        self.hover = None      # the widget under the mouse
        self.pressed = None    # the widget a mouse button went down on
        self.widgets = []
        self.editing = None    # the text field being typed into
        self.edit_text = ""
        self.edit_commit = None
        self.drag = None       # a callback that follows the mouse while the left button is held on a widget

    # --- to override
    def layout(self, width, height):
        self.widgets = []

    def draw_widget(self, p, w, state):
        pass

    # --- the common part
    def draw(self, region):
        p = Painter(region)
        gpu.state.blend_set('ALPHA')
        p.rect(0, 0, p.w, p.h, self.background)
        self.layout(p.w, p.h)
        hover, pressed = sig(self.hover), sig(self.pressed)
        for w in self.widgets:
            ws = sig(w)
            state = 'pressed' if ws == pressed and ws == hover else ('hover' if ws == hover else 'normal')
            self.draw_widget(p, w, state)
        gpu.state.blend_set('NONE')

    def widget_at(self, x, y):
        for w in reversed(self.widgets):
            if w.get("action") is not None and w["x"] <= x < w["x"] + w["w"] and w["y"] <= y < w["y"] + w["h"]:
                return w
        return None

    def on_event(self, event, area, region):
        """Returns True when the event was used."""
        x = event.mouse_region_x
        y = region.height - event.mouse_region_y   # top-left origin
        self.layout(region.width, region.height)   # (the widgets as they are drawn now; the previous list may be from before a change)
        hit = self.widget_at(x, y)
        used = False
        if event.type == 'MOUSEMOVE':
            if self.pressed is not None and self.pressed.get("drag"):
                self.pressed["drag"](bpy.context, self.pressed, x, y)   # a widget that follows the mouse (the timeline ruler)
                area.tag_redraw()
                return True
            if sig(hit) != sig(self.hover):
                self.hover = hit
                area.tag_redraw()
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.pressed = hit
            if hit is not None:
                used = True
                if hit.get("drag"):
                    hit["drag"](bpy.context, hit, x, y)
                area.tag_redraw()
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            was, self.pressed = self.pressed, None
            area.tag_redraw()
            if was is not None and was.get("drag"):
                used = True
            elif was is not None and sig(was) == sig(hit):
                self.activate(hit, bpy.context)
                used = True
        return used

    # --- typing into a field: the Softimage value boxes and the command line
    def begin_edit(self, widget, text, commit):
        self.editing, self.edit_text, self.edit_commit = widget, text, commit
        _text_state["canvas"] = self
        bpy.ops.siwk.text_input('INVOKE_DEFAULT')

    def end_edit(self, commit):
        w, text, fn = self.editing, self.edit_text, self.edit_commit
        self.editing, self.edit_text, self.edit_commit = None, "", None
        if commit and fn is not None:
            fn(text)

    def activate(self, widget, context):
        action = widget.get("action")
        if callable(action):
            action(context)
        elif isinstance(action, str):
            try:
                bpy.ops.wm.call_menu(name=action)
            except RuntimeError:
                pass


_text_state = {}


class SIWK_OT_text_input(Operator):
    """Types into the field of a custom-drawn panel"""
    bl_idname = "siwk.text_input"
    bl_label = "Type into a Softimage field"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        self._canvas = _text_state.get("canvas")
        self._area = context.area
        if self._canvas is None or self._canvas.editing is None:
            return {'CANCELLED'}
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        c = self._canvas
        if c.editing is None:
            return {'FINISHED'}
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 'TIMER', 'TIMER_REPORT'}:
            return {'RUNNING_MODAL'}
        if event.value == 'PRESS' or event.value == 'CLICK':
            if event.type == 'ESC':
                c.end_edit(False)
            elif event.type in {'RET', 'NUMPAD_ENTER'}:
                c.end_edit(True)
            elif event.type == 'BACK_SPACE':
                c.edit_text = c.edit_text[:-1]
            elif event.type == 'DEL':
                c.edit_text = ""
            elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
                c.end_edit(True)   # a click elsewhere takes the value
                self._area.tag_redraw()
                return {'FINISHED'}
            elif event.unicode and event.unicode.isprintable():
                c.edit_text += event.unicode
            self._area.tag_redraw()
            if c.editing is None:
                return {'FINISHED'}
        return {'RUNNING_MODAL'}


def view3d_context():
    """Keyword arguments for context.temp_override that put an operator in a 3D view: the buttons of the panels are clicked in a canvas area, and many operators need a 3D view."""
    win = bpy.context.window
    if win is None:
        return {}
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if region is not None:
                return {"window": win, "screen": win.screen, "area": area, "region": region}
    return {}


def run_op(idname, **kw):
    """Runs a Blender operator ('mesh.bevel') from a panel button, in a 3D view; operators that cannot run here are ignored."""
    mod, fn = idname.split(".")
    try:
        with bpy.context.temp_override(**view3d_context()):
            getattr(getattr(bpy.ops, mod), fn)(**kw)
    except RuntimeError:
        pass


def register_canvas(area, canvas):
    _registry[area.as_pointer()] = canvas
    area.tag_redraw()


def canvas_of(area):
    return _registry.get(area.as_pointer()) if area is not None else None


def forget_canvases():
    _registry.clear()


def prepare_area(area):
    """Turns an area into a canvas host: the Spreadsheet editor with every region but the main one hidden."""
    area.type = HOST_TYPE
    space = area.spaces.active
    for attr in ("show_region_header", "show_region_toolbar", "show_region_ui", "show_region_footer", "show_region_channels", "show_region_tool_header"):
        if hasattr(space, attr):
            try:
                setattr(space, attr, False)
            except (AttributeError, TypeError):
                pass


def _draw():
    context = bpy.context
    canvas = canvas_of(context.area)
    if canvas is not None and context.region is not None:
        canvas.draw(context.region)


class SIWK_OT_canvas_event(Operator):
    """Sends the mouse to the custom-drawn Softimage panel under it"""
    bl_idname = "siwk.canvas_event"
    bl_label = "Softimage Panel Event"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        canvas = canvas_of(context.area)
        if os.environ.get("SIWK_DEBUG_EVENTS") and event.type != 'MOUSEMOVE':
            with open(os.environ["SIWK_DEBUG_EVENTS"], "a", encoding="utf-8") as f:
                f.write("%s %s canvas=%s at (%d,%d) region h=%d\n" % (event.type, event.value, canvas.name if canvas else None, event.mouse_region_x, event.mouse_region_y, context.region.height))
        if canvas is None:
            return {'PASS_THROUGH'}
        used = canvas.on_event(event, context.area, context.region)
        return {'FINISHED'} if used else {'PASS_THROUGH'}


classes = (SIWK_OT_canvas_event, SIWK_OT_text_input)


def register():
    global _handle
    for cls in classes:
        bpy.utils.register_class(cls)
    _handle = HOST_SPACE.draw_handler_add(_draw, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    global _handle
    if _handle is not None:
        HOST_SPACE.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
    forget_canvases()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
