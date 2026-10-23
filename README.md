# Softimage Workflow Kit for Blender

Work in Blender the way you worked in Softimage: its layout and panels, its keys and navigation, its menus and its pie menus, on top of Blender's own tools.

> **Status: 0.1.0, personal use.** The Softimage workspace is in and working: menu bar, module toolbar, four viewports with Softimage's header strips, the MCP, the timeline and the bottom bar. Many buttons call the closest Blender operation; Softimage features Blender has no equivalent for are greyed out.

## The Softimage workspace

Preferences > Add-ons > Softimage Workflow Kit > **Create Softimage Workspace** builds a "Softimage" workspace laid out like Softimage's default layout (`Application/layouts/default.xsily`):

- **Menu bar:** File, Edit, View, Display, Window, Help, then Model, Animate, Render, ICE and Simulate; the construction-mode and pass choosers; Scene Search (type a name, Enter selects).
- **Toolbar panel (left):** the module chooser (Model / Animate / Render / Simulate) and the groups of buttons (Get, Create, Deform, Actions, Tools ...). Each button opens a flyout of Blender operations.
- **Four viewports:** Top, User, Front, Right in a 2 x 2 grid, with Softimage's header strip over each (viewport letter, view-type dropdown, display-type dropdown, maximize) and the mid-grey background.
- **MCP (right):** Select (tool, Group, Center, Object / Point / Edge / Polygon, the name box), Transform (scale, rotation and translation boxes you can type into, the S / R / T tools, locks, Global / Local / View and the other reference frames, COG / Prop / Sym), Snap, Constrain and Edit.
- **Timeline:** the current-frame box, the ruler (click or drag to scrub), the range boxes.
- **Bottom bar:** the command line (type a Python statement, Enter runs it; `bpy`, `scene`, `D`, `C` and `selection` are available), the playback buttons, Auto key, the key button, Key All Keyable and the status line.

The panels are drawn by the kit itself (Blender's own widgets cannot look like Softimage's) into dedicated areas, with the mouse routed to them by the kit. Colours, sizes and positions were measured from Softimage 2015 SP2 at 100 % scale. Softimage's own icons and bitmaps are not used or included.

## Keys and navigation

**Navigation.** Hold **S** and drag: left = orbit, middle = pan, right = dolly. S alone does nothing.

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

**Pie menus** (hold the key, flick toward a choice, release; or tap and click): **Z** display, **\`** view, **Tab** mode, **.** transform, **D** modeling (it follows the selection: objects, polygons, edges, vertices, or the geometry tools when nothing is selected).

**One switch back.** Untick "Softimage keys and pie menus" in the add-on preferences, or disable the add-on, and Blender's own keys are back. The kit only adds to Blender's add-on key configuration; it never edits your keymap, theme or preferences on its own (the navigation preferences are a button).

## What it will not be

Blender is not Softimage. It has no construction-history operator stack, no clusters and no Softimage object model, so "Construction Mode", "CnsComp", "ChldComp" and "Immed" are shown greyed out, and Explore / Scene / Selection / Clusters open menus of the closest Blender equivalents. Menus open as Blender menus, not Softimage's own popup style.

## Try it without installing

`powershell -File launch_softimage.ps1` starts Blender (5.1 by default; `-Blender <path>` picks another, `-Factory` uses factory settings) with the kit loaded from this folder and the Softimage workspace built a couple of seconds later (its tab is called **Softimage**). Nothing is installed or saved to your preferences.

## Install (development)

1. Copy or link the `softimage_workflow_kit` folder into Blender's add-ons folder, or build a zip with `blender --command extension build --source-dir softimage_workflow_kit`.
2. Enable **Softimage Workflow Kit** under Edit > Preferences > Add-ons, then click *Create Softimage Workspace*.

Tested on Blender 5.0 and 5.1. The manifest asks for 4.5 LTS or newer; 4.5 itself is not tested yet. Fonts: Tahoma (from Windows) when present.

## Tests

All three run a real Blender and need no extra tools:

- `blender --factory-startup --python tests/blender_smoke.py`: registers the kit, checks the keymap, the operators, the workspace and the panels, activates the panels' buttons and typed values, runs a command-line statement, draws every menu, unregisters and checks nothing is left behind. Writes `tests/last_result.txt`.
- `powershell -File tests\live_nav.ps1` (Windows): sends real key and mouse events to check S + left / middle / right drag navigation.
- `powershell -File tests\live_panels.ps1` (Windows): builds the workspace and clicks panel buttons and the timeline ruler with the real mouse.

## Licence and credits

GPL-3.0-or-later (see `LICENSE`), as every Blender add-on must be.

This project is not affiliated with, endorsed by or sponsored by Autodesk. "Softimage" is a trademark of Autodesk, Inc., used here only to say which workflow this kit follows. The kit contains no Autodesk code, icons or other assets.
