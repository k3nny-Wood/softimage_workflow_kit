# SPDX-License-Identifier: GPL-3.0-or-later
"""The menus the custom panels open: Softimage's menu bar (File, Edit, View, Display, Window, Help and the Model / Animate / Render / ICE / Simulate menus) and the
flyouts of the toolbar panel's buttons. They are ordinary Blender menus, listing Softimage's commands and running Blender's own operators.

An item is (label, operator, {properties}); None is a separator; ("sub", label, menu id) opens another menu. An item whose operator this Blender does not have is left out.
"""

import bpy
from bpy.types import Menu

_generated = []


def _has(idname):
    mod, _dot, fn = idname.partition(".")
    return hasattr(getattr(bpy.ops, mod, None), fn)


def _draw_items(layout, items):
    last_sep = True
    for it in items:
        if it is None:
            if not last_sep:
                layout.separator()
                last_sep = True
            continue
        if it[0] == "sub":
            layout.menu(it[2], text=it[1])
            last_sep = False
            continue
        label, idname = it[0], it[1]
        props = it[2] if len(it) > 2 else {}
        if idname.startswith("!"):   # shown, never available (Softimage has it, Blender has nothing to run)
            layout.label(text=label)
            last_sep = False
            continue
        if not _has(idname):
            continue
        op = layout.operator(idname, text=label)
        for k, v in props.items():
            setattr(op, k, v)
        last_sep = False


def make_menu(idname, label, items):
    def draw(self, context):
        _draw_items(self.layout, items() if callable(items) else items)
    cls = type(idname, (Menu,), {"bl_idname": idname, "bl_label": label, "draw": draw, "_items": items})
    _generated.append(cls)
    return cls


def S(label, menu_id):
    return ("sub", label, menu_id)


# ---------------------------------------------------------------------------------------------------------------- the menu bar

def _workspaces():
    items = []
    for ws in bpy.data.workspaces:
        items.append((ws.name, "siwk.set_workspace", {"name": ws.name}))
    return items


FILE = [
    ("New Scene", "wm.read_homefile"), ("Open Scene...", "wm.open_mainfile"), S("Open Recent", "TOPBAR_MT_file_open_recent"), None,
    ("Save Scene", "wm.save_mainfile"), ("Save Scene As...", "wm.save_as_mainfile"), None,
    S("Import", "SIWK_MT_import"), S("Export", "SIWK_MT_export"), None,
    ("Quit", "wm.quit_blender"),
]
IMPORT = [("Wavefront OBJ...", "wm.obj_import"), ("FBX...", "wm.fbx_import"), ("FBX (add-on)...", "import_scene.fbx"), ("glTF 2.0...", "import_scene.gltf"),
          ("Alembic...", "wm.alembic_import"), ("USD...", "wm.usd_import"), ("STL...", "wm.stl_import"), ("PLY...", "wm.ply_import")]
EXPORT = [("Wavefront OBJ...", "wm.obj_export"), ("FBX...", "wm.fbx_export"), ("FBX (add-on)...", "export_scene.fbx"), ("glTF 2.0...", "export_scene.gltf"),
          ("Alembic...", "wm.alembic_export"), ("USD...", "wm.usd_export"), ("STL...", "wm.stl_export"), ("PLY...", "wm.ply_export")]
EDIT = [
    ("Undo", "ed.undo"), ("Redo", "ed.redo"), None,
    ("Select All", "siwk.select_all", {"action": 'SELECT'}), ("Invert Selection", "siwk.select_all", {"action": 'INVERT'}), ("Deselect All", "siwk.select_all", {"action": 'DESELECT'}), None,
    ("Duplicate", "siwk.duplicate"), ("Delete", "siwk.delete"), None,
    ("Preferences...", "screen.userpref_show"),
]
VIEW = [
    ("Frame All", "view3d.view_all"), ("Frame Selection", "view3d.view_selected"), None,
    S("View Type", "SIWK_MT_viewtype"), None,
    ("Toggle Maximize", "screen.screen_full_area"), ("Show / Hide Grid", "siwk.toggle_grid"), None,
    ("Softimage Workspace", "siwk.create_workspace"),
]
VIEWTYPE = [("Top", "siwk.view_type", {"type": 'TOP'}), ("Front", "siwk.view_type", {"type": 'FRONT'}), ("Right", "siwk.view_type", {"type": 'RIGHT'}),
            ("User", "siwk.view_type", {"type": 'USER'}), ("Isometric", "siwk.view_type", {"type": 'ISO'})]
