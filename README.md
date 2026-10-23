# Softimage Workflow Kit for Blender

Work in Blender the way you worked in Softimage: its keys and navigation, its four-view layout and panels, its menus and its ways of working, on top of Blender's own tools.

> **Status: just started.** This repository is the scaffold. Nothing is switched on yet.

## What it is meant to do

- **Keys and navigation:** Softimage's keymap, including S-hold orbit / pan / dolly, the Q / W / E / R tools and the component modes.
- **Layout:** a Softimage workspace: Top / Front / Right / User views, the left and right panel groups, command line and timeline.
- **Menus and pies:** Softimage's menu sets and pie menus, calling Blender's own operators.
- **Concepts:** groups and layers, an Explorer-style outliner, a property page, constraint compensation, Freeze mapped to applying modifiers.
- **One switch back:** turn the kit off and Blender is plain Blender again. Nothing is written to your preferences, theme or keymap.

## What it will not be

Blender is not Softimage. It has no construction-history operator stack, no clusters and no Softimage object model, and a Python add-on cannot redraw the interface from scratch. The kit gets Blender close to Softimage's feel, not identical to it. Where Softimage has something Blender cannot do, the menu entry is greyed out with an explanation.

## Install (development)

1. Copy or link the `softimage_workflow_kit` folder into Blender's add-ons folder, or build a zip with `blender --command extension build --source-dir softimage_workflow_kit`.
2. Enable **Softimage Workflow Kit** under Edit > Preferences > Add-ons.

Requires Blender 4.5 LTS or newer.

## Licence and credits

GPL-3.0-or-later (see `LICENSE`), as every Blender add-on must be.

This project is not affiliated with, endorsed by or sponsored by Autodesk. "Softimage" is a trademark of Autodesk, Inc., used here only to say which workflow this kit follows. The kit contains no Autodesk code, icons or other assets.
