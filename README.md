# Softimage Workflow Kit for Blender

Work in Blender the way you worked in Softimage: its keys and navigation, its four-view layout and its pie menus, on top of Blender's own tools.

> **Status: early (0.0.2).** The first milestone is in: keys, hold-S navigation, the Softimage workspace and five pie menus. Menus, panels and the Softimage concepts (groups, Explorer, property page, constraint compensation) come next.

## What it does now

**Navigation.** Hold **S** and drag: left = orbit, middle = pan, right = dolly. S alone does nothing (Blender's own S, scale, is swallowed).

**Keys** (Object mode and the edit modes):

| Key | Does |
|---|---|
| Q / W / E / R | select, move, rotate, scale tools |
| 1 / 2 / 3 / 7 | vertex, edge, polygon, object |
| 4 / 5 / 6 | wireframe, wire on shaded, shaded |
| Space | maximize the view under the cursor |
| F | frame selection |
| T / V / I | top, user, isometric |
| G | show / hide the grid |
| B | soft selection (proportional editing) on / off |
| Ctrl+A / Ctrl+I | select all / invert |
| Ctrl+D | duplicate |
| Delete | delete the objects or the points / edges / polygons |
| Shift+B | bevel (edit mode) |

**Pie menus** (hold the key, flick toward a choice, release; or tap and click):

| Key | Pie |
|---|---|
| Z | Display: wireframe, shaded, textured, realtime, constant, rendered, wire on shaded, grid |
| \` | View: front, right, user, top, frame all, frame selection, maximize, isometric |
| Tab | Mode: vertex, edge, polygon, object and the select / move / rotate / scale tools |
| . | Transform: view, local, parent, global, soft selection, normal, invert selection, unselect all |
| D | Modeling: follows the context. Objects: duplicate, merge, delete, freeze ... Polygons: bevel, extrude, inset, bridge ... Edges and vertices have their own sets. With nothing selected in edit mode: the geometry tools (knife, loop cut, poly build ...) |

**Workspace.** Preferences > Add-ons > Softimage Workflow Kit > *Create Softimage Workspace* adds a "Softimage" workspace with Top, User, Front and Right views in a 2 x 2 layout: wireframe in the orthographic views, shaded in the User view. *Apply Softimage Navigation Preferences* sets turntable orbit and horizontal dolly (it changes your own preferences, so it is a button and not automatic).

**One switch back.** Untick "Softimage keys and pie menus" in the add-on preferences, or disable the add-on, and Blender's own keys are back. The kit only adds items to Blender's add-on key configuration; it never edits your keymap, theme or preferences on its own.

## What it will not be

Blender is not Softimage. It has no construction-history operator stack, no clusters and no Softimage object model, and a Python add-on cannot redraw the interface from scratch. The kit gets Blender close to Softimage's feel, not identical to it. Where Softimage has something Blender cannot do, the entry will be greyed out with an explanation.

## Install (development)

1. Copy or link the `softimage_workflow_kit` folder into Blender's add-ons folder, or build a zip with `blender --command extension build --source-dir softimage_workflow_kit`.
2. Enable **Softimage Workflow Kit** under Edit > Preferences > Add-ons.

Tested on Blender 5.0 and 5.1. The manifest asks for 4.5 LTS or newer; 4.5 itself is not tested yet.

## Tests

Both run a real Blender and need no extra tools:

- `blender --factory-startup --python tests/blender_smoke.py`: registers the kit, checks the keymap, calls the operators, builds the workspace, unregisters and checks nothing is left behind. Writes `tests/last_result.txt`.
- `powershell -File tests\live_nav.ps1` (Windows): starts Blender and sends real key and mouse events to check S + left / middle / right drag navigation. Writes `tests/live_result.txt`.

## Licence and credits

GPL-3.0-or-later (see `LICENSE`), as every Blender add-on must be.

This project is not affiliated with, endorsed by or sponsored by Autodesk. "Softimage" is a trademark of Autodesk, Inc., used here only to say which workflow this kit follows. The kit contains no Autodesk code, icons or other assets.