DISPLAY = [
    ("Wireframe", "siwk.shading", {"type": 'WIREFRAME'}), ("Shaded", "siwk.shading", {"type": 'SHADED'}), ("Wireframe on Shaded", "siwk.shading", {"type": 'WIRE_ON_SHADED'}),
    ("Textured", "siwk.shading", {"type": 'TEXTURED'}), ("Constant", "siwk.shading", {"type": 'CONSTANT'}), ("Realtime", "siwk.shading", {"type": 'REALTIME'}),
    ("Rendered", "siwk.shading", {"type": 'RENDERED'}), None,
    ("X-Ray", "view3d.toggle_xray"), None, ("Show / Hide Grid", "siwk.toggle_grid"),
]
HELP = [("Blender Manual", "wm.url_open", {"url": "https://docs.blender.org/manual/en/latest/"}), ("About Blender", "wm.splash")]

MODEL = [
    S("Create", "SIWK_MT_create"), S("Modify", "SIWK_MT_modify"), None,
    ("Subdivision Surface +", "object.subdivision_set", {"level": 1, "relative": True}), ("Subdivision Surface -", "object.subdivision_set", {"level": -1, "relative": True}),
    None, ("Freeze (apply modifiers)", "object.convert", {"target": 'MESH'}), ("Freeze Transform", "object.transform_apply"),
]
CREATE = [
    ("Cube", "mesh.primitive_cube_add"), ("Sphere", "mesh.primitive_uv_sphere_add"), ("Icosphere", "mesh.primitive_ico_sphere_add"), ("Cylinder", "mesh.primitive_cylinder_add"),
    ("Cone", "mesh.primitive_cone_add"), ("Torus", "mesh.primitive_torus_add"), ("Grid", "mesh.primitive_grid_add"), ("Plane", "mesh.primitive_plane_add"), ("Monkey", "mesh.primitive_monkey_add"),
    None, ("Null (Empty)", "object.empty_add"), ("Camera", "object.camera_add"), ("Light", "object.light_add"), ("Bone / Armature", "object.armature_add"),
]
MODIFY = [
    ("Extrude", "mesh.extrude_region_move"), ("Bevel", "mesh.bevel"), ("Inset", "mesh.inset"), ("Subdivide", "mesh.subdivide"), ("Loop Cut", "mesh.loopcut_slide"), None,
    ("Dissolve", "mesh.dissolve_mode"), ("Collapse", "mesh.merge", {"type": 'COLLAPSE'}), ("Weld", "mesh.remove_doubles"), ("Bridge", "mesh.bridge_edge_loops"), ("Fill / Add Polygon", "mesh.edge_face_add"),
    None, ("Flip Normals", "mesh.flip_normals"), ("Triangulate", "mesh.quads_convert_to_tris"), ("Quadrangulate", "mesh.tris_convert_to_quads"), ("Symmetrize", "mesh.symmetrize"),
]
ANIMATE = [
    ("Save Key", "anim.keyframe_insert_menu"), ("Delete Key", "anim.keyframe_delete_v3d"), ("Clear Keys", "anim.keyframe_clear_v3d"), None,
    S("Constrain", "SIWK_MT_constrain"), ("Parent", "object.parent_set"), ("Cut (Clear Parent)", "object.parent_clear"), None,
    ("Add Armature", "object.armature_add"), ("Add Shape Key", "object.shape_key_add", {"from_mix": False}),
]
CONSTRAIN = [(n, "object.constraint_add", {"type": t}) for n, t in (("Position", 'COPY_LOCATION'), ("Orientation", 'COPY_ROTATION'), ("Scaling", 'COPY_SCALE'), ("Pose (Child Of)", 'CHILD_OF'),
                                                                   ("Direction (Track To)", 'TRACK_TO'), ("Path", 'FOLLOW_PATH'), ("Distance (Limit Distance)", 'LIMIT_DISTANCE'), ("Inverse Kinematics", 'IK'))]
