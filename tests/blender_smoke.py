# SPDX-License-Identifier: GPL-3.0-or-later
"""Smoke test, run inside Blender (not background): blender --factory-startup --python tests/blender_smoke.py

It registers the add-on from this checkout, checks the keymap, calls the operators, builds the workspace, unregisters and checks that nothing is left behind.
The result is printed as `SIWK RESULT: OK` or `SIWK RESULT: FAIL ...` and written to tests/last_result.txt.
"""

import os
import sys
import traceback

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
failures = []


def check(cond, what):
    if not cond:
        failures.append(what)
        print("SIWK FAIL:", what)


def items_of(kc, km_name):
    km = kc.keymaps.get(km_name)
    return list(km.keymap_items) if km else []


def view3d_override():
    win = bpy.context.window
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            return bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region)
    return None


state = {}


def finish():
    result = "SIWK RESULT: OK" if not failures else "SIWK RESULT: FAIL " + "; ".join(failures)
    print(result)
    with open(os.path.join(ROOT, "tests", "last_result.txt"), "w", encoding="utf-8") as f:
        f.write(result + "\n")
    sys.stdout.flush()
    os._exit(0 if not failures else 1)   # (Blender 5.1 can crash in its own shutdown code when a tooltip is open; the result is already written)


def after_workspace():
    state["waited"] += 0.3
    screen = bpy.context.window.screen
    views = [a for a in screen.areas if a.type == 'VIEW_3D' and a.width > 0]
    if not state["kit"].workspace.build_done:
        if state["waited"] < 20.0:
            return 0.3
    try:
        kit, kc, n_items = state["kit"], state["kc"], state["n_items"]
        check(bpy.data.workspaces.get("Softimage") is not None, "the Softimage workspace exists")
        check(bpy.context.window.workspace.name == "Softimage", "the Softimage workspace is the one on screen (%s)" % bpy.context.window.workspace.name)
        check(bpy.data.workspaces.get("Layout") is not None and bpy.data.workspaces.get("Layout.001") is None, "the original Layout workspace is untouched and no stray copy is left: %s" % [w.name for w in bpy.data.workspaces])
        check(len(views) == 4, "the workspace has four 3D views (%d): %s" % (len(views), [(x.type, x.x, x.y, x.width, x.height) for x in screen.areas]))
        if len(views) == 4:
            views.sort(key=lambda a: (-a.y, a.x))
            kinds = [(a.spaces.active.shading.type, a.spaces.active.region_3d.view_perspective) for a in views]
            check(sum(1 for k in kinds if k[0] == 'WIREFRAME') == 3 and sum(1 for k in kinds if k[0] == 'SOLID') == 1, "three wireframe views and one shaded: %s" % (kinds,))
            check(sum(1 for k in kinds if k[1] == 'ORTHO') == 3, "three orthographic views: %s" % (kinds,))
            if os.environ.get("SIWK_SHOT"):
                bpy.ops.screen.screenshot(filepath=os.path.join(ROOT, "tests", "workspace.png"))
        # ---- switching the kit off leaves nothing behind
        if os.environ.get("SIWK_NO_UNREG"):
            finish()
            return None
        kit.unregister()
        after_items = sorted((km.name, i.idname, i.type) for km in kc.keymaps for i in km.keymap_items)
        left = len(after_items) - len(state["before_items"]) if after_items != state["before_items"] else 0
        check(after_items == state["before_items"], "unregistering leaves the add-on key configuration as it was (%d items, %d before)" % (len(after_items), len(state["before_items"])))
        check(not hasattr(bpy.types, "SIWK_MT_pie_display"), "the pies are unregistered")
    except Exception:
        failures.append("exception: " + traceback.format_exc())
        print(traceback.format_exc())
    finish()
    return None


