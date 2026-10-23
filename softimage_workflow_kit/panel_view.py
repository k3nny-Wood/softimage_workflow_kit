# SPDX-License-Identifier: GPL-3.0-or-later
"""The strip across the top of each Softimage viewport: the viewport letter, the view type (User / Top / Front / Right), a few buttons, the camera and the eye, X Y Z,
and on the right the display type (Shaded, Wireframe ...) and the maximize button. Drawn over Blender's own 3D view, whose header is hidden in the Softimage workspace."""

import bpy
import gpu
from bpy.types import Operator

from .canvas import Painter, c8, text_width

HEIGHT = 20
GREEN = c8(128, 168, 147)
EDGE = c8(120, 118, 116)
TEXT = c8(20, 20, 20)

_views = {}   # area pointer -> the viewport's letter (A, B, C, D)
_handle = None


def register_view(area, letter):
    _views[area.as_pointer()] = letter
    area.tag_redraw()


def forget_views():
    _views.clear()


def view_label(space):
    rv = space.region_3d
    if rv.view_perspective != 'ORTHO':
        return "User"
    q = rv.view_rotation
    known = {"Top": (1, 0, 0, 0), "Bottom": (0, 1, 0, 0), "Front": (0.7071, 0.7071, 0, 0), "Back": (0, 0, 0.7071, 0.7071), "Right": (0.5, 0.5, 0.5, 0.5), "Left": (0.5, 0.5, -0.5, -0.5)}
    for name, k in known.items():
        if abs(abs(q[0] * k[0] + q[1] * k[1] + q[2] * k[2] + q[3] * k[3]) - 1.0) < 0.02:
            return name
    return "User"


def display_label(space):
    sh = space.shading
    if sh.type == 'WIREFRAME':
        return "Wireframe"
    if sh.type == 'MATERIAL':
        return "Realtime"
    if sh.type == 'RENDERED':
        return "Rendered"
    if space.overlay.show_wireframes:
        return "Wireframe on Shaded"
    if sh.light == 'FLAT':
        return "Constant"
    if sh.color_type == 'TEXTURE':
        return "Textured"
    return "Shaded"


def layout(width, space, letter):
    """The widgets of a viewport header: (kind, x, y, w, h, label, action)."""
    ws = [("letter", 3, 2, 17, 17, letter, None),
          ("dropdown", 22, 2, 138, 17, view_label(space), "SIWK_MT_viewtype")]
    for i in range(4):
        ws.append(("square", 164 + i * 19, 3, 16, 15, "", None))
    ws.append(("camera", 246, 2, 24, 17, "", None))
    ws.append(("eye", 274, 2, 24, 17, "", "SIWK_MT_show"))
    ws.append(("xyz", 304, 2, 40, 17, "X Y Z", None))
    disp = display_label(space)
    ws.append(("display", max(360, width - 190), 2, 120, 17, disp, "SIWK_MT_display"))
    ws.append(("maximize", width - 24, 2, 20, 17, "", "maximize"))
    return ws


def _draw():
    context = bpy.context
    area = context.area
    letter = _views.get(area.as_pointer()) if area else None
    if letter is None or context.region is None or context.space_data is None:
        return
    region, space = context.region, context.space_data
    p = Painter(region)
    gpu.state.blend_set('ALPHA')
    p.vgrad(0, 0, p.w, HEIGHT, c8(176, 173, 172), c8(160, 157, 156))
    p.rect(0, HEIGHT - 1, p.w, 1, c8(104, 102, 101))
    for kind, x, y, w, h, label, _action in layout(p.w, space, letter):
        if kind == "letter":
            p.circle_grad(x + w / 2.0, y + h / 2.0, h / 2.0, c8(210, 207, 206), c8(160, 157, 156))
            p.circle_outline(x + w / 2.0, y + h / 2.0, h / 2.0, c8(60, 60, 60), 1.5)
            p.text_center(x, y + h * 0.5, w, label, TEXT, size=12, bold=True)
        elif kind == "dropdown":
            p.round_rect(x, y, w, h, 5, GREEN)
            p.round_outline(x, y, w, h, 5, c8(96, 128, 108))
            p.text_center(x, y + h * 0.5, w - 14, label, TEXT, size=13, bold=True)
            p.triangle(x + w - 14, y + h * 0.5 - 3, x + w - 5, y + h * 0.5 - 3, x + w - 9.5, y + h * 0.5 + 3, c8(20, 40, 30))
        elif kind == "square":
            p.round_rect(x, y, w, h, 3, c8(166, 163, 162))
            p.round_outline(x, y, w, h, 3, c8(130, 128, 127))
        elif kind == "camera":
            p.rect(x + 3, y + 3, 12, 8, c8(40, 40, 40)); p.triangle(x + 15, y + 5, x + 20, y + 3, x + 20, y + 11, c8(40, 40, 40))
            p.triangle(x + 8, y + 13, x + 14, y + 13, x + 11, y + 16, c8(40, 40, 40))
        elif kind == "eye":
            p.circle_outline(x + 11, y + 7, 6, c8(40, 40, 40), 1.6); p.circle(x + 11, y + 7, 2.5, c8(40, 40, 40))
            p.triangle(x + 8, y + 13, x + 14, y + 13, x + 11, y + 16, c8(40, 40, 40))
        elif kind == "xyz":
            p.text(x, y + h * 0.5, label, c8(40, 40, 40), size=12, bold=True)
        elif kind == "display":
            p.text_center(x, y + h * 0.5, w, label, TEXT, size=13, bold=True)
            p.triangle(x + w * 0.5 - 4, y + h - 3, x + w * 0.5 + 4, y + h - 3, x + w * 0.5, y + h + 1, c8(20, 20, 20))
        elif kind == "maximize":
            p.round_outline(x + 3, y + 2, 14, 12, 2, c8(50, 50, 50), 1.6)
            p.round_rect(x + 8, y + 6, 8, 8, 1, c8(50, 50, 50))
    gpu.state.blend_set('NONE')


class SIWK_OT_view_header(Operator):
    """A click on the strip across the top of a Softimage viewport"""
    bl_idname = "siwk.view_header"
    bl_label = "Viewport Header"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        area, region, space = context.area, context.region, context.space_data
        letter = _views.get(area.as_pointer()) if area else None
        if letter is None or region is None or space is None or space.type != 'VIEW_3D':
            return {'PASS_THROUGH'}
        y = region.height - event.mouse_region_y
        if not 0 <= y < HEIGHT:
            return {'PASS_THROUGH'}
        x = event.mouse_region_x
        for kind, wx, wy, ww, wh, label, action in layout(region.width, space, letter):
            if wx <= x < wx + ww and wy <= y < wy + wh and action:
                if action == "maximize":
                    bpy.ops.screen.screen_full_area()
                else:
                    bpy.ops.wm.call_menu(name=action)
                return {'FINISHED'}
        return {'FINISHED'}   # (the strip itself swallows the click, so it does not select what is under it)


classes = (SIWK_OT_view_header,)


def register():
    global _handle
    for cls in classes:
        bpy.utils.register_class(cls)
    _handle = bpy.types.SpaceView3D.draw_handler_add(_draw, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    global _handle
    if _handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
    forget_views()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
