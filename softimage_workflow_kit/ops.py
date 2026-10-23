# SPDX-License-Identifier: GPL-3.0-or-later
"""Operators the keymap and the pie menus call: the Softimage-named commands that need a little logic on top of Blender's own operators."""

import math

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator
from mathutils import Euler


def _view3d_space(context):
    space = getattr(context, "space_data", None)
    return space if space is not None and space.type == 'VIEW_3D' else None


class SIWK_OT_nav_hold(Operator):
    """S is a hold in Softimage: S + left drag orbits, S + middle drag pans, S + right drag dollies. The key itself does nothing"""
    bl_idname = "siwk.nav_hold"
    bl_label = "Navigate (hold S)"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}


class SIWK_OT_component_mode(Operator):
    """Object / Vertex / Edge / Polygon, from either mode (Softimage's 7 / 1 / 2 / 3)"""
    bl_idname = "siwk.component_mode"
    bl_label = "Component Mode"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(items=[('OBJECT', "Object", ""), ('VERT', "Vertex", "Point"), ('EDGE', "Edge", ""), ('FACE', "Polygon", "")], default='OBJECT')

    def execute(self, context):
        obj = context.active_object
        if self.mode == 'OBJECT':
            if obj and obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            return {'FINISHED'}
        if obj is None or obj.type != 'MESH':
            self.report({'INFO'}, "Select a mesh first")
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        context.tool_settings.mesh_select_mode = (self.mode == 'VERT', self.mode == 'EDGE', self.mode == 'FACE')
        return {'FINISHED'}


# the display types of Softimage's viewport menu, as Blender shading settings
_SHADING = {
    'WIREFRAME': ("Wireframe", 'WIREFRAME', {}),
    'SHADED': ("Shaded", 'SOLID', {'color_type': 'MATERIAL', 'light': 'STUDIO'}),
    'TEXTURED': ("Textured", 'SOLID', {'color_type': 'TEXTURE', 'light': 'STUDIO'}),
    'CONSTANT': ("Constant", 'SOLID', {'color_type': 'MATERIAL', 'light': 'FLAT'}),
    'REALTIME': ("Realtime", 'MATERIAL', {}),
    'RENDERED': ("Rendered", 'RENDERED', {}),
}


class SIWK_OT_shading(Operator):
    """Set the display type of the 3D view under the cursor (Softimage's Wireframe, Shaded, Textured, Constant, Realtime ...)"""
    bl_idname = "siwk.shading"
    bl_label = "Display Type"

    type: EnumProperty(items=[(k, v[0], "") for k, v in _SHADING.items()] + [('WIRE_ON_SHADED', "Wireframe on Shaded", "")], default='SHADED')

    @classmethod
    def poll(cls, context):
        return _view3d_space(context) is not None

    def execute(self, context):
        space = _view3d_space(context)
        sh = space.shading
        if self.type == 'WIRE_ON_SHADED':
            sh.type = 'SOLID'
            space.overlay.show_wireframes = not space.overlay.show_wireframes
            return {'FINISHED'}
        label, kind, extra = _SHADING[self.type]
        sh.type = kind
        for key, value in extra.items():
            setattr(sh, key, value)
        if kind != 'WIREFRAME':
            space.overlay.show_wireframes = False
        return {'FINISHED'}


class SIWK_OT_view_type(Operator):
    """Top / Front / Right / User view (Softimage's view types)"""
    bl_idname = "siwk.view_type"
    bl_label = "View Type"

    type: EnumProperty(items=[('TOP', "Top", ""), ('FRONT', "Front", ""), ('RIGHT', "Right", ""), ('USER', "User", ""), ('ISO', "Isometric", "")], default='USER')

    @classmethod
    def poll(cls, context):
        return _view3d_space(context) is not None

    def execute(self, context):
        space = _view3d_space(context)
        rv3d = space.region_3d
        if self.type in {'TOP', 'FRONT', 'RIGHT'}:
            bpy.ops.view3d.view_axis(type=self.type)
            if space.shading.type != 'WIREFRAME' and self.type != 'USER':
                space.shading.type = 'WIREFRAME'   # Softimage's orthographic views start as wireframe
        elif self.type == 'ISO':
            rv3d.view_perspective = 'ORTHO'
            rv3d.view_rotation = Euler((math.radians(54.7356), 0.0, math.radians(45.0)), 'XYZ').to_quaternion()
        else:
            rv3d.view_perspective = 'PERSP'
            if space.shading.type == 'WIREFRAME':
                space.shading.type = 'SOLID'
        return {'FINISHED'}


class SIWK_OT_toggle_grid(Operator):
    """Show / hide the grid (Softimage's G)"""
    bl_idname = "siwk.toggle_grid"
    bl_label = "Show/Hide Grid"

    @classmethod
    def poll(cls, context):
        return _view3d_space(context) is not None

    def execute(self, context):
        ov = _view3d_space(context).overlay
        ov.show_floor = not ov.show_floor
        return {'FINISHED'}


class SIWK_OT_proportional(Operator):
    """Soft selection: Blender's proportional editing, on or off (Softimage's proportional modeling)"""
    bl_idname = "siwk.proportional"
    bl_label = "Soft Selection"

    def execute(self, context):
        ts = context.tool_settings
        if context.mode == 'OBJECT':
            ts.use_proportional_edit_objects = not ts.use_proportional_edit_objects
            on = ts.use_proportional_edit_objects
        else:
            ts.use_proportional_edit = not ts.use_proportional_edit
            on = ts.use_proportional_edit
        self.report({'INFO'}, "Soft selection " + ("on" if on else "off"))
        return {'FINISHED'}


class SIWK_OT_select_all(Operator):
    """Select all / invert / deselect, in objects or in the components being edited"""
    bl_idname = "siwk.select_all"
    bl_label = "Select"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(items=[('SELECT', "All", ""), ('INVERT', "Invert", ""), ('DESELECT', "None", "")], default='SELECT')

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            bpy.ops.mesh.select_all(action=self.action)
        elif context.mode == 'OBJECT':
            bpy.ops.object.select_all(action=self.action)
        return {'FINISHED'}


class SIWK_OT_delete(Operator):
    """Delete the selected objects, or the selected points / edges / polygons"""
    bl_idname = "siwk.delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            mode = context.tool_settings.mesh_select_mode
            bpy.ops.mesh.delete(type='VERT' if mode[0] else ('EDGE' if mode[1] else 'FACE'))
        elif context.mode == 'OBJECT':
            bpy.ops.object.delete()
        return {'FINISHED'}


class SIWK_OT_duplicate(Operator):
    """Duplicate (Softimage's Ctrl+D) and move"""
    bl_idname = "siwk.duplicate"
    bl_label = "Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            return bpy.ops.mesh.duplicate_move('INVOKE_DEFAULT')
        return bpy.ops.object.duplicate_move('INVOKE_DEFAULT')


class SIWK_OT_open_prefs(Operator):
    """Open the kit's preferences"""
    bl_idname = "siwk.open_prefs"
    bl_label = "Softimage Workflow Kit Preferences"

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        return {'FINISHED'}


classes = (
    SIWK_OT_nav_hold, SIWK_OT_component_mode, SIWK_OT_shading, SIWK_OT_view_type, SIWK_OT_toggle_grid, SIWK_OT_proportional,
    SIWK_OT_select_all, SIWK_OT_delete, SIWK_OT_duplicate, SIWK_OT_open_prefs,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
