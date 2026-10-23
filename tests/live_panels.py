# SPDX-License-Identifier: GPL-3.0-or-later
"""Live test of the custom-drawn panels, started by tests/live_panels.ps1: builds the Softimage workspace, tells the PowerShell side where some buttons are on the screen,
waits while it clicks them with the real mouse, and then checks what the clicks did.
Blender: blender --factory-startup --python tests/live_panels.py
"""

import json
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "tests", "live_panels_result.txt")
POINTS = os.path.join(ROOT, "tests", "live_panels_points.json")
MARKER = os.path.join(ROOT, "tests", "live_panels_marker.txt")
state = {"waited": 0.0, "before": {}}


def finish(lines):
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\nDONE\n")
    sys.stdout.flush()
    os._exit(0)


def target_points(kit):
    cv = kit.canvas
    win = bpy.context.window
    pts = {}
    for area in win.screen.areas:
        c = cv.canvas_of(area)
        if c is None:
            continue
        c.layout(area.width, area.height)
        top = win.height - (area.y + area.height)   # the area's top edge, measured from the top of the window
        for w in c.widgets:
            key = "%s:%s" % (c.name, w.get("label") or w.get("key") or w["kind"])
            pts[key] = (area.x + w["x"] + w["w"] / 2.0, top + w["y"] + w["h"] / 2.0)   # relative to the window's client area (the caller adds where that is on the screen)
    return pts


def start():
    import softimage_workflow_kit as kit
    kit.register()
    bpy.ops.mesh.primitive_cube_add()
    state["kit"] = kit
    bpy.ops.siwk.create_workspace()
    bpy.app.timers.register(wait_built, first_interval=0.5)
    return None


def wait_built():
    state["waited"] += 0.5
    kit = state["kit"]
    if not kit.workspace.build_done and state["waited"] < 25:
        return 0.5
    # a couple of redraws so the areas have their final sizes
    bpy.app.timers.register(publish, first_interval=1.5)
    return None


def publish():
    kit = state["kit"]
    pts = target_points(kit)
    sc = bpy.context.scene
    state["before"] = {"orient": sc.transform_orientation_slots[0].type, "frame": sc.frame_current, "auto": sc.tool_settings.use_keyframe_insert_auto,
                       "prop": sc.tool_settings.use_proportional_edit_objects}
    # the screen position the ruler's middle and the buttons are at, as the PowerShell side will click them
    with open(POINTS, "w", encoding="utf-8") as f:
        json.dump({k: pts[k] for k in ("MCP:Local", "Timeline:ruler", "Command line / playback:Auto", "MCP:Prop", "Toolbar Panel:Animate", "Menu Bar:Display", "Menu Bar:Model", "Toolbar Panel:Primitive", "MCP:Explore") if k in pts}, f)
    bpy.app.timers.register(poll, first_interval=0.3)
    return None


def poll():
    try:
        with open(MARKER, "r", encoding="utf-8") as f:
            marker = f.read().strip()
    except OSError:
        return 0.3
    if marker != "done":
        return 0.3
    sc = bpy.context.scene
    b = state["before"]
    lines = []
    ok = True

    def check(cond, what):
        nonlocal ok
        ok = ok and cond
        lines.append(("PASS " if cond else "FAIL ") + what)
    check(sc.transform_orientation_slots[0].type == 'LOCAL', "a click on the MCP's Local button sets the Local orientation (now %s)" % sc.transform_orientation_slots[0].type)
    check(sc.tool_settings.use_keyframe_insert_auto != b["auto"], "a click on Auto toggles auto-key")
    check(sc.tool_settings.use_proportional_edit_objects != b["prop"], "a click on Prop toggles soft selection")
    check(sc.frame_current != b["frame"] and abs(sc.frame_current - (sc.frame_start + sc.frame_end) / 2.0) < 30, "a click on the middle of the timeline ruler moves the frame there (%d)" % sc.frame_current)
    lines.append("LIVE RESULT: " + ("OK" if ok else "FAIL"))
    finish(lines)
    return None


bpy.app.timers.register(start, first_interval=2.0)
