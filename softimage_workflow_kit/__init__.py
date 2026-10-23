# SPDX-License-Identifier: GPL-3.0-or-later
"""Softimage Workflow Kit: Softimage's keys, layout, menus and ways of working on top of Blender's own tools.

Nothing here writes to the user's preferences, theme or active keymap unless a button says so: everything the kit registers is removed again when it is switched off.
"""

import bpy
from bpy.props import BoolProperty

bl_info = {
    "name": "Softimage Workflow Kit",
    "author": "k3nny-Wood",
    "version": (0, 0, 2),
    "blender": (4, 5, 0),
    "description": "Softimage's workflow on top of Blender",
    "category": "Interface",
}

from . import keymap, ops, pies, workspace


def _use_keys_changed(self, context):
    keymap.unregister()
    if self.use_keys:
        keymap.register()


class SIWK_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    use_keys: BoolProperty(
        name="Softimage keys and pie menus",
        description="Turn off to get Blender's own keys back without disabling the add-on",
        default=True,
        update=_use_keys_changed,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "use_keys")
        col = layout.column(align=True)
        col.operator("siwk.create_workspace", icon='WORKSPACE')
        col.operator("siwk.apply_navigation_prefs", icon='VIEW_PAN')
        box = layout.box()
        box.label(text="Keys", icon='KEYINGSET')
        grid = box.grid_flow(columns=2, align=True)
        for line in (
            "S + drag: orbit (left), pan (middle), dolly (right)",
            "Q / W / E / R: select, move, rotate, scale",
            "1 / 2 / 3 / 7: vertex, edge, polygon, object",
            "4 / 5 / 6: wireframe, wire on shaded, shaded",
            "Space: maximize the view     F: frame selection",
            "T / V / I: top, user, isometric     G: grid",
            "B: soft selection     Ctrl+D: duplicate",
            "Pies:  Z display   `  view   Tab  mode   .  transform   D  modeling",
        ):
            grid.label(text=line)


_classes = (SIWK_AddonPreferences,)


def _prefs():
    try:
        return bpy.context.preferences.addons[__package__].preferences
    except (KeyError, AttributeError):
        return None


def register():
    ops.register()
    pies.register()
    workspace.register()
    for cls in _classes:
        bpy.utils.register_class(cls)
    prefs = _prefs()
    if prefs is None or prefs.use_keys:
        keymap.register()


def unregister():
    keymap.unregister()
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    workspace.unregister()
    pies.unregister()
    ops.unregister()
