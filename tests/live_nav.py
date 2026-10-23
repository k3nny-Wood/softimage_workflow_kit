# SPDX-License-Identifier: GPL-3.0-or-later
"""Live navigation test, started by tests/live_nav.ps1 (which sends real key and mouse events to the Blender window):
S + left drag must orbit the 3D view, S + middle drag pan it, S + right drag dolly it, and S alone must not start Blender's own scale.
Blender: blender --factory-startup --python tests/live_nav.py
The PowerShell side writes a phase number to tests/live_marker.txt after each drag; this side takes a snapshot of the view whenever the number changes.
"""

import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "tests", "live_result.txt")
MARKER = os.path.join(ROOT, "tests", "live_marker.txt")
snaps = {}
state = {"last": None}


def view():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            return area.spaces.active.region_3d
    return None


def snapshot():
    rv = view()
    eye = rv.view_location + rv.view_rotation @ Vector((0.0, 0.0, rv.view_distance))
    return {"rot": tuple(rv.view_rotation), "loc": tuple(rv.view_location), "dist": rv.view_distance, "eye": tuple(eye), "scale": tuple(bpy.context.active_object.scale)}


def diff(a, b, key):
    return max(abs(x - y) for x, y in zip(a[key], b[key]))


def start():
    import softimage_workflow_kit as kit
    kit.register()
    bpy.ops.mesh.primitive_cube_add()
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            win = bpy.context.window
            with open(os.path.join(ROOT, "tests", "live_area.txt"), "w", encoding="utf-8") as f:
                f.write("%d %d %d %d %d %d %d %d\n" % (win.x, win.y, area.x, area.y, area.width, area.height, win.width, win.height))
    bpy.app.timers.register(poll, first_interval=0.25)
    return None


def poll():
    try:
        with open(MARKER, "r", encoding="utf-8") as f:
            marker = f.read().strip()
    except OSError:
        return 0.25
    if marker and marker != state["last"]:
        state["last"] = marker
        snaps[marker] = snapshot()
        if marker == "5":
            finish()
            return None
    return 0.25


def finish():
    lines = []
    s = snaps
    if all(k in s for k in ("1", "2", "3", "4")):
        lines.append("S + left drag:   rotation change %.4f" % diff(s["1"], s["2"], "rot"))
        lines.append("S + middle drag: location change %.4f (rotation %.4f)" % (diff(s["2"], s["3"], "loc"), diff(s["2"], s["3"], "rot")))
        lines.append("S + right drag:  eye position change %.4f (rotation %.4f)" % (diff(s["3"], s["4"], "eye"), diff(s["3"], s["4"], "rot")))
        lines.append("object scale change over the whole run %.4f" % diff(s["1"], s["4"], "scale"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\nDONE\n")
    bpy.ops.wm.quit_blender()


bpy.app.timers.register(start, first_interval=2.0)