RENDER = [
    ("Render Frame", "render.render", {"animation": False, "use_viewport": True}), ("Render Animation", "render.render", {"animation": True, "use_viewport": True}),
    ("View Last Render", "render.view_show"), None, ("Render Region", "view3d.render_border"), ("Clear Render Region", "view3d.clear_render_border"),
]
ICE = [("Add Geometry Nodes", "object.modifier_add", {"type": 'NODES'}), ("New Node Tree", "node.new_geometry_nodes_modifier"), ("Open Geometry Nodes Editor", "!")]
SIMULATE = [
    ("Rigid Body", "rigidbody.object_add"), ("Remove Rigid Body", "rigidbody.object_remove"), None,
    ("Cloth", "object.modifier_add", {"type": 'CLOTH'}), ("Soft Body", "object.modifier_add", {"type": 'SOFT_BODY'}), ("Fluid", "object.modifier_add", {"type": 'FLUID'}),
    ("Particle System", "object.particle_system_add"), None, ("Bake All Dynamics", "ptcache.bake_all", {"bake": True}),
]


def _window_items():
    items = _workspaces()
    items.append(None)
    items.append(("Preferences...", "screen.userpref_show"))
    return items


# ---------------------------------------------------------------------------------------------------------------- the toolbar panel's flyouts

def _modifier_items():
    items = []
    for label, t in (("Subdivision Surface", 'SUBSURF'), ("Bevel", 'BEVEL'), ("Mirror (Symmetry)", 'MIRROR'), ("Array", 'ARRAY'), ("Solidify", 'SOLIDIFY'), ("Smooth", 'SMOOTH'),
                     ("Displace", 'DISPLACE'), ("Lattice", 'LATTICE'), ("Shrinkwrap", 'SHRINKWRAP'), ("Boolean", 'BOOLEAN')):
        items.append((label, "object.modifier_add", {"type": t}))
    return items


