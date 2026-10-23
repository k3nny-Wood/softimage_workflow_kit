# SPDX-License-Identifier: GPL-3.0-or-later
"""Softimage-style pie menus: Z display, ` view, Tab mode, . transform, D modeling (it follows the selection mode and what is selected).

Blender's pie slots run West, East, South, North, North-West, North-East, South-West, South-East, which is the order the entries are added in.
"""

import bpy
from bpy.types import Menu


def _op(pie, label, idname, **props):
    op = pie.operator(idname, text=label)
    for key, value in props.items():
        setattr(op, key, value)
    return op


class SIWK_MT_pie_display(Menu):
    bl_idname = "SIWK_MT_pie_display"
    bl_label = "Display"

    def draw(self, context):
        pie = self.layout.menu_pie()
        _op(pie, "Wireframe", "siwk.shading", type='WIREFRAME')
        _op(pie, "Shaded", "siwk.shading", type='SHADED')
        _op(pie, "Textured", "siwk.shading", type='TEXTURED')
        _op(pie, "Realtime", "siwk.shading", type='REALTIME')
        _op(pie, "Constant", "siwk.shading", type='CONSTANT')
        _op(pie, "Rendered", "siwk.shading", type='RENDERED')
        _op(pie, "Wire on Shaded", "siwk.shading", type='WIRE_ON_SHADED')
        pie.operator("siwk.toggle_grid", text="Grid")


class SIWK_MT_pie_view(Menu):
    bl_idname = "SIWK_MT_pie_view"
    bl_label = "View"

    def draw(self, context):
        pie = self.layout.menu_pie()
        _op(pie, "Front", "siwk.view_type", type='FRONT')
        _op(pie, "Right", "siwk.view_type", type='RIGHT')
        _op(pie, "User", "siwk.view_type", type='USER')
        _op(pie, "Top", "siwk.view_type", type='TOP')
        pie.operator("view3d.view_all", text="Frame All")
        pie.operator("view3d.view_selected", text="Frame Selection")
        pie.operator("screen.screen_full_area", text="Maximize")
        _op(pie, "Isometric", "siwk.view_type", type='ISO')


class SIWK_MT_pie_mode(Menu):
    bl_idname = "SIWK_MT_pie_mode"
    bl_label = "Mode"

    def draw(self, context):
        pie = self.layout.menu_pie()
        _op(pie, "Edge", "siwk.component_mode", mode='EDGE')
        _op(pie, "Polygon", "siwk.component_mode", mode='FACE')
        _op(pie, "Object", "siwk.component_mode", mode='OBJECT')
        _op(pie, "Vertex", "siwk.component_mode", mode='VERT')
        _op(pie, "Move", "wm.tool_set_by_id", name="builtin.move")
        _op(pie, "Rotate", "wm.tool_set_by_id", name="builtin.rotate")
        _op(pie, "Select", "wm.tool_set_by_id", name="builtin.select_box")
        _op(pie, "Scale", "wm.tool_set_by_id", name="builtin.scale")


class SIWK_MT_pie_transform(Menu):
    bl_idname = "SIWK_MT_pie_transform"
    bl_label = "Transform"

    def draw(self, context):
        pie = self.layout.menu_pie()
        _op(pie, "View", "transform.select_orientation", orientation='VIEW')
        _op(pie, "Local", "transform.select_orientation", orientation='LOCAL')
        _op(pie, "Parent", "transform.select_orientation", orientation='PARENT')
        _op(pie, "Global", "transform.select_orientation", orientation='GLOBAL')
        pie.operator("siwk.proportional", text="Soft Selection")
        _op(pie, "Normal", "transform.select_orientation", orientation='NORMAL')
        _op(pie, "Invert Selection", "siwk.select_all", action='INVERT')
        _op(pie, "Unselect All", "siwk.select_all", action='DESELECT')


