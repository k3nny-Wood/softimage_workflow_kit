# SPDX-License-Identifier: GPL-3.0-or-later
"""Softimage Workflow Kit: Softimage's keys, layout, menus and ways of working on top of Blender's own tools.

Nothing here writes to the user's preferences, theme or active keymap: everything the kit registers is removed again when it is switched off.
"""

import bpy

bl_info = {
    "name": "Softimage Workflow Kit",
    "author": "k3nny-Wood",
    "version": (0, 0, 1),
    "blender": (4, 5, 0),
    "description": "Softimage's workflow on top of Blender",
    "category": "Interface",
}


class SIWK_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        layout.label(text="Softimage Workflow Kit 0.0.1: the scaffold. Nothing is switched on yet.")


_classes = (SIWK_AddonPreferences,)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