LEFT_FLYOUTS = {
    "Primitive": CREATE[:9] + [None, ("Empty", "object.empty_add")],
    "Material": [("New Material", "material.new"), ("Assign Material Slot", "object.material_slot_add"), ("Remove Material Slot", "object.material_slot_remove")],
    "Property": _modifier_items,
    "Model": [("New Collection (Group)", "collection.create"), ("Link to Collection", "object.link_to_collection"), ("Move to Collection", "object.move_to_collection")],
    "Parameter": [("Insert Keyframe", "anim.keyframe_insert_menu"), ("Add Driver", "anim.driver_button_add"), ("Remove Driver", "anim.driver_button_remove")],
    "Curve": [("Bezier Curve", "curve.primitive_bezier_curve_add"), ("Bezier Circle", "curve.primitive_bezier_circle_add"), ("NURBS Curve", "curve.primitive_nurbs_curve_add"),
              ("NURBS Circle", "curve.primitive_nurbs_circle_add")],
    "Surface": [("NURBS Surface", "surface.primitive_nurbs_surface_surface_add"), ("NURBS Sphere", "surface.primitive_nurbs_surface_sphere_add"),
                ("NURBS Cylinder", "surface.primitive_nurbs_surface_cylinder_add"), ("NURBS Torus", "surface.primitive_nurbs_surface_torus_add")],
    "Path": [("Path", "curve.primitive_nurbs_path_add"), ("Follow Path Constraint", "object.constraint_add", {"type": 'FOLLOW_PATH'})],
    "Skeleton": [("Add Bone / Armature", "object.armature_add"), ("Human (Rigify)", "object.armature_human_metarig_add")],
    "Character": [("Parent with Automatic Weights", "object.parent_set", {"type": 'ARMATURE_AUTO'}), ("Parent with Empty Groups", "object.parent_set", {"type": 'ARMATURE_NAME'})],
    "Shape": [("Add Shape Key", "object.shape_key_add", {"from_mix": False}), ("Add Shape Key from Mix", "object.shape_key_add", {"from_mix": True}), ("Remove Shape Keys", "object.shape_key_remove", {"all": True})],
    "Envelope": [("Parent with Automatic Weights", "object.parent_set", {"type": 'ARMATURE_AUTO'}), ("Normalize Weights", "object.vertex_group_normalize_all"), ("Clean Weights", "object.vertex_group_clean")],
    "Deform": _modifier_items,
    "Store": [("Push Action Down (Store)", "nla.action_pushdown"), ("New Action", "action.new")],
    "Apply": [("Apply Pose", "pose.armature_apply"), ("Copy Pose", "pose.copy"), ("Paste Pose", "pose.paste")],
    "Templates": [("Add Armature", "object.armature_add"), ("Add Camera", "object.camera_add"), ("Add Light", "object.light_add")],
    "Plot": [("Bake Animation", "nla.bake"), ("Bake Action", "nla.bake", {"bake_types": {'POSE'}})],
    "Devices": [("Preferences...", "screen.userpref_show")],
    "Import/Export": [S("Import", "SIWK_MT_import"), S("Export", "SIWK_MT_export")],
    "MOTOR": [("MOTOR is not part of Blender", "!")],
    "Poly. Mesh": CREATE[:9],
    "Transform": [("Apply Location", "object.transform_apply", {"location": True, "rotation": False, "scale": False}), ("Apply Rotation", "object.transform_apply", {"location": False, "rotation": True, "scale": False}),
                  ("Apply Scale", "object.transform_apply", {"location": False, "rotation": False, "scale": True}), None, ("Origin to Geometry", "object.origin_set", {"type": 'ORIGIN_GEOMETRY'}),
                  ("Origin to 3D Cursor", "object.origin_set", {"type": 'ORIGIN_CURSOR'}), ("Clear Location", "object.location_clear"), ("Clear Rotation", "object.rotation_clear"), ("Clear Scale", "object.scale_clear")],
    "Component": MODIFY,
    "Constrain": CONSTRAIN,
    "Light": [("Point", "object.light_add", {"type": 'POINT'}), ("Sun", "object.light_add", {"type": 'SUN'}), ("Spot", "object.light_add", {"type": 'SPOT'}), ("Area", "object.light_add", {"type": 'AREA'})],
    "Camera": [("Camera", "object.camera_add"), ("Camera from View", "view3d.camera_to_view"), ("Look Through Camera", "view3d.object_as_camera")],
    "Pass": [("New View Layer", "scene.view_layer_add", {"type": 'NEW'}), ("Copy View Layer", "scene.view_layer_add", {"type": 'COPY'}), ("Remove View Layer", "scene.view_layer_remove")],
    "Frame": [("Render Frame", "render.render", {"animation": False, "use_viewport": True}), ("View Last Render", "render.view_show")],
    "Sequence": [("Render Animation", "render.render", {"animation": True, "use_viewport": True})],
    "Region": [("Render Region", "view3d.render_border"), ("Clear Render Region", "view3d.clear_render_border")],
    "Options": [("Preferences...", "screen.userpref_show")],
    "Rigid Body": [("Add Active Rigid Body", "rigidbody.object_add", {"type": 'ACTIVE'}), ("Add Passive Rigid Body", "rigidbody.object_add", {"type": 'PASSIVE'}), ("Remove Rigid Body", "rigidbody.object_remove")],
    "Cloth": [("Add Cloth", "object.modifier_add", {"type": 'CLOTH'}), ("Add Soft Body", "object.modifier_add", {"type": 'SOFT_BODY'})],
    "Fluid": [("Add Fluid", "object.modifier_add", {"type": 'FLUID'})],
    "Particles": [("Add Particle System", "object.particle_system_add"), ("Remove Particle System", "object.particle_system_remove")],
    "Bake": [("Bake All Dynamics", "ptcache.bake_all", {"bake": True}), ("Free All Bakes", "ptcache.free_bake_all")],
    "Clear": [("Clear Animation", "anim.keyframe_clear_v3d"), ("Clear Transforms", "object.location_clear")],
}

MODULES = ("Model", "Animate", "Render", "Simulate")


def flyout_id(label):
    return "SIWK_MT_fly_" + "".join(ch if ch.isalnum() else "_" for ch in label)


TOP_MENUS = {   # the menu bar: label -> menu id
    "File": "SIWK_MT_file", "Edit": "SIWK_MT_edit", "View": "SIWK_MT_view", "Display": "SIWK_MT_display", "Window": "SIWK_MT_window", "Help": "SIWK_MT_help",
    "Model": "SIWK_MT_model", "Animate": "SIWK_MT_animate", "Render": "SIWK_MT_render", "ICE": "SIWK_MT_ice", "Simulate": "SIWK_MT_simulate",
}


