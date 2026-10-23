# SPDX-License-Identifier: GPL-3.0-or-later
"""The Softimage workspace, laid out like Softimage's default layout (Application/layouts/default.xsily):

    +--------+---------------------------+--------+
    | toolbar|   Top        User         |  MCP   |
    | panel  |   Front      Right        |        |
    |        +---------------------------+        |
    |        |   timeline / time range   |        |
    +--------+---------------------------+--------+
    |   command line / playback / animation bar    |
    +----------------------------------------------+

The toolbar panel, the MCP, the timeline and the bottom bar are canvases (custom-drawn, see canvas.py); the four views are Blender's own 3D views, wireframe in the
orthographic ones and shaded in the User view, as Softimage opens them. The layout is built one step per timer tick: Blender only gives areas their new sizes when it redraws.
"""

import math

import bpy
from bpy.types import Operator
from mathutils import Euler

from . import canvas, panel_view
from .panel_left import LeftPanel
from .panel_mcp import McpPanel
from .panel_top import TopPanel
from .panel_timeline import TimelinePanel
from .panel_bottom import BottomPanel

WORKSPACE_NAME = "Softimage"
build_done = True   # False while build() is working through its timer ticks

# pixel sizes of Softimage's default layout at 100 % scale
LEFT_W, MCP_W, BOTTOM_H, TIMELINE_H, TOP_H = 106, 136, 70, 50, 24


class Blank(canvas.Canvas):
    """A canvas that only shows its name (the panels that are not drawn yet)."""

    def __init__(self, name):
        super().__init__()
        self.name = name

    def draw_widget(self, p, w, state):
        p.text(w["x"], w["y"], w["label"], canvas.c8(60, 60, 60), size=12)

    def layout(self, width, height):
        self.widgets = [{"x": 8, "y": 12, "w": 10, "h": 10, "label": self.name, "action": None}]


def _window_region(area):
    return next((r for r in area.regions if r.type == 'WINDOW'), None)


def _areas(context):
    return list(context.window.screen.areas)


def _by_ptr(context, ptr):
    return next((a for a in context.window.screen.areas if a.as_pointer() == ptr), None)


def _split(context, area, direction, factor=0.5):
    """Splits `area` at `factor` of the way from its left (or bottom) edge and returns the pointers of the two pieces. Blender gives the new areas their positions only when it
    redraws, so the caller yields once and then tells them apart with _order()."""
    window, screen = context.window, context.window.screen
    old_ptr = area.as_pointer()
    before = {a.as_pointer() for a in screen.areas}
    with context.temp_override(window=window, screen=screen, area=area, region=_window_region(area)):
        bpy.ops.screen.area_split(direction=direction, factor=factor)
    new_ptr = next(a.as_pointer() for a in context.window.screen.areas if a.as_pointer() not in before)
    return old_ptr, new_ptr


def _order(context, ptr_a, ptr_b, direction):
    """(low, high) = (the left or bottom piece, the right or top piece), once Blender has laid the areas out."""
    pair = [_by_ptr(context, ptr_a), _by_ptr(context, ptr_b)]
    key = (lambda a: a.x) if direction == 'VERTICAL' else (lambda a: a.y)
    pair.sort(key=key)
    return pair[0], pair[1]


def _join_pair(context):
    """Joins one pair of neighbouring areas that share a whole edge; returns False when there is nothing left to join."""
    areas = _areas(context)
    if len(areas) < 2:
        return False
    for a in areas:
        for b in areas:
            if a is b:
                continue
            stacked = abs(a.x - b.x) <= 3 and abs(a.width - b.width) <= 3 and (abs(a.y + a.height - b.y) <= 4 or abs(b.y + b.height - a.y) <= 4)
            side_by_side = abs(a.y - b.y) <= 3 and abs(a.height - b.height) <= 3 and (abs(a.x + a.width - b.x) <= 4 or abs(b.x + b.width - a.x) <= 4)
            if stacked or side_by_side:
                with context.temp_override(window=context.window, screen=context.window.screen, area=a):
                    bpy.ops.screen.area_join(source_xy=(a.x + 30, a.y + 30), target_xy=(b.x + 30, b.y + 30))
                return True
    return False


def _set_view(context, area, kind):
    space = area.spaces.active
    region = _window_region(area)
    with context.temp_override(window=context.window, screen=context.window.screen, area=area, region=region):
        if kind == 'USER':
            space.region_3d.view_perspective = 'PERSP'
            space.region_3d.view_rotation = Euler((math.radians(62.0), 0.0, math.radians(38.0)), 'XYZ').to_quaternion()
            space.shading.type = 'SOLID'
        else:
            bpy.ops.view3d.view_axis(type=kind)
            space.shading.type = 'WIREFRAME'


def _make_canvas(area, panel):
    canvas.prepare_area(area)
    canvas.register_canvas(area, panel)


