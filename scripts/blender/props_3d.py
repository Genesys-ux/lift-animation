"""True 3D Art Deco Stylized Toon-PBR Handheld Props attached to 2.5D character hands.

All meshes live inside collection 'Env_Props3D' (child of 'Env_3D'), so they share the
exact same brushed brass, walnut, saddle leather, crimson lacquer, mirror glass,
real 3D shadow casting, live mirror reflections, and Freestyle ink outlines as the lobby!
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import bmesh
import bpy
from mathutils import Euler, Vector

from .compat import get_or_create_collection, link_obj_exclusive


def _assign_mat(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def _bevel(obj: bpy.types.Object, width: float = 0.005, segments: int = 1) -> None:
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(32.0)


def _pbox(
    name: str,
    size: Tuple[float, float, float],
    loc: Tuple[float, float, float],
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object,
    rot_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel: float = 0.004,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
    _assign_mat(obj, mat)
    if bevel > 0.0:
        _bevel(obj, bevel, 2)
    link_obj_exclusive(obj, col)
    obj.parent = parent
    return obj


def _pcyl(
    name: str,
    r1: float,
    r2: float,
    depth: float,
    loc: Tuple[float, float, float],
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    parent: bpy.types.Object,
    rot_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    verts: int = 22,
    smooth: bool = True,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=verts,
        radius1=r1,
        radius2=r2,
        depth=depth,
    )
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
    _assign_mat(obj, mat)
    link_obj_exclusive(obj, col)
    obj.parent = parent
    return obj


def _get_props_collection() -> bpy.types.Collection:
    env_col = get_or_create_collection("Env_3D")
    return get_or_create_collection("Env_Props3D", parent=env_col)


def clear_handheld_props() -> None:
    if "Env_Props3D" not in bpy.data.collections:
        return
    col = bpy.data.collections["Env_Props3D"]
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


# ==============================================================================
# 1. RAKA — ART DECO CAFÉ COFFEE CUP (3D)
# ==============================================================================
def build_3d_coffee(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    # Tapered cream porcelain/paper cup centered at grip sleeve (z=0)
    _pcyl(f"{name}_Cup", 0.056, 0.074, 0.22, (0, 0, 0.01), mats["coffee_cream"], col, root)
    # Art Deco brushed-brass & bronze ribbed sleeve wrapping cup!
    _pcyl(f"{name}_Sleeve", 0.064, 0.072, 0.095, (0, 0, 0.00), mats["walnut"], col, root)
    _pcyl(f"{name}_SleeveRimTop", 0.074, 0.074, 0.014, (0, 0, 0.048), mats["brass"], col, root)
    _pcyl(f"{name}_SleeveRimBot", 0.066, 0.066, 0.014, (0, 0, -0.048), mats["brass"], col, root)
    # Embossed Art Deco diamond emblem on front of sleeve
    _pbox(f"{name}_Emblem", (0.036, 0.016, 0.036), (0, -0.068, 0.0), mats["brass"], col, root, rot_deg=(0, 45, 0), bevel=0.002)
    # Stepped Art Deco domed lid with gold rim
    _pcyl(f"{name}_LidBase", 0.084, 0.082, 0.024, (0, 0, 0.125), mats["coffee_cream"], col, root)
    _pcyl(f"{name}_LidGold", 0.086, 0.086, 0.010, (0, 0, 0.114), mats["brass"], col, root)
    _pcyl(f"{name}_LidDome", 0.072, 0.064, 0.024, (0, 0, 0.148), mats["coffee_cream"], col, root)
    # Delicate curved 3D Bezier wispy steam curls rising organically above lid!
    for s_idx, (sx, sh, amp) in enumerate(((-0.020, 0.11, 0.016), (0.020, 0.09, -0.014))):
        cdata = bpy.data.curves.new(f"{name}_Steam_{s_idx}", type="CURVE")
        cdata.dimensions = "3D"
        cdata.bevel_depth = 0.0045
        cdata.bevel_resolution = 3
        sp = cdata.splines.new("BEZIER")
        sp.bezier_points.add(2)
        p0, p1, p2 = sp.bezier_points[0], sp.bezier_points[1], sp.bezier_points[2]
        p0.co = (sx, 0.0, 0.165)
        p0.handle_left = (sx, 0.0, 0.150)
        p0.handle_right = (sx - amp, 0.0, 0.185)
        p0.radius = 0.85
        p1.co = (sx + amp * 0.5, 0.0, 0.165 + sh * 0.55)
        p1.handle_left = (sx + amp, 0.0, 0.165 + sh * 0.35)
        p1.handle_right = (sx - amp * 0.6, 0.0, 0.165 + sh * 0.78)
        p1.radius = 1.0
        p2.co = (sx - amp * 0.3, 0.0, 0.165 + sh)
        p2.handle_left = (sx + amp * 0.4, 0.0, 0.165 + sh * 0.90)
        p2.handle_right = (sx - amp * 0.5, 0.0, 0.165 + sh * 1.08)
        p2.radius = 0.18
        sobj = bpy.data.objects.new(f"{name}_Steam_{s_idx}", cdata)
        _assign_mat(sobj, mats["sconce_glass"])
        link_obj_exclusive(sobj, col)
        sobj.parent = root
    return root


# ==============================================================================
# 2. RAKA — ART DECO STEPPED BRASS HAND MIRROR (3D WITH REAL REFLECTIVE GLASS!)
# ==============================================================================
def build_3d_hand_mirror(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    # Turned Art Deco walnut & brass grip handle centered at z=0
    _pcyl(f"{name}_Handle", 0.024, 0.020, 0.15, (0, 0, 0.00), mats["walnut"], col, root)
    _pcyl(f"{name}_Pommel", 0.030, 0.018, 0.032, (0, 0, -0.082), mats["brass"], col, root)
    _pcyl(f"{name}_Collar", 0.034, 0.028, 0.028, (0, 0, 0.082), mats["brass"], col, root)
    # Stepped octagonal/oval Art Deco gold brass frame (centered at z=+0.22m!)
    mz = 0.225
    _pcyl(f"{name}_FrameOuter", 0.132, 0.132, 0.034, (0, 0, mz), mats["dark_bronze"], col, root, rot_deg=(90, 0, 0), verts=12, smooth=False)
    _pcyl(f"{name}_FrameGold", 0.122, 0.122, 0.042, (0, 0, mz), mats["brass"], col, root, rot_deg=(90, 0, 0), verts=12, smooth=False)
    # Stepped Art Deco sunburst crown pediment on top!
    _pbox(f"{name}_Crown1", (0.095, 0.040, 0.032), (0, 0, mz + 0.130), mats["brass"], col, root, bevel=0.003)
    _pbox(f"{name}_Crown2", (0.052, 0.042, 0.028), (0, 0, mz + 0.154), mats["brass"], col, root, bevel=0.003)
    # TRUE reflective mirror glass on front (-Y)!
    _pcyl(f"{name}_GlassFront", 0.098, 0.098, 0.008, (0, -0.022, mz), mats["mirror_glass"], col, root, rot_deg=(90, 0, 0), verts=24)
    # Engraved Art Deco sunburst diamond relief on back (+Y)!
    _pbox(f"{name}_BackDiamond", (0.072, 0.016, 0.072), (0, 0.022, mz), mats["brass"], col, root, rot_deg=(0, 45, 0), bevel=0.003)
    _pbox(f"{name}_BackBarH", (0.150, 0.012, 0.018), (0, 0.020, mz), mats["dark_bronze"], col, root, bevel=0.002)
    _pbox(f"{name}_BackBarV", (0.018, 0.012, 0.150), (0, 0.020, mz), mats["dark_bronze"], col, root, bevel=0.002)
    return root


# ==============================================================================
# 3. PAK BIMA — ART DECO WALNUT & BRASS "KOMPLAIN 99%" CLIPBOARD (3D)
# ==============================================================================
def build_3d_clipboard(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    # Board sits offset cleanly upward-left from grip hand so hand clutches lower-right edge!
    ox, oz = -0.05, 0.08
    _pbox(f"{name}_Board", (0.28, 0.022, 0.36), (ox, 0, oz), mats["walnut"], col, root, bevel=0.006)
    # Art Deco brass corner brackets
    for sx in (-1, 1):
        for sz in (-1, 1):
            _pbox(f"{name}_Corner_{sx}_{sz}", (0.052, 0.028, 0.052), (ox + sx * 0.118, 0, oz + sz * 0.158), mats["brass"], col, root, bevel=0.003)
    # Layered cream paper sheets on front (-Y)
    _pbox(f"{name}_PaperBack", (0.23, 0.008, 0.30), (ox + 0.006, -0.013, oz - 0.005), mats["paper_cream"], col, root, rot_deg=(0, 3, 0), bevel=0.001)
    _pbox(f"{name}_PaperFront", (0.23, 0.008, 0.30), (ox, -0.018, oz), mats["paper_cream"], col, root, bevel=0.001)
    # Bold red header bar & 3D raised skyrocketing red complaint chart bars!
    _pbox(f"{name}_HeaderRed", (0.18, 0.008, 0.032), (ox, -0.023, oz + 0.102), mats["paper_red"], col, root, bevel=0.001)
    for idx, (bx, bh) in enumerate(((-0.068, 0.04), (-0.024, 0.07), (0.020, 0.11), (0.064, 0.165))):
        _pbox(f"{name}_Bar_{idx}", (0.028, 0.010, bh), (ox + bx, -0.024, oz - 0.105 + bh * 0.5), mats["crimson_lacquer"], col, root, bevel=0.002)
    # Yellow panic sticky note peeking off side!
    _pbox(f"{name}_Sticky", (0.085, 0.009, 0.082), (ox + 0.095, -0.027, oz + 0.01), mats["sticky_yellow"], col, root, rot_deg=(0, -10, 0), bevel=0.001)
    # Stepped Art Deco brass spring clip at top
    _pbox(f"{name}_ClipBase", (0.125, 0.036, 0.048), (ox, -0.010, oz + 0.168), mats["brass"], col, root, bevel=0.004)
    _pcyl(f"{name}_ClipRing", 0.024, 0.024, 0.026, (ox, -0.016, oz + 0.194), mats["brass"], col, root, rot_deg=(90, 0, 0))
    return root


# ==============================================================================
# 4. PAK BIMA — ART DECO CRIMSON & BRASS FOUNTAIN PEN (3D)
# ==============================================================================
def build_3d_pen(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    _pcyl(f"{name}_Barrel", 0.016, 0.018, 0.21, (0, 0, 0.02), mats["crimson_lacquer"], col, root, rot_deg=(0, 38, 0), verts=14)
    _pcyl(f"{name}_Band", 0.020, 0.020, 0.022, (0.03, 0, 0.055), mats["brass"], col, root, rot_deg=(0, 38, 0), verts=14)
    _pcyl(f"{name}_Nib", 0.016, 0.002, 0.068, (0.078, 0, 0.118), mats["brass"], col, root, rot_deg=(0, 38, 0), verts=12)
    return root


# ==============================================================================
# 5. PAK DONI — ART DECO SADDLE-LEATHER & BRASS BRIEFCASE (3D)
# ==============================================================================
def build_3d_briefcase(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    # Curved leather & brass grip handle centered right at Z = 0 (inside Pak Doni's hand!)
    _pbox(f"{name}_HandleTop", (0.125, 0.030, 0.026), (0, 0, 0.005), mats["leather"], col, root, bevel=0.008)
    _pbox(f"{name}_HandlePostL", (0.022, 0.024, 0.055), (-0.054, 0, -0.025), mats["brass"], col, root, bevel=0.004)
    _pbox(f"{name}_HandlePostR", (0.022, 0.024, 0.055), (0.054, 0, -0.025), mats["brass"], col, root, bevel=0.004)
    # Main sculpted beveled 3D Art Deco leather case hanging below grip
    cz = -0.185
    _pbox(f"{name}_Body", (0.37, 0.135, 0.27), (0, 0, cz), mats["leather"], col, root, bevel=0.018)
    # Upper overlapping leather flap
    _pbox(f"{name}_Flap", (0.378, 0.144, 0.105), (0, 0, cz + 0.088), mats["leather"], col, root, bevel=0.012)
    # Art Deco stepped brass corner guards & speed-line trim!
    for sx in (-1, 1):
        for sz in (-1, 1):
            _pbox(f"{name}_Corner_{sx}_{sz}", (0.055, 0.146, 0.055), (sx * 0.162, 0, cz + sz * 0.112), mats["brass"], col, root, bevel=0.006)
    _pbox(f"{name}_TrimFront", (0.35, 0.016, 0.018), (0, -0.072, cz + 0.034), mats["brass"], col, root, bevel=0.003)
    _pbox(f"{name}_TrimBack", (0.35, 0.016, 0.018), (0, 0.072, cz + 0.034), mats["brass"], col, root, bevel=0.003)
    # Dual gleaming Art Deco brass clasp locks on BOTH front & back faces!
    for lx in (-0.095, 0.095):
        _pbox(f"{name}_ClaspF_{lx}", (0.044, 0.026, 0.062), (lx, -0.072, cz + 0.036), mats["brass"], col, root, bevel=0.005)
        _pbox(f"{name}_ClaspB_{lx}", (0.044, 0.026, 0.062), (lx, 0.072, cz + 0.036), mats["brass"], col, root, bevel=0.005)
    return root


# ==============================================================================
# 6. PAK DONI — ART DECO GOLD & WALNUT POCKET COMB (3D)
# ==============================================================================
def build_3d_comb(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    # Angled comb held above fist!
    piv = bpy.data.objects.new(f"{name}_Pivot", None)
    piv.location = (0.0, 0.0, 0.045)
    piv.rotation_euler = Euler((0.0, math.radians(-28.0), 0.0), "XYZ")
    link_obj_exclusive(piv, col)
    piv.parent = root
    # Stepped Art Deco walnut + brushed gold spine
    _pbox(f"{name}_Spine", (0.23, 0.024, 0.036), (0, 0, 0.022), mats["walnut"], col, piv, bevel=0.006)
    _pbox(f"{name}_GoldInlay", (0.205, 0.028, 0.014), (0, 0, 0.024), mats["brass"], col, piv, bevel=0.003)
    # 10 crisp individual sculpted 3D golden/walnut comb teeth!
    for i in range(10):
        tx = -0.095 + i * (0.190 / 9.0)
        _pbox(f"{name}_Tooth_{i}", (0.011, 0.014, 0.052), (tx, 0, -0.018), mats["brass"], col, piv, bevel=0.002)
    return root


# ==============================================================================
# 7. PAK DONI — ART DECO OCTAGONAL GOLD WRISTWATCH (3D)
# ==============================================================================
def build_3d_watch(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    # Leather strap + octagonal Art Deco gold casing + glowing white dial + red hand!
    _pbox(f"{name}_Strap", (0.11, 0.036, 0.045), (0, 0, 0), mats["leather"], col, root, bevel=0.006)
    _pcyl(f"{name}_Bezel", 0.052, 0.052, 0.038, (0, -0.008, 0), mats["brass"], col, root, rot_deg=(90, 0, 0), verts=8, smooth=False)
    _pcyl(f"{name}_Dial", 0.038, 0.038, 0.042, (0, -0.010, 0), mats["clock_face"], col, root, rot_deg=(90, 0, 0), verts=20)
    _pbox(f"{name}_Hand1", (0.008, 0.008, 0.028), (0, -0.033, 0.009), mats["dark_bronze"], col, root, bevel=0.001)
    _pbox(f"{name}_Hand2", (0.024, 0.008, 0.007), (0.008, -0.034, -0.004), mats["crimson_lacquer"], col, root, bevel=0.001)
    return root


# ==============================================================================
# 8. CLARA — ART DECO ROLLED TURBO-LIFT BLUEPRINT CYLINDER (3D)
# ==============================================================================
def build_3d_blueprint(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    piv = bpy.data.objects.new(f"{name}_Pivot", None)
    piv.location = (0.0, 0.0, 0.04)
    piv.rotation_euler = Euler((0.0, math.radians(-22.0), 0.0), "XYZ")
    link_obj_exclusive(piv, col)
    piv.parent = root
    # Rolled cyan/Prussian blue architectural blueprint tube
    _pcyl(f"{name}_Roll", 0.054, 0.054, 0.34, (0, 0, 0.03), mats["blueprint_blue"], col, piv)
    # Recessed cream inner spiral core peeking out both ends
    _pcyl(f"{name}_Core", 0.036, 0.036, 0.346, (0, 0, 0.03), mats["paper_cream"], col, piv)
    _pcyl(f"{name}_Hole", 0.018, 0.018, 0.350, (0, 0, 0.03), mats["dark_bronze"], col, piv)
    # Art Deco brass end trim rings + bold crimson center strap!
    _pcyl(f"{name}_RingTop", 0.057, 0.057, 0.018, (0, 0, 0.16), mats["brass"], col, piv)
    _pcyl(f"{name}_RingBot", 0.057, 0.057, 0.018, (0, 0, -0.10), mats["brass"], col, piv)
    _pcyl(f"{name}_StrapRed", 0.059, 0.059, 0.034, (0, 0, 0.02), mats["crimson_lacquer"], col, piv)
    # Uncurling schematic corner flap peeking out right side!
    _pbox(f"{name}_Flap", (0.12, 0.010, 0.17), (0.085, 0.012, 0.06), mats["blueprint_blue"], col, piv, rot_deg=(0, 8, -16), bevel=0.002)
    _pbox(f"{name}_Line1", (0.075, 0.014, 0.010), (0.085, 0.010, 0.095), mats["paper_cream"], col, piv, rot_deg=(0, 8, -16), bevel=0.001)
    _pbox(f"{name}_Line2", (0.060, 0.014, 0.010), (0.085, 0.010, 0.055), mats["paper_cream"], col, piv, rot_deg=(0, 8, -16), bevel=0.001)
    return root


# ==============================================================================
# 9. CLARA — ART DECO INDUSTRIAL BRUSHED-STEEL & BRASS WRENCH (3D)
# ==============================================================================
def build_3d_wrench(name: str, mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    link_obj_exclusive(root, col)
    piv = bpy.data.objects.new(f"{name}_Pivot", None)
    piv.location = (0.0, 0.0, 0.04)
    piv.rotation_euler = Euler((0.0, math.radians(26.0), 0.0), "XYZ")
    link_obj_exclusive(piv, col)
    piv.parent = root
    # Chunky beveled steel shaft + Art Deco brass grip collar
    _pbox(f"{name}_Shaft", (0.048, 0.026, 0.25), (0, 0, 0.04), mats["steel"], col, piv, bevel=0.005)
    _pbox(f"{name}_GripBrass", (0.056, 0.032, 0.072), (0, 0, -0.01), mats["brass"], col, piv, bevel=0.005)
    # Sculpted open C-jaw spanner head at top!
    _pbox(f"{name}_JawBase", (0.118, 0.032, 0.052), (0, 0, 0.165), mats["steel"], col, piv, bevel=0.005)
    _pbox(f"{name}_JawL", (0.038, 0.032, 0.088), (-0.044, 0, 0.215), mats["steel"], col, piv, rot_deg=(0, 14, 0), bevel=0.005)
    _pbox(f"{name}_JawR", (0.038, 0.032, 0.088), (0.044, 0, 0.215), mats["steel"], col, piv, rot_deg=(0, -14, 0), bevel=0.005)
    # Closed ring spanner tail at bottom
    _pcyl(f"{name}_RingOut", 0.044, 0.044, 0.028, (0, 0, -0.102), mats["steel"], col, piv, rot_deg=(90, 0, 0))
    _pcyl(f"{name}_RingIn", 0.020, 0.020, 0.032, (0, 0, -0.102), mats["dark_bronze"], col, piv, rot_deg=(90, 0, 0))
    return root


PROP_BUILDERS = {
    "coffee": build_3d_coffee,
    "mirror": build_3d_hand_mirror,
    "clipboard": build_3d_clipboard,
    "pen": build_3d_pen,
    "briefcase": build_3d_briefcase,
    "comb": build_3d_comb,
    "watch": build_3d_watch,
    "blueprint": build_3d_blueprint,
    "wrench": build_3d_wrench,
}


def attach_3d_art_deco_props(
    card_obj: bpy.types.Object,
    manifest: dict,
    char_id: str,
    angle_key: str,
    mats: Dict[str, bpy.types.Material],
    flip_x: bool = False,
    scale: float = 1.0,
) -> Dict[str, bpy.types.Object]:
    """Build and attach all true 3D Art Deco handheld props directly to a character card's hand grip anchors!"""
    col = _get_props_collection()
    anchors = manifest["characters"][char_id]["hand_anchors_m"].get(angle_key, {})
    created: Dict[str, bpy.types.Object] = {}

    # Subtle prop yaw so 3D depth bevels catch studio specular highlights even in front view!
    prop_yaw_deg = {
        "coffee": 18.0,
        "mirror": -22.0,
        "clipboard": 18.0,
        "pen": -14.0,
        "briefcase": -26.0,
        "comb": 18.0,
        "watch": 10.0,
        "blueprint": 22.0,
        "wrench": -18.0,
    }

    for prop_key, (ax, ay, az) in anchors.items():
        if prop_key not in PROP_BUILDERS:
            continue
        px = (-ax if flip_x else ax) * scale
        py = ay * scale
        pz = az * scale

        prop_root = PROP_BUILDERS[prop_key](f"{card_obj.name}_Prop3D_{prop_key}", mats, col)
        prop_root.parent = card_obj
        prop_root.location = (px, py, pz)
        yaw = prop_yaw_deg.get(prop_key, 15.0) * (-1.0 if flip_x else 1.0)
        # Rotate mirror slightly toward camera or back depending on angle
        if prop_key == "mirror" and angle_key in ("back", "back_three_quarter"):
            yaw += 180.0
        if prop_key == "clipboard" and angle_key in ("back", "back_three_quarter"):
            yaw += 180.0
        prop_root.rotation_euler = Euler((0.0, 0.0, math.radians(yaw)), "XYZ")
        prop_root.scale = (scale, scale, scale)
        created[prop_key] = prop_root

    return created