def _build():
    make_menu("SIWK_MT_file", "File", FILE)
    make_menu("SIWK_MT_import", "Import", IMPORT)
    make_menu("SIWK_MT_export", "Export", EXPORT)
    make_menu("SIWK_MT_edit", "Edit", EDIT)
    make_menu("SIWK_MT_view", "View", VIEW)
    make_menu("SIWK_MT_viewtype", "View Type", VIEWTYPE)
    make_menu("SIWK_MT_display", "Display", DISPLAY)
    make_menu("SIWK_MT_window", "Window", _window_items)
    make_menu("SIWK_MT_help", "Help", HELP)
    make_menu("SIWK_MT_model", "Model", MODEL)
    make_menu("SIWK_MT_create", "Create", CREATE)
    make_menu("SIWK_MT_modify", "Modify", MODIFY)
    make_menu("SIWK_MT_animate", "Animate", ANIMATE)
    make_menu("SIWK_MT_constrain", "Constrain", CONSTRAIN)
    make_menu("SIWK_MT_render", "Render", RENDER)
    make_menu("SIWK_MT_ice", "ICE", ICE)
    make_menu("SIWK_MT_simulate", "Simulate", SIMULATE)
    make_menu("SIWK_MT_modules", "Module", [(m, "siwk.set_module", {"module": m}) for m in MODULES])
    make_menu("SIWK_MT_show", "Show", [("Overlays", "wm.context_toggle", {"data_path": "space_data.overlay.show_overlays"}), ("Grid", "siwk.toggle_grid"), ("Statistics", "wm.context_toggle", {"data_path": "space_data.overlay.show_stats"}),
                                      ("Text Info", "wm.context_toggle", {"data_path": "space_data.overlay.show_text"}), ("Navigation Gizmo", "wm.context_toggle", {"data_path": "space_data.show_gizmo_navigate"}),
                                      ("Wireframe Overlay", "wm.context_toggle", {"data_path": "space_data.overlay.show_wireframes"}), ("X-Ray", "view3d.toggle_xray")])
    make_menu("SIWK_MT_explore", "Explore", [("Select Children", "object.select_grouped", {"type": 'CHILDREN'}), ("Select Immediate Children", "object.select_grouped", {"type": 'CHILDREN_RECURSIVE'}),
                                              ("Select Parent", "object.select_grouped", {"type": 'PARENT'}), ("Select Siblings", "object.select_grouped", {"type": 'SIBLINGS'}),
                                              ("Select Same Type", "object.select_grouped", {"type": 'TYPE'}), ("Select Same Collection", "object.select_grouped", {"type": 'COLLECTION'})])
    make_menu("SIWK_MT_scene_objects", "Scene", lambda: [(o.name, "siwk.scene_search", {"text": o.name}) for o in list(bpy.context.view_layer.objects)[:40]] or [("(the scene is empty)", "!")])
    make_menu("SIWK_MT_selection", "Selection", [("Select All", "siwk.select_all", {"action": 'SELECT'}), ("Invert", "siwk.select_all", {"action": 'INVERT'}), ("Deselect All", "siwk.select_all", {"action": 'DESELECT'}), None,
                                                  ("Grow", "mesh.select_more"), ("Shrink", "mesh.select_less"), ("Select Random", "object.select_random"), ("Select Linked", "object.select_linked")])
    make_menu("SIWK_MT_clusters", "Clusters", lambda: [(g.name, "object.vertex_group_set_active", {"group": g.name}) for g in (bpy.context.active_object.vertex_groups if bpy.context.active_object else [])]
                                                       + [None, ("New Cluster (Vertex Group)", "object.vertex_group_add"), ("Assign Selection", "object.vertex_group_assign"), ("Select Cluster", "object.vertex_group_select")])
    make_menu("SIWK_MT_constr_mode", "Construction Mode", [("Modeling", "siwk.set_module", {"module": "Model"}), ("Primary Shape", "!"), ("Animation", "siwk.set_module", {"module": "Animate"}), ("Secondary Shape", "!")])
    make_menu("SIWK_MT_passes", "Pass", lambda: [(vl.name, "siwk.set_view_layer", {"name": vl.name}) for vl in bpy.context.scene.view_layers])
    for label, items in LEFT_FLYOUTS.items():
        make_menu(flyout_id(label), label, items)


_built = False


def register():
    global _built
    if not _built:
        _build()
        _built = True
    for cls in _generated:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_generated):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