def _steps(on_done):
    context = bpy.context
    existing = bpy.data.workspaces.get(WORKSPACE_NAME)
    if existing is not None:
        context.window.workspace = existing
        if on_done:
            on_done(existing)
        return
    bpy.ops.workspace.duplicate()
    yield   # (the window switches to the copy at the next tick; renaming before that would rename the original)
    ws = context.window.workspace
    ws.name = WORKSPACE_NAME
    yield

    # ---- one area to carve up: join the copied layout's areas together
    for _ in range(8):
        if not _join_pair(context):
            break
        yield
    root = max(_areas(context), key=lambda a: a.width * a.height)
    root.type = 'VIEW_3D'
    yield

    # ---- the menu bar along the top
    pa, pb = _split(context, root, 'HORIZONTAL', (root.height - TOP_H) / float(root.height))
    yield
    rest0, topbar = _order(context, pa, pb, 'HORIZONTAL')
    # ---- the bottom bar (command line, playback, animation)
    pa, pb = _split(context, rest0, 'HORIZONTAL', BOTTOM_H / float(rest0.height))
    yield
    bottom, upper = _order(context, pa, pb, 'HORIZONTAL')
    # ---- the toolbar panel on the left
    pa, pb = _split(context, upper, 'VERTICAL', LEFT_W / float(upper.width))
    yield
    left, rest = _order(context, pa, pb, 'VERTICAL')
    # ---- the middle (views and timeline) and the MCP on the right
    pa, pb = _split(context, rest, 'VERTICAL', (rest.width - MCP_W) / float(rest.width))
    yield
    middle, mcp = _order(context, pa, pb, 'VERTICAL')
    # ---- the timeline strip under the views
    pa, pb = _split(context, middle, 'HORIZONTAL', TIMELINE_H / float(middle.height))
    yield
    timeline, view = _order(context, pa, pb, 'HORIZONTAL')
    canvas_ptrs = {topbar.as_pointer(), bottom.as_pointer(), left.as_pointer(), mcp.as_pointer(), timeline.as_pointer()}
    pa, pb = _split(context, view, 'VERTICAL', 0.5)
    yield
    for col in [a for a in _areas(context) if a.as_pointer() not in canvas_ptrs]:
        _split(context, col, 'HORIZONTAL', 0.5)
        yield
    yield

    # ---- the canvases and the views
    _make_canvas(_by_ptr(context, left.as_pointer()), LeftPanel("Animate"))
    _make_canvas(_by_ptr(context, mcp.as_pointer()), McpPanel())
    _make_canvas(_by_ptr(context, timeline.as_pointer()), TimelinePanel())
    _make_canvas(_by_ptr(context, bottom.as_pointer()), BottomPanel())
    _make_canvas(_by_ptr(context, topbar.as_pointer()), TopPanel())
    yield
    quad = [a for a in _areas(context) if a.as_pointer() not in canvas_ptrs and a.type == 'VIEW_3D' and a.width > 0]
    if len(quad) == 4:
        quad.sort(key=lambda a: (-a.y, a.x))   # top row first, left to right
        top_row = sorted(quad[:2], key=lambda a: a.x)
        bottom_row = sorted(quad[2:], key=lambda a: a.x)
        # top-left Top, top-right User, bottom-left Front, bottom-right Right: Softimage's default
        for area, kind, letter in zip(top_row + bottom_row, ('TOP', 'USER', 'FRONT', 'RIGHT'), "ABCD"):
            _set_view(context, area, kind)
            sp = area.spaces.active
            sp.show_region_header = False      # Softimage's own strip is drawn over the view instead (panel_view.py)
            sp.show_region_toolbar = False
            sp.overlay.show_text = False
            sp.shading.background_type = 'VIEWPORT'          # Softimage's mid-grey viewport background
            sp.shading.background_color = (0.216, 0.216, 0.216)   # linear: displays as Softimage's 128 grey
            panel_view.register_view(area, letter)
    if on_done:
        on_done(ws)


def build(on_done=None):
    """Creates the Softimage workspace (or switches to it when it exists). It finishes a few timer ticks later; on_done(workspace) is called then."""
    global build_done
    build_done = False

    def finished(ws):
        global build_done
        build_done = True
        if on_done:
            on_done(ws)

    gen = _steps(finished)

    def tick():
        try:
            next(gen)
        except StopIteration:
            return None
        except (RuntimeError, ReferenceError, StopIteration) as exc:
            print("Softimage Workflow Kit: could not build the workspace:", exc)
            finished(None)
            return None
        return 0.15

    bpy.app.timers.register(tick, first_interval=0.05)


class SIWK_OT_create_workspace(Operator):
    """Open the Softimage workspace: toolbar panel, Top / User / Front / Right views, MCP and the bottom bars, laid out like Softimage's default"""
    bl_idname = "siwk.create_workspace"
    bl_label = "Create Softimage Workspace"

    def execute(self, context):
        build()
        self.report({'INFO'}, "Building the Softimage workspace")
        return {'FINISHED'}


class SIWK_OT_apply_navigation_prefs(Operator):
    """Set Blender's navigation preferences the way Softimage navigates: turntable orbit, dolly zoom along the horizontal. Changes your own preferences"""
    bl_idname = "siwk.apply_navigation_prefs"
    bl_label = "Apply Softimage Navigation Preferences"

    def execute(self, context):
        inputs = context.preferences.inputs
        inputs.view_rotate_method = 'TURNTABLE'
        inputs.view_zoom_method = 'DOLLY'
        inputs.view_zoom_axis = 'HORIZONTAL'
        self.report({'INFO'}, "Navigation: turntable orbit, horizontal dolly")
        return {'FINISHED'}


classes = (SIWK_OT_create_workspace, SIWK_OT_apply_navigation_prefs)


def register():
    canvas.register()
    panel_view.register()
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    panel_view.unregister()
    canvas.unregister()