class SIWK_MT_pie_modeling(Menu):
    """The operations that fit what is being edited: objects, or the polygons / edges / vertices selected, or the geometry tools when nothing is"""
    bl_idname = "SIWK_MT_pie_modeling"
    bl_label = "Modeling"

    def draw(self, context):
        pie = self.layout.menu_pie()
        obj = context.active_object
        if context.mode != 'EDIT_MESH' or obj is None or obj.type != 'MESH':
            self._objects(pie)
            return
        mode = context.tool_settings.mesh_select_mode
        me = obj.data
        nothing = me.total_vert_sel == 0
        self.bl_label = "Polygon" if mode[2] else ("Edge" if mode[1] else "Vertex")
        if nothing:
            self._tools(pie)
        elif mode[2]:
            self._polygons(pie)
        elif mode[1]:
            self._edges(pie)
        else:
            self._vertices(pie)

    @staticmethod
    def _objects(pie):
        _op(pie, "Duplicate", "siwk.duplicate")
        pie.operator("object.join", text="Merge")
        _op(pie, "Delete", "siwk.delete")
        _op(pie, "Freeze", "object.convert", target='MESH')
        pie.operator("object.transform_apply", text="Freeze Transform")
        _op(pie, "Subdivision +", "object.subdivision_set", level=1, relative=True)
        _op(pie, "Subdivision -", "object.subdivision_set", level=-1, relative=True)
        _op(pie, "Unselect All", "siwk.select_all", action='DESELECT')

    @staticmethod
    def _tools(pie):
        pie.operator("mesh.edge_face_add", text="Add Edge / Polygon")
        _op(pie, "Knife", "wm.tool_set_by_id", name="builtin.knife")
        _op(pie, "Poly Build", "wm.tool_set_by_id", name="builtin.poly_build")
        pie.operator("mesh.loopcut_slide", text="Loop Cut")
        pie.operator("mesh.primitive_vert_add", text="Add Vertex")
        _op(pie, "Select Box", "wm.tool_set_by_id", name="builtin.select_box")
        pie.operator("mesh.edge_split", text="Split Edge")
        _op(pie, "Select All", "siwk.select_all", action='SELECT')

    @staticmethod
    def _polygons(pie):
        pie.operator("mesh.bevel", text="Bevel")
        pie.operator("view3d.edit_mesh_extrude_move_normal", text="Extrude Along Normal")
        _op(pie, "Delete", "siwk.delete")
        pie.operator("mesh.extrude_region_move", text="Extrude")
        pie.operator("mesh.subdivide", text="Subdivide")
        pie.operator("mesh.bridge_edge_loops", text="Bridge")
        pie.operator("mesh.dissolve_faces", text="Dissolve")
        pie.operator("mesh.inset", text="Inset")

    @staticmethod
    def _edges(pie):
        pie.operator("mesh.bevel", text="Bevel")
        pie.operator("mesh.extrude_region_move", text="Extrude Edge")
        _op(pie, "Delete", "siwk.delete")
        pie.operator("mesh.subdivide", text="Subdivide")
        pie.operator("mesh.edge_rotate", text="Spin Edge")
        pie.operator("mesh.loop_multi_select", text="Edge Loop")
        pie.operator("mesh.dissolve_edges", text="Dissolve")
        _op(pie, "Collapse", "mesh.merge", type='COLLAPSE')

    @staticmethod
    def _vertices(pie):
        pie.operator("mesh.remove_doubles", text="Weld")
        pie.operator("mesh.bevel", text="Bevel")
        _op(pie, "Delete", "siwk.delete")
        _op(pie, "Collapse", "mesh.merge", type='COLLAPSE')
        pie.operator("mesh.dissolve_verts", text="Dissolve")
        _op(pie, "Disconnect", "mesh.edge_split", type='VERT')
        pie.operator("mesh.select_more", text="Grow Selection")
        pie.operator("mesh.select_less", text="Shrink Selection")


classes = (SIWK_MT_pie_display, SIWK_MT_pie_view, SIWK_MT_pie_mode, SIWK_MT_pie_transform, SIWK_MT_pie_modeling)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