def run():
    try:
        import softimage_workflow_kit as kit
        kc = bpy.context.window_manager.keyconfigs.addon
        state["before_items"] = sorted((km.name, i.idname, i.type) for km in kc.keymaps for i in km.keymap_items)   # (Blender's own add-ons may already have items there)
        kit.register()

        # ---- keymap
        view = items_of(kc, "3D View")
        mods = {(i.idname, i.type, i.key_modifier) for i in view}
        check(("view3d.rotate", 'LEFTMOUSE', 'S') in mods, "S + left drag orbits")
        check(("view3d.move", 'MIDDLEMOUSE', 'S') in mods, "S + middle drag pans")
        check(("view3d.dolly", 'RIGHTMOUSE', 'S') in mods, "S + right drag dollies")
        for name in ("Object Mode", "Mesh", "Pose"):
            ids = {(i.idname, i.type) for i in items_of(kc, name)}
            check(("siwk.nav_hold", 'S') in ids, "S is swallowed in " + name)
            check(("wm.tool_set_by_id", 'W') in ids and ("wm.tool_set_by_id", 'E') in ids, "W / E choose tools in " + name)
            check(("wm.call_menu_pie", 'Z') in ids and ("wm.call_menu_pie", 'D') in ids, "the pies are on Z and D in " + name)
        n_items = sum(len(items_of(kc, n)) for n in ("3D View", "Object Mode", "Mesh"))

        # ---- operators
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        check(bpy.ops.siwk.component_mode(mode='FACE') == {'FINISHED'} and obj.mode == 'EDIT' and tuple(bpy.context.tool_settings.mesh_select_mode) == (False, False, True), "3 = polygon mode")
        bpy.ops.siwk.component_mode(mode='EDGE')
        check(tuple(bpy.context.tool_settings.mesh_select_mode) == (False, True, False), "2 = edge mode")
        bpy.ops.siwk.component_mode(mode='OBJECT')
        check(obj.mode == 'OBJECT', "7 = object mode")
        before = len(bpy.data.objects)
        bpy.ops.siwk.duplicate  # (invoke-only: just check it exists)
        check(hasattr(bpy.ops.siwk, "duplicate"), "duplicate exists")
        bpy.ops.siwk.select_all(action='DESELECT')
        check(not obj.select_get(), "unselect all")
        bpy.ops.siwk.select_all(action='SELECT')
        check(obj.select_get(), "select all")
        ts = bpy.context.tool_settings
        was = ts.use_proportional_edit_objects
        bpy.ops.siwk.proportional()
        check(ts.use_proportional_edit_objects != was, "B toggles soft selection")
        bpy.ops.siwk.proportional()

        ctx = view3d_override()
        if ctx is not None:
            with ctx:
                space = bpy.context.space_data
                for kind, shading in (('WIREFRAME', 'WIREFRAME'), ('SHADED', 'SOLID'), ('REALTIME', 'MATERIAL'), ('RENDERED', 'RENDERED')):
                    bpy.ops.siwk.shading(type=kind)
                    check(space.shading.type == shading, "display type " + kind)
                bpy.ops.siwk.shading(type='SHADED')
                bpy.ops.siwk.view_type(type='TOP')
                check(abs(space.region_3d.view_rotation.to_euler().x) < 1e-3, "Top view")
                bpy.ops.siwk.view_type(type='ISO')
                check(space.region_3d.view_perspective == 'ORTHO', "isometric is orthographic")
                bpy.ops.siwk.view_type(type='USER')
                check(space.region_3d.view_perspective == 'PERSP', "user view is perspective")
                on = space.overlay.show_floor
                bpy.ops.siwk.toggle_grid()
                check(space.overlay.show_floor != on, "G toggles the grid")
                bpy.ops.siwk.toggle_grid()
        else:
            check(False, "there is no 3D view to test in")

        # ---- the pies draw (they are only classes here: check they are registered)
        for name in ("SIWK_MT_pie_display", "SIWK_MT_pie_view", "SIWK_MT_pie_mode", "SIWK_MT_pie_transform", "SIWK_MT_pie_modeling"):
            check(hasattr(bpy.types, name), name + " is registered")

        # ---- the workspace is built over a few timer ticks: wait for it, then check it
        bpy.ops.siwk.create_workspace()
        state["kit"], state["kc"], state["n_items"], state["waited"] = kit, kc, n_items, 0.0
        bpy.app.timers.register(after_workspace, first_interval=0.3)
        return None
    except Exception:
        failures.append("exception: " + traceback.format_exc())
        print(traceback.format_exc())
        finish()
    return None


bpy.app.timers.register(run, first_interval=2.5)
