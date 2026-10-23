# SPDX-License-Identifier: GPL-3.0-or-later
"""The Softimage keymap, added to Blender's add-on key configuration (never to the user's own), so switching the kit off removes every item again.

Keys follow ISX's confirmed conventions: S is a hold (S + left / middle / right drag = orbit / pan / dolly), Q / W / E / R select / move / rotate / scale,
1 / 2 / 3 / 7 = vertex / edge / polygon / object, 4 / 5 / 6 = wireframe / wire on shaded / shaded, Space maximizes the view, F frames the selection, B is soft selection.
"""

import bpy

_items = []   # (keymap, item) pairs added by the kit
_keymaps = []   # keymaps the kit created (removed again on unregister when they are empty)

# keymaps of the modes: their default items (E = extrude, S = scale, 1..9 = hide collections ...) beat "3D View", so the kit adds its keys in each of them
_MODE_KEYMAPS = ("Object Mode", "Mesh", "Curve", "Armature", "Pose", "Lattice", "Metaball")


def _add(km, idname, key, value='PRESS', *, shift=False, ctrl=False, alt=False, key_modifier='NONE', **props):
    kmi = km.keymap_items.new(idname, key, value, shift=shift, ctrl=ctrl, alt=alt, key_modifier=key_modifier)
    for name, val in props.items():
        setattr(kmi.properties, name, val)
    _items.append((km, kmi))
    return kmi


def _keymap(kc, name, space_type='EMPTY', region_type='WINDOW'):
    km = kc.keymaps.new(name=name, space_type=space_type, region_type=region_type)
    _keymaps.append(km)
    return km


def _nav(km):
    """S + drag: the navigation, in every keymap whose own left / right press (select, context menu) would otherwise win"""
    _add(km, "view3d.rotate", 'LEFTMOUSE', key_modifier='S')
    _add(km, "view3d.move", 'MIDDLEMOUSE', key_modifier='S')
    _add(km, "view3d.dolly", 'RIGHTMOUSE', key_modifier='S')


def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is None:   # background mode: no keymaps to edit
        return

    # ---- 3D view: navigation, views and display (the S hold is a no-op key so Blender's own S, scale, does not fire)
    km = _keymap(kc, "3D View", 'VIEW_3D')
    _nav(km)
    _add(km, "view3d.view_selected", 'F')
    _add(km, "siwk.view_type", 'T', type='TOP')
    _add(km, "siwk.view_type", 'V', type='USER')
    _add(km, "siwk.view_type", 'I', type='ISO')
    _add(km, "siwk.toggle_grid", 'G')
    _add(km, "screen.screen_full_area", 'SPACE')

    # ---- keys that must beat the modes' own
    for name in _MODE_KEYMAPS:
        km = _keymap(kc, name)
        _add(km, "siwk.nav_hold", 'S')
        _nav(km)
        _add(km, "wm.tool_set_by_id", 'Q', name="builtin.select_box")
        _add(km, "wm.tool_set_by_id", 'W', name="builtin.move")
        _add(km, "wm.tool_set_by_id", 'E', name="builtin.rotate")
        _add(km, "wm.tool_set_by_id", 'R', name="builtin.scale")
        _add(km, "siwk.shading", 'FOUR', type='WIREFRAME')
        _add(km, "siwk.shading", 'FIVE', type='WIRE_ON_SHADED')
        _add(km, "siwk.shading", 'SIX', type='SHADED')
        _add(km, "siwk.component_mode", 'ONE', mode='VERT')
        _add(km, "siwk.component_mode", 'TWO', mode='EDGE')
        _add(km, "siwk.component_mode", 'THREE', mode='FACE')
        _add(km, "siwk.component_mode", 'SEVEN', mode='OBJECT')
        _add(km, "siwk.proportional", 'B')
        _add(km, "siwk.select_all", 'A', ctrl=True, action='SELECT')
        _add(km, "siwk.select_all", 'I', ctrl=True, action='INVERT')
        _add(km, "siwk.duplicate", 'D', ctrl=True)
        _add(km, "siwk.delete", 'DEL')
        _add(km, "siwk.toggle_grid", 'G')
        # the pie menus
        _add(km, "wm.call_menu_pie", 'Z', name="SIWK_MT_pie_display")
        _add(km, "wm.call_menu_pie", 'ACCENT_GRAVE', name="SIWK_MT_pie_view")
        _add(km, "wm.call_menu_pie", 'TAB', name="SIWK_MT_pie_mode")
        _add(km, "wm.call_menu_pie", 'PERIOD', name="SIWK_MT_pie_transform")
        _add(km, "wm.call_menu_pie", 'D', name="SIWK_MT_pie_modeling")
    km = _keymap(kc, "Mesh")
    _add(km, "mesh.bevel", 'B', shift=True)

    # the tools' own keymaps take the left press (select) before the modes' do: S + drag has to be in them as well
    for dkm in bpy.context.window_manager.keyconfigs.default.keymaps:
        if dkm.name.startswith("3D View Tool:"):
            _nav(_keymap(kc, dkm.name, dkm.space_type, dkm.region_type))


def unregister():
    for km, kmi in reversed(_items):
        try:
            km.keymap_items.remove(kmi)
        except (RuntimeError, ReferenceError):
            pass
    _items.clear()
    # (the keymaps themselves stay, empty: removing a keymap Blender is still dispatching events through can crash it)
    _keymaps.clear()
