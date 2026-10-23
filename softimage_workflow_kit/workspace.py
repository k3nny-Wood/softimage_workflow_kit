# SPDX-License-Identifier: GPL-3.0-or-later
"""The Softimage workspace: four views (Top, User / Front, Right), wireframe in the orthographic ones and shaded in the User view, as Softimage opens."""

import math

import bpy
from bpy.types import Operator
from mathutils import Euler

WORKSPACE_NAME = "Softimage"
build_done = True   # False while build() is working through its timer ticks


def _window_region(area):
    return next((r for r in area.regions if r.type == 'WINDOW'), None)


def _view_areas(screen):
    return [a for a in screen.areas if a.type == 'VIEW_3D']


def _split(context, area, direction):
    """Splits `area` in half and returns the new area."""
    window, screen = context.window, context.window.screen
    before = {a.as_pointer() for a in screen.areas}
    with context.temp_override(window=window, screen=screen, area=area, region=_window_region(area)):
        bpy.ops.screen.area_split(direction=direction, factor=0.5)
    created = [a for a in context.window.screen.areas if a.as_pointer() not in before]
    return created[0] if created else None


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


def _steps(on_done):
    """The workspace is built one step per timer tick: Blender only gives a new area its size when it redraws, so each split has to see the layout the one before made."""
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
    views = _view_areas(context.window.screen)
    if not views:
        if on_done:
            on_done(ws)
        return
    main = max(views, key=lambda a: a.width * a.height)
    _split(context, main, 'VERTICAL')
    yield
    columns = sorted((a for a in _view_areas(context.window.screen) if a.width > 0), key=lambda a: a.x)
    for col in columns[-2:]:
        _split(context, col, 'HORIZONTAL')
        yield
    yield
    areas = [a for a in _view_areas(context.window.screen) if a.width > 0]
    if len(areas) == 4:
        areas.sort(key=lambda a: (-a.y, a.x))   # top row first, left to right
        top_row = sorted(areas[:2], key=lambda a: a.x)
        bottom_row = sorted(areas[2:], key=lambda a: a.x)
        # top-left Top, top-right User, bottom-left Front, bottom-right Right: Softimage's default
        for area, kind in zip(top_row + bottom_row, ('TOP', 'USER', 'FRONT', 'RIGHT')):
            _set_view(context, area, kind)
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
        except RuntimeError as exc:
            print("Softimage Workflow Kit: could not build the workspace:", exc)
            finished(None)
            return None
        return 0.15

    bpy.app.timers.register(tick, first_interval=0.05)


class SIWK_OT_create_workspace(Operator):
    """Open the Softimage workspace: Top, User, Front and Right views in a 2 x 2 layout"""
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
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
