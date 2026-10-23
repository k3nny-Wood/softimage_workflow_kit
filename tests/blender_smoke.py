# SPDX-License-Identifier: GPL-3.0-or-later
"""Smoke test, run inside Blender (not background): blender --factory-startup --python tests/blender_smoke.py

It registers the add-on from this checkout, checks the keymap, calls the operators, builds the workspace, unregisters and checks that nothing is left behind.
The result is printed as `SIWK RESULT: OK` or `SIWK RESULT: FAIL ...` and written to tests/last_result.txt.
"""

import math
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
        canvases = state["kit"].canvas._registry
        names = sorted(c.name for c in canvases.values())
        check(len(canvases) == 5 and names == sorted(["Toolbar Panel", "MCP", "Timeline", "Command line / playback", "Menu Bar"]), "the five custom panels are registered: %s" % names)
        host = [a for a in bpy.context.window.screen.areas if a.type == 'SPREADSHEET']
        check(len(host) == 5, "the panels sit in five canvas areas (%d)" % len(host))
        left = next((a for a in host if state["kit"].canvas.canvas_of(a).name == "Toolbar Panel"), None)
        check(left is not None and 80 <= left.width <= 130, "the toolbar panel is about 106 px wide (%s)" % (left.width if left else None))
        mcp = next((a for a in host if state["kit"].canvas.canvas_of(a).name == "MCP"), None)
        check(mcp is not None and 110 <= mcp.width <= 160, "the MCP is about 136 px wide (%s)" % (mcp.width if mcp else None))
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
        views_reg = state["kit"].panel_view._views
        check(sorted(views_reg.values()) == ["A", "B", "C", "D"], "the four viewports have Softimage's header strips (letters %s)" % sorted(views_reg.values()))
        for area in bpy.context.window.screen.areas:
            if area.as_pointer() in views_reg:
                sp = area.spaces.active
                check(not sp.show_region_header and sp.shading.background_type == 'VIEWPORT', "viewport %s has Blender's header hidden and the grey background" % views_reg[area.as_pointer()])
                lbl = state["kit"].panel_view.view_label(sp)
                check(lbl in ("Top", "Front", "Right", "User"), "viewport %s is labelled %s" % (views_reg[area.as_pointer()], lbl))
        # ---- the panels do things: activate their buttons the way a click would
        kit = state["kit"]
        cv = kit.canvas
        by_name = {c.name: (a, c) for a in host for c in [cv.canvas_of(a)]}
        sc = bpy.context.scene

        def widget(panel, label=None, key=None, kind=None):
            area, c = by_name[panel]
            c.layout(area.width, area.height)
            for w in c.widgets:
                if (label is None or w.get("label") == label) and (key is None or w.get("key") == key) and (kind is None or w["kind"] == kind):
                    return c, w
            return c, None

        c, w = widget("MCP", "Local")
        check(w is not None, "the MCP has a Local button")
        if w is not None:
            c.activate(w, bpy.context)
            check(sc.transform_orientation_slots[0].type == 'LOCAL', "the MCP's Local button sets the transform orientation")
        c, w = widget("MCP", "Global")
        c.activate(w, bpy.context)
        check(sc.transform_orientation_slots[0].type == 'GLOBAL', "Global sets it back")
        c, w = widget("MCP", "ON")
        was = sc.tool_settings.use_snap
        c.activate(w, bpy.context)
        check(sc.tool_settings.use_snap != was, "the Snap ON button toggles snapping")
        c.activate(widget("MCP", "ON")[1], bpy.context)
        ob = bpy.context.active_object
        if ob is not None:
            ob.location = (0, 0, 0)
            c, w = widget("MCP", key="T0")
            c.begin_edit = lambda widget_, text, commit: commit("2.5")   # (typing needs the real mouse and keyboard)
            c.activate(w, bpy.context)
            check(abs(ob.location.x - 2.5) < 1e-6, "typing 2.5 into the translation X box moves the object (%s)" % ob.location.x)
            c, w = widget("MCP", key="R2")
            c.begin_edit = lambda widget_, text, commit: commit("90")
            c.activate(w, bpy.context)
            check(abs(math.degrees(ob.rotation_euler.z) - 90.0) < 1e-4, "typing 90 into the rotation Z box rotates the object")
            c, w = widget("MCP", key="name")
            c.begin_edit = lambda widget_, text, commit: commit("Softimage_Cube")
            c.activate(w, bpy.context)
            check(ob.name == "Softimage_Cube", "the name box renames the object")
            ob.rotation_euler = (0, 0, 0)
            c, w = widget("MCP", "Object")
            check(w is not None and w.get("on") is True, "the Object button shows object mode")
            c, w = widget("MCP", "Group")
            n_coll = len(bpy.data.collections)
            c.activate(w, bpy.context)
            check(len(bpy.data.collections) == n_coll + 1, "Group puts the selection in a new collection")
        # timeline
        c, w = widget("Timeline", kind="ruler")
        c._scrub(bpy.context, w, w["x"] + w["w"] * 0.5, 5)
        mid = sc.frame_start + (sc.frame_end - sc.frame_start) * 0.5
        check(abs(sc.frame_current - mid) <= 1, "dragging on the ruler scrubs to the middle of the range (%d)" % sc.frame_current)
        c, w = widget("Timeline", key="end")
        c.begin_edit = lambda widget_, text, commit: commit("120")
        c.activate(w, bpy.context)
        check(sc.frame_end == 120, "the end-frame box sets the range")
        sc.frame_end = 250
        sc.frame_set(1)
        # bottom bar
        c, w = widget("Command line / playback", "Auto")
        was = sc.tool_settings.use_keyframe_insert_auto
        c.activate(w, bpy.context)
        check(sc.tool_settings.use_keyframe_insert_auto != was, "Auto toggles auto-key")
        c.activate(widget("Command line / playback", "Auto")[1], bpy.context)
        c, w = widget("Command line / playback", key="cmd")
        c.begin_edit = lambda widget_, text, commit: commit("scene.frame_end = 77")
        c.activate(w, bpy.context)
        check(sc.frame_end == 77, "a Python statement typed on the command line runs")
        sc.frame_end = 250
        # left panel: modules and flyouts
        bpy.ops.siwk.set_module(module="Model")
        lp = by_name["Toolbar Panel"][1]
        check(lp.module == "Model", "the module chooser switches the toolbar panel to Model")
        lp.layout(by_name["Toolbar Panel"][0].width, 800)
        labels = [x["label"] for x in lp.widgets]
        check("Poly. Mesh" in labels and "Constr. Mode" in labels, "the Model module has its own groups")
        w = next(x for x in lp.widgets if x["label"] == "Primitive")
        check(w["action"] == "SIWK_MT_fly_Primitive" and hasattr(bpy.types, "SIWK_MT_fly_Primitive"), "a toolbar button opens its flyout menu")
        bpy.ops.siwk.set_module(module="Animate")
        # every menu draws
        class _Op:
            pass

        class _Layout:
            def __init__(self):
                self.calls = []
            def operator(self, idname, text=""):
                self.calls.append(("op", idname)); return _Op()
            def menu(self, idname, text=""):
                self.calls.append(("menu", idname))
            def separator(self):
                self.calls.append(("sep",))
            def label(self, text=""):
                self.calls.append(("label", text))
        counts = {}
        for cls in kit.menus._generated:
            lay = _Layout()
            try:
                items = cls.__dict__.get("_items") or []
                kit.menus._draw_items(lay, items() if callable(items) else items)
            except Exception as exc:
                check(False, "menu %s fails to draw: %s" % (cls.__name__, exc))
        check(len(kit.menus._generated) > 40, "the menus are generated (%d)" % len(kit.menus._generated))
        check(all(hasattr(bpy.types, cls.__name__) for cls in kit.menus._generated), "every generated menu is registered")
        for label, mid in kit.menus.TOP_MENUS.items():
            check(hasattr(bpy.types, mid), "menu bar entry %s has a menu" % label)

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
