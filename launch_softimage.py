# SPDX-License-Identifier: GPL-3.0-or-later
"""Start-up script for launch_softimage.ps1: loads the kit from this folder (nothing is installed) and builds the Softimage workspace.
Run by hand with:  blender --python launch_softimage.py
"""

import os
import sys

import bpy

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def go():
    import softimage_workflow_kit as kit
    kit.register()
    bpy.ops.siwk.create_workspace()
    return None


bpy.app.timers.register(go, first_interval=1.0)
