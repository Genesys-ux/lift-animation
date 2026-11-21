"""Procedural Blender (bpy) builder for the Grand Art Deco Skyscraper Lobby (Opsi 2).

All geometry is built in real-world meters (+X right, +Y toward elevator wall, +Z up)
and proportioned specifically for dramatic 9:16 vertical cinematography.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

import bmesh
import bpy
from mathutils import Euler, Vector

from .compat import get_or_create_collection, link_obj_exclusive


def _assign_mat(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def _add_bevel(obj: bpy.types.Object, width: float = 0.015, segments: int = 1) -> None:
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(32.0)


def _box(
    name: str,
    size: Tuple[float, float, float],
    loc: Tuple[float, float, float],
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    rot: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel: float = 0.012,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler(rot, "XYZ")
    _assign_mat(obj, mat)
    if bevel > 0.0:
        _add_bevel(obj, width=bevel, segments=1)
    link_obj_exclusive(obj, col)
    return obj


def _cyl(
    name: str,
    radius: float,
    depth: float,
    loc: Tuple[float, float, float],
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    rot: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    verts: int = 28,
    smooth: bool = True,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=verts,
        radius1=radius,
        radius2=radius,
        depth=depth,
    )
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True

    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler(rot, "XYZ")
    _assign_mat(obj, mat)
    link_obj_exclusive(obj, col)
    return obj


def _cone(
    name: str,
    r1: float,
    r2: float,
    depth: float,
    loc: Tuple[float, float, float],
    mat: bpy.types.Material,
    col: bpy.types.Collection,
    rot: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    verts: int = 24,
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
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler(rot, "XYZ")
    _assign_mat(obj, mat)
    link_obj_exclusive(obj, col)
    return obj


def _build_gear(
    name: str,
    radius: float,
    thickness: float,
    teeth: int,
    loc: Tuple[float, float, float],
    mat: bpy.types.Material,
    col: bpy.types.Collection,
) -> bpy.types.Object:
    """Build a crisp stylized 3D mechanical clock gear facing -Y."""
    parent = _cyl(
        name,
        radius=radius * 0.84,
        depth=thickness,
        loc=loc,
        mat=mat,
        col=col,
        rot=(math.radians(90), 0.0, 0.0),
        verts=24,
        smooth=False,
    )
    for i in range(teeth):
        ang = (2.0 * math.pi * i) / teeth
        # Parent cylinder's circular face lies in local XY plane (rotated 90° X into world XZ)!
        tx = math.cos(ang) * radius * 0.90
        ty = math.sin(ang) * radius * 0.90
        tooth = _box(
            f"{name}_Tooth_{i}",
            (radius * 0.25, radius * 0.18, thickness * 0.96),
            (tx, ty, 0.0),
            mat,
            col,
            rot=(0.0, 0.0, ang),
            bevel=0.004,
        )
        tooth.parent = parent
    return parent


def _build_elevator_bay(
    prefix: str,
    cx: float,
    wall_y: float,
    mats: Dict[str, bpy.types.Material],
    col: bpy.types.Collection,
) -> Dict[str, bpy.types.Object]:
    """Build one complete Art Deco brass elevator bay with sliding doors + semicircular floor dial."""
    door_w = 1.72
    door_h = 2.75
    half_w = door_w * 0.5

    # Stepped Art Deco outer brass frame (3 tiered steps!)
    frame_specs = [
        (door_w + 0.44, 0.16, door_h + 0.28, 0.08, mats["dark_bronze"]),
        (door_w + 0.30, 0.22, door_h + 0.20, 0.11, mats["brass"]),
        (door_w + 0.14, 0.26, door_h + 0.10, 0.13, mats["dark_bronze"]),
    ]
    for i, (fw, fd, fh, y_off, fmat) in enumerate(frame_specs):
        # Left jamb, right jamb, top lintel
        jamb_w = (fw - door_w) * 0.5 + 0.04
        _box(f"{prefix}_JambL_{i}", (jamb_w, fd, fh), (cx - half_w - jamb_w * 0.5 + 0.02, wall_y - y_off, fh * 0.5), fmat, col, bevel=0.01)
        _box(f"{prefix}_JambR_{i}", (jamb_w, fd, fh), (cx + half_w + jamb_w * 0.5 - 0.02, wall_y - y_off, fh * 0.5), fmat, col, bevel=0.01)
        lintel_h = fh - door_h + 0.04
        _box(f"{prefix}_Lintel_{i}", (fw, fd, lintel_h), (cx, wall_y - y_off, door_h + lintel_h * 0.5 - 0.02), fmat, col, bevel=0.01)

    # Dark interior elevator shaft backing (visible when doors slide open in Stage 4!)
    _box(f"{prefix}_ShaftBack", (door_w + 0.1, 0.08, door_h + 0.1), (cx, wall_y + 0.85, door_h * 0.5), mats["walnut"], col, bevel=0.0)
    _box(f"{prefix}_ShaftFloor", (door_w + 0.1, 1.0, 0.05), (cx, wall_y + 0.42, 0.01), mats["floor_marble"], col, bevel=0.0)

    # Twin sliding brushed-brass elevator doors with embossed Art Deco chevron relief panels!
    leaf_w = half_w - 0.012
    door_l = _box(f"{prefix}_DoorL", (leaf_w, 0.08, door_h), (cx - half_w * 0.5, wall_y + 0.02, door_h * 0.5), mats["brass"], col, bevel=0.008)
    door_r = _box(f"{prefix}_DoorR", (leaf_w, 0.08, door_h), (cx + half_w * 0.5, wall_y + 0.02, door_h * 0.5), mats["brass"], col, bevel=0.008)

    for side_tag, door in (("L", door_l), ("R", door_r)):
        sgn = -1.0 if side_tag == "L" else 1.0
        # Recessed bronze border inlay panel
        panel = _box(f"{prefix}_Panel_{side_tag}", (leaf_w * 0.72, 0.025, door_h * 0.82), (0.0, -0.042, 0.0), mats["dark_bronze"], col, bevel=0.004)
        panel.parent = door
        # Raised inner brass Art Deco stepped stripe
        inner = _box(f"{prefix}_Inner_{side_tag}", (leaf_w * 0.56, 0.032, door_h * 0.72), (0.0, -0.046, 0.0), mats["brass"], col, bevel=0.004)
        inner.parent = door
        # Three crisp Art Deco geometric chevron bars across door center!
        for k, z_bar in enumerate((-0.45, 0.0, 0.45)):
            bar = _box(
                f"{prefix}_Chev_{side_tag}_{k}",
                (leaf_w * 0.58, 0.036, 0.075),
                (0.0, -0.052, z_bar),
                mats["dark_bronze"],
                col,
                rot=(0.0, math.radians(18.0 * sgn), 0.0),
                bevel=0.004,
            )
            bar.parent = door
        # Vertical brass handle bar near center seam
        handle = _cyl(
            f"{prefix}_Handle_{side_tag}",
            radius=0.016,
            depth=0.42,
            loc=(-sgn * (leaf_w * 0.36), -0.075, -0.15),
            mat=mats["brass"],
            col=col,
        )
        handle.parent = door

    # Semicircular Mechanical Art Deco Floor-Dial Indicator right above the doors!
    dial_z = door_h + 0.44
    dial_y = wall_y - 0.14
    # Brass arch housing
    _cyl(f"{prefix}_DialFrame", radius=0.46, depth=0.12, loc=(cx, dial_y, dial_z), mat=mats["brass"], col=col, rot=(math.radians(90), 0, 0), verts=32)
    _cyl(f"{prefix}_DialFace", radius=0.39, depth=0.13, loc=(cx, dial_y - 0.01, dial_z), mat=mats["clock_face"], col=col, rot=(math.radians(90), 0, 0), verts=32)
    # Mask bottom half of cylinder into classic semicircular Art Deco dial!
    _box(f"{prefix}_DialMask", (0.98, 0.22, 0.48), (cx, dial_y - 0.02, dial_z - 0.24), mats["brass"], col, bevel=0.01)

    # 9 golden floor-number tick batons around upper semicircle (floors 1..9)
    for t in range(9):
        ang = math.radians(165.0 - t * (150.0 / 8.0))
        tx = cx + math.cos(ang) * 0.32
        tz = dial_z + math.sin(ang) * 0.32
        _box(f"{prefix}_DialTick_{t}", (0.022, 0.04, 0.07), (tx, dial_y - 0.075, tz), mats["dark_bronze"], col, rot=(0, -(ang - math.pi * 0.5), 0), bevel=0.002)

    # Physical animatable 3D Crimson Dial Needle (pivots around Y axis at dial center!)
    needle_pivot = bpy.data.objects.new(f"{prefix}_DialNeedlePivot", None)
    needle_pivot.location = (cx, dial_y - 0.09, dial_z + 0.02)
    needle_pivot.rotation_euler = (0.0, math.radians(-52.0 if cx < 0 else 40.0), 0.0)
    link_obj_exclusive(needle_pivot, col)

    needle_blade = _box(f"{prefix}_DialNeedle", (0.032, 0.025, 0.31), (0.0, 0.0, 0.13), mats["crimson_lacquer"], col, bevel=0.003)
    needle_blade.parent = needle_pivot
    needle_cap = _cyl(f"{prefix}_DialCap", radius=0.045, depth=0.05, loc=(0.0, -0.01, 0.0), mat=mats["brass"], col=col, rot=(math.radians(90), 0, 0))
    needle_cap.parent = needle_pivot

    return {"door_l": door_l, "door_r": door_r, "dial_needle": needle_pivot}


def _build_hero_wall_clock(
    wall_y: float,
    mats: Dict[str, bpy.types.Material],
    col: bpy.types.Collection,
) -> Dict[str, bpy.types.Object]:
    """HERO STORY PROP #1: Giant Mechanical Art Deco Lobby Clock towering above the elevators!"""
    cz = 4.55
    cy = wall_y - 0.16
    r_outer = 0.88

    # Stepped golden brass Art Deco bezel rings
    _cyl("HeroClock_RimOuter", r_outer, 0.18, (0.0, cy, cz), mats["dark_bronze"], col, (math.radians(90), 0, 0), verts=48)
    _cyl("HeroClock_RimGold", r_outer - 0.06, 0.22, (0.0, cy - 0.02, cz), mats["brass"], col, (math.radians(90), 0, 0), verts=48)
    _cyl("HeroClock_Face", r_outer - 0.14, 0.23, (0.0, cy - 0.025, cz), mats["clock_face"], col, (math.radians(90), 0, 0), verts=48)

    # Decorative Art Deco sunburst rays projecting behind clock rim!
    for i in range(16):
        ang = (2.0 * math.pi * i) / 16.0
        ray_len = 0.36 if i % 2 == 0 else 0.22
        rx = math.cos(ang) * (r_outer + ray_len * 0.42)
        rz = cz + math.sin(ang) * (r_outer + ray_len * 0.42)
        _box(
            f"HeroClock_Ray_{i}",
            (0.055 if i % 2 == 0 else 0.032, 0.06, ray_len),
            (rx, cy + 0.04, rz),
            mats["brass"],
            col,
            rot=(0.0, -(ang - math.pi * 0.5), 0.0),
            bevel=0.005,
        )

    # Exposed spinning brass clockwork gears inset on clock face for mechanical storytelling!
    gear_a = _build_gear("HeroClock_GearA", 0.22, 0.03, 12, (-0.22, cy - 0.145, cz - 0.16), mats["brass"], col)
    gear_b = _build_gear("HeroClock_GearB", 0.16, 0.03, 10, (0.14, cy - 0.145, cz - 0.26), mats["dark_bronze"], col)

    # 12 bold golden/bronze Art Deco hour baton markers
    for h in range(12):
        ang = math.radians(90.0 - h * 30.0)
        is_cardinal = h % 3 == 0
        dist = r_outer - 0.24
        hx = math.cos(ang) * dist
        hz = cz + math.sin(ang) * dist
        _box(
            f"HeroClock_HourMark_{h}",
            (0.055 if is_cardinal else 0.032, 0.04, 0.16 if is_cardinal else 0.11),
            (hx, cy - 0.145, hz),
            mats["dark_bronze"] if is_cardinal else mats["brass"],
            col,
            rot=(0.0, -(ang - math.pi * 0.5), 0.0),
            bevel=0.004,
        )

    # Animatable Clock Hands (all pivot cleanly around local Y axis!)
    hand_y = cy - 0.18
    hour_piv = bpy.data.objects.new("HeroClock_HourPivot", None)
    hour_piv.location = (0.0, hand_y, cz)
    hour_piv.rotation_euler = (0.0, math.radians(55.0), 0.0)  # ~10:10 iconic watch posture!
    link_obj_exclusive(hour_piv, col)
    h_mesh = _box("HeroClock_HourHand", (0.068, 0.028, 0.44), (0.0, 0.0, 0.17), mats["dark_bronze"], col, bevel=0.005)
    h_mesh.parent = hour_piv

    min_piv = bpy.data.objects.new("HeroClock_MinPivot", None)
    min_piv.location = (0.0, hand_y - 0.025, cz)
    min_piv.rotation_euler = (0.0, math.radians(-58.0), 0.0)
    link_obj_exclusive(min_piv, col)
    m_mesh = _box("HeroClock_MinHand", (0.048, 0.026, 0.62), (0.0, 0.0, 0.25), mats["dark_bronze"], col, bevel=0.004)
    m_mesh.parent = min_piv

    sec_piv = bpy.data.objects.new("HeroClock_SecPivot", None)
    sec_piv.location = (0.0, hand_y - 0.05, cz)
    sec_piv.rotation_euler = (0.0, math.radians(-145.0), 0.0)
    link_obj_exclusive(sec_piv, col)
    s_mesh = _box("HeroClock_SecHand", (0.026, 0.022, 0.72), (0.0, 0.0, 0.24), mats["crimson_lacquer"], col, bevel=0.003)
    s_mesh.parent = sec_piv

    # Center brass boss cap
    _cyl("HeroClock_CenterCap", 0.085, 0.09, (0.0, hand_y - 0.04, cz), mats["brass"], col, (math.radians(90), 0, 0))

    return {
        "clock_hour": hour_piv,
        "clock_min": min_piv,
        "clock_sec": sec_piv,
        "clock_gear_a": gear_a,
        "clock_gear_b": gear_b,
    }


def _build_art_deco_mirrors(
    wall_y: float,
    mats: Dict[str, bpy.types.Material],
    mirrors_col: bpy.types.Collection,
    alcove_col: bpy.types.Collection,
) -> Dict[str, bpy.types.Object]:
    """HERO STORY PROP #2: Grand Art Deco Framed Mirrors + Zero-Raytracing Optical Mirrored Alcove!"""
    # 1. CENTER PIER MIRROR (mounted right between the twin elevators, X = 0, Z = 1.66m!)
    mw, mh = 1.24, 2.18
    mz = 1.66
    my = wall_y - 0.14

    # Hollow stepped beveled gold Art Deco frame (4 perimeter rails so center opening can act as an optical portal!)
    rail_w = 0.12
    # Outer dark bronze perimeter rails
    _box("MirrorCenter_OuterL", (rail_w, 0.12, mh + 0.24), (-(mw * 0.5 + rail_w * 0.5), my + 0.02, mz), mats["dark_bronze"], mirrors_col, bevel=0.012)
    _box("MirrorCenter_OuterR", (rail_w, 0.12, mh + 0.24), ((mw * 0.5 + rail_w * 0.5), my + 0.02, mz), mats["dark_bronze"], mirrors_col, bevel=0.012)
    _box("MirrorCenter_OuterT", (mw + 0.24, 0.12, rail_w), (0.0, my + 0.02, mz + mh * 0.5 + rail_w * 0.5), mats["dark_bronze"], mirrors_col, bevel=0.012)
    _box("MirrorCenter_OuterB", (mw + 0.24, 0.12, rail_w), (0.0, my + 0.02, mz - mh * 0.5 - rail_w * 0.5), mats["dark_bronze"], mirrors_col, bevel=0.012)

    # Inner gleaming brushed-brass stepped perimeter rails
    gold_w = 0.085
    _box("MirrorCenter_GoldL", (gold_w, 0.15, mh + 0.16), (-(mw * 0.5 + gold_w * 0.45), my, mz), mats["brass"], mirrors_col, bevel=0.010)
    _box("MirrorCenter_GoldR", (gold_w, 0.15, mh + 0.16), ((mw * 0.5 + gold_w * 0.45), my, mz), mats["brass"], mirrors_col, bevel=0.010)
    _box("MirrorCenter_GoldT", (mw + 0.16, 0.15, gold_w), (0.0, my, mz + mh * 0.5 + gold_w * 0.45), mats["brass"], mirrors_col, bevel=0.010)
    _box("MirrorCenter_GoldB", (mw + 0.16, 0.15, gold_w), (0.0, my, mz - mh * 0.5 - gold_w * 0.45), mats["brass"], mirrors_col, bevel=0.010)

    # Art Deco stepped pediment crown above mirror
    _box("MirrorCenter_Crown1", (0.76, 0.16, 0.16), (0.0, my, mz + mh * 0.5 + 0.14), mats["brass"], mirrors_col, bevel=0.010)
    _box("MirrorCenter_Crown2", (0.42, 0.17, 0.15), (0.0, my - 0.01, mz + mh * 0.5 + 0.26), mats["brass"], mirrors_col, bevel=0.010)
    # Corner geometric brass diamond studs
    for sx in (-1, 1):
        for sz in (-1, 1):
            _box(
                f"MirrorCenter_Stud_{sx}_{sz}",
                (0.11, 0.06, 0.11),
                (sx * (mw * 0.5 + 0.04), my - 0.075, mz + sz * (mh * 0.5 + 0.04)),
                mats["brass"],
                mirrors_col,
                rot=(0.0, math.radians(45.0), 0.0),
                bevel=0.004,
            )

    # Physical opaque reflective mirror glass (used in Cycles / raytraced mode & Scene 7 drop-in)
    mirror_plane = _box("MirrorCenter_Glass", (mw, 0.02, mh), (0.0, my - 0.065, mz), mats["mirror_glass"], mirrors_col, bevel=0.0)

    # Crisp stylized 2.5D diagonal glass sheen accents tucked cleanly across upper-left mirror corner
    # (both ends tuck neatly behind GoldL & GoldT rails — classic animated glass gleam with 0ms raytrace cost!)
    sheen_a = _box(
        "MirrorCenter_SheenA",
        (0.055, 0.004, 0.72),
        (-0.37, my - 0.062, 2.50),
        mats["mirror_sheen"],
        alcove_col,
        rot=(0.0, math.radians(45.0), 0.0),
        bevel=0.0,
    )
    sheen_b = _box(
        "MirrorCenter_SheenB",
        (0.022, 0.004, 0.96),
        (-0.27, my - 0.062, 2.40),
        mats["mirror_sheen"],
        alcove_col,
        rot=(0.0, math.radians(45.0), 0.0),
        bevel=0.0,
    )

    # Real EEVEE Reflection Plane Light Probe aligned precisely to MirrorCenter_Glass
    probe_data = bpy.data.lightprobes.new("MirrorCenter_ProbeData", type="PLANE")
    if hasattr(probe_data, "influence_distance"):
        probe_data.influence_distance = 6.0
    if hasattr(probe_data, "falloff"):
        probe_data.falloff = 0.05
    if hasattr(probe_data, "clip_start"):
        probe_data.clip_start = 0.02
    probe_obj = bpy.data.objects.new("MirrorCenter_ReflectionProbe", probe_data)
    probe_obj.location = (0.0, my - 0.08, mz)
    probe_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    probe_obj.scale = (mw * 0.65, mh * 0.65, 1.0)
    link_obj_exclusive(probe_obj, mirrors_col)

    # ZERO-RAYTRACING OPTICAL MIRRORED ALCOVE strictly behind BackWall rear face (wall_y + 0.30 = 4.90m)!
    # All walls/ceiling start at Y = 4.96m (> 4.90m) so NOTHING can ever poke through BackWall_Upper!
    _box("MirrorAlcove_Floor", (6.2, 4.84, 0.14), (0.0, 7.18, -0.07), mats["floor_marble"], alcove_col, bevel=0.0)
    _box("MirrorAlcove_CarpetGold", (3.12, 4.60, 0.016), (0.0, 7.26, 0.008), mats["carpet_gold"], alcove_col, bevel=0.0)
    _box("MirrorAlcove_CarpetRed", (2.82, 4.60, 0.022), (0.0, 7.26, 0.011), mats["carpet_red"], alcove_col, bevel=0.0)
    # Mirrored Lobby Rear Wall (rich deep emerald wainscoting + champagne upper plaster + brass cornice!)
    _box("MirrorAlcove_BackLow", (6.4, 0.20, 3.45), (0.0, 9.55, 1.725), mats["emerald_wall"], alcove_col, bevel=0.0)
    _box("MirrorAlcove_BackUpper", (6.4, 0.20, 2.85), (0.0, 9.55, 4.82), mats["warm_plaster"], alcove_col, bevel=0.0)
    _box("MirrorAlcove_Cornice", (6.2, 0.18, 0.14), (0.0, 9.42, 3.45), mats["brass"], alcove_col, bevel=0.0)
    _box("MirrorAlcove_Baseboard", (6.2, 0.14, 0.24), (0.0, 9.42, 0.12), mats["dark_bronze"], alcove_col, bevel=0.0)
    # Side walls & ceiling strictly behind Y = 4.96m and outside elevator shafts (X = +/-3.15m)
    _box("MirrorAlcove_LeftWall", (0.20, 4.64, 6.20), (-3.15, 7.28, 3.10), mats["emerald_wall"], alcove_col, bevel=0.0)
    _box("MirrorAlcove_RightWall", (0.20, 4.64, 6.20), (3.15, 7.28, 3.10), mats["emerald_wall"], alcove_col, bevel=0.0)
    _box("MirrorAlcove_Ceiling", (6.5, 4.64, 0.20), (0.0, 7.28, 6.10), mats["warm_plaster"], alcove_col, bevel=0.0)
    # Mirrored Art Deco lobby arch doorway tucked to the left (leaves dark emerald right behind Pak Doni for high contrast!)
    _box("MirrorAlcove_ArchRecess", (1.35, 0.12, 2.55), (-1.15, 9.42, 1.32), mats["warm_plaster"], alcove_col, bevel=0.0)
    _box("MirrorAlcove_ArchFrameL", (0.14, 0.20, 2.68), (-1.86, 9.38, 1.36), mats["brass"], alcove_col, bevel=0.008)
    _box("MirrorAlcove_ArchFrameR", (0.14, 0.20, 2.68), (-0.44, 9.38, 1.36), mats["brass"], alcove_col, bevel=0.008)
    _box("MirrorAlcove_ArchTop", (1.56, 0.20, 0.16), (-1.15, 9.38, 2.68), mats["brass"], alcove_col, bevel=0.008)
    # Mirrored Art Deco brass pilaster on right background for architectural depth
    _box("MirrorAlcove_PilasterR", (0.18, 0.16, 4.2), (1.05, 9.40, 2.1), mats["brass"], alcove_col, bevel=0.008)
    # Subtle golden dust motes continuing inside the mirror reflection!
    for m_i, (mx, my_d, mz_d, mr) in enumerate((
        (-0.28, 6.45, 2.38, 0.018),
        (0.32, 7.10, 2.15, 0.015),
        (-0.08, 7.80, 2.58, 0.020),
        (0.45, 6.20, 1.72, 0.014),
    )):
        d_mesh = bpy.data.meshes.new(f"MirrorDust_{m_i}_Mesh")
        d_bm = bmesh.new()
        bmesh.ops.create_icosphere(d_bm, subdivisions=1, radius=mr)
        d_bm.to_mesh(d_mesh)
        d_bm.free()
        d_obj = bpy.data.objects.new(f"MirrorAlcove_Dust_{m_i}", d_mesh)
        d_obj.location = (mx, my_d, mz_d)
        _assign_mat(d_obj, mats["dust_mote"])
        link_obj_exclusive(d_obj, alcove_col)

    # Balanced warm golden key light IN FRONT of the mirrored character (Y = 5.05m) so reflections look rich & sunlit!
    ldata = bpy.data.lights.new("MirrorAlcove_LightData", type="POINT")
    ldata.energy = 68.0
    ldata.color = (1.0, 0.84, 0.56)
    ldata.shadow_soft_size = 0.45
    if hasattr(ldata, "use_shadow"):
        ldata.use_shadow = False
    lobj = bpy.data.objects.new("MirrorAlcove_Light", ldata)
    lobj.location = (-0.15, 5.05, 2.25)
    link_obj_exclusive(lobj, alcove_col)

    # 2. SIDE WALL GRAND MIRROR (on left wall between arched window & elevator corner, X = -4.78, Y = 2.55)
    smw, smh = 1.65, 2.25
    smz = 1.85
    smy = 2.55
    smx = -4.76
    _box("MirrorSide_FrameOuter", (0.12, smw + 0.22, smh + 0.22), (smx - 0.02, smy, smz), mats["dark_bronze"], mirrors_col, bevel=0.012)
    _box("MirrorSide_FrameGold", (0.15, smw + 0.14, smh + 0.14), (smx, smy, smz), mats["brass"], mirrors_col, bevel=0.012)
    _box("MirrorSide_Crown", (0.16, 0.90, 0.22), (smx, smy, smz + smh * 0.5 + 0.16), mats["brass"], mirrors_col, bevel=0.010)
    _box("MirrorSide_Glass", (0.02, smw, smh), (smx + 0.065, smy, smz), mats["mirror_glass"], mirrors_col, bevel=0.0)

    return {
        "mirror_center": mirror_plane,
        "mirror_sheen_a": sheen_a,
        "mirror_sheen_b": sheen_b,
        "mirror_probe": probe_obj,
        "mirror_plane_y": my - 0.055,
    }


def _build_sconce(
    name: str,
    loc: Tuple[float, float, float],
    rot_z: float,
    mats: Dict[str, bpy.types.Material],
    col: bpy.types.Collection,
) -> bpy.types.Object:
    """Build an Art Deco vertical brass & glowing frosted-glass wall sconce."""
    parent = _box(f"{name}_Backplate", (0.24, 0.06, 0.68), loc, mats["brass"], col, rot=(0.0, 0.0, rot_z), bevel=0.008)
    # Frosted glass glowing tube
    glass = _cyl(f"{name}_Glass", 0.075, 0.54, (0.0, -0.09, 0.02), mats["sconce_glass"], col, verts=20)
    glass.parent = parent
    # Tiered brass Art Deco cage rings
    for k, z_ring in enumerate((-0.24, -0.06, 0.12, 0.28)):
        ring = _cyl(f"{name}_Ring_{k}", 0.092, 0.032, (0.0, -0.09, z_ring), mats["brass"], col, verts=20)
        ring.parent = parent
    # Tapered brass bottom finial
    fin = _cone(f"{name}_Finial", 0.01, 0.085, 0.14, (0.0, -0.09, -0.32), mats["brass"], col)
    fin.parent = parent
    return parent


def _build_chandelier(
    loc: Tuple[float, float, float],
    mats: Dict[str, bpy.types.Material],
    col: bpy.types.Collection,
) -> None:
    """Grand tiered Art Deco brass & frosted-glass chandelier hanging from the coffered ceiling."""
    cx, cy, cz = loc
    # Ceiling stem & medallion
    _cyl("Chandelier_Medallion", 0.55, 0.08, (cx, cy, 6.14), mats["brass"], col, verts=32)
    _cyl("Chandelier_Stem", 0.05, 1.35, (cx, cy, 5.48), mats["brass"], col, verts=16)

    # 3 concentric stepped glowing tiers!
    tiers = [
        (0.92, 0.30, cz + 0.18, 12),
        (0.64, 0.34, cz - 0.14, 9),
        (0.36, 0.36, cz - 0.46, 6),
    ]
    for t_i, (rad, h, tz, num_fins) in enumerate(tiers):
        _cyl(f"Chandelier_Glass_{t_i}", rad * 0.94, h, (cx, cy, tz), mats["sconce_glass"], col, verts=32)
        _cyl(f"Chandelier_RingTop_{t_i}", rad, 0.045, (cx, cy, tz + h * 0.46), mats["brass"], col, verts=32)
        _cyl(f"Chandelier_RingBot_{t_i}", rad, 0.045, (cx, cy, tz - h * 0.46), mats["brass"], col, verts=32)
        for f in range(num_fins):
            ang = (2.0 * math.pi * f) / num_fins
            fx = cx + math.cos(ang) * (rad + 0.01)
            fy = cy + math.sin(ang) * (rad + 0.01)
            _box(f"Chandelier_Fin_{t_i}_{f}", (0.03, 0.07, h + 0.06), (fx, fy, tz), mats["brass"], col, rot=(0, 0, ang), bevel=0.004)
    # Bottom brass spike finial
    _cone("Chandelier_Tip", 0.01, 0.22, 0.32, (cx, cy, cz - 0.78), mats["brass"], col)


def _build_potted_palm(
    name: str,
    loc: Tuple[float, float, float],
    mats: Dict[str, bpy.types.Material],
    col: bpy.types.Collection,
) -> None:
    """Stylized Art Deco brass urn planter with lush sculpted palm fronds (great foreground parallax!)."""
    px, py, pz = loc
    _cone(f"{name}_Base", 0.28, 0.20, 0.12, (px, py, pz + 0.06), mats["dark_bronze"], col)
    _cone(f"{name}_Urn", 0.22, 0.34, 0.56, (px, py, pz + 0.40), mats["brass"], col)
    _cyl(f"{name}_Rim", 0.36, 0.06, (px, py, pz + 0.69), mats["dark_bronze"], col)
    _cyl(f"{name}_Soil", 0.31, 0.04, (px, py, pz + 0.67), mats["walnut"], col)

    # 9 sculpted stylized arching leaves radiating naturally
    for i in range(9):
        ang = (2.0 * math.pi * i) / 9.0 + (0.2 if i % 2 else 0.0)
        tilt = math.radians(34.0 + (i % 3) * 14.0)
        length = 0.72 + (i % 2) * 0.18
        lx = px + math.cos(ang) * (0.24 + (i % 3) * 0.06)
        ly = py + math.sin(ang) * (0.24 + (i % 3) * 0.06)
        lz = pz + 0.92 + (i % 2) * 0.14
        _box(
            f"{name}_Leaf_{i}",
            (0.22, 0.022, length),
            (lx, ly, lz),
            mats["foliage"],
            col,
            rot=(tilt, 0.0, ang - math.pi * 0.5),
            bevel=0.008,
        )


def _build_concierge_desk(
    loc: Tuple[float, float, float],
    mats: Dict[str, bpy.types.Material],
    col: bpy.types.Collection,
) -> None:
    """Art Deco walnut concierge desk with brass speed stripes, banker's lamp & overflowing red complaints!"""
    dx, dy, dz = loc
    # Main walnut cabinet facing -X (into lobby center)
    _box("Desk_Body", (0.92, 2.35, 1.04), (dx, dy, dz + 0.52), mats["walnut"], col, bevel=0.025)
    _box("Desk_Counter", (1.06, 2.48, 0.08), (dx - 0.04, dy, dz + 1.08), mats["brass"], col, bevel=0.015)
    # 3 iconic horizontal Art Deco brass speed-lines along front face
    for k, z_s in enumerate((0.28, 0.54, 0.80)):
        _box(f"Desk_Stripe_{k}", (0.04, 2.26, 0.055), (dx - 0.46, dy, dz + z_s), mats["brass"], col, bevel=0.006)
    # Emerald Banker's Lamp!
    _cyl("BankerLamp_Base", 0.11, 0.04, (dx - 0.12, dy + 0.62, dz + 1.14), mats["brass"], col)
    _cyl("BankerLamp_Stem", 0.02, 0.30, (dx - 0.12, dy + 0.62, dz + 1.30), mats["brass"], col)
    _box("BankerLamp_Shade", (0.18, 0.28, 0.12), (dx - 0.12, dy + 0.62, dz + 1.46), mats["banker_green"], col, rot=(0, math.radians(15), 0), bevel=0.018)
    # Brass concierge call bell
    _cyl("Desk_BellBase", 0.07, 0.02, (dx - 0.28, dy - 0.18, dz + 1.13), mats["dark_bronze"], col)
    _cone("Desk_BellDome", 0.062, 0.02, 0.055, (dx - 0.28, dy - 0.18, dz + 1.165), mats["brass"], col)

    # Overflowing towering stack of RED COMPLAINT PAPERS on the desk (storytelling detail!)
    rng = random.Random(42)
    for stack_i, (sy, count) in enumerate(((-0.62, 16), (-0.28, 10))):
        for p in range(count):
            pmat = mats["paper_red"] if p % 3 == 0 else mats["paper_cream"]
            _box(
                f"Desk_Complaint_{stack_i}_{p}",
                (0.24, 0.30, 0.014),
                (dx - 0.12 + rng.uniform(-0.02, 0.02), dy + sy + rng.uniform(-0.02, 0.02), dz + 1.13 + p * 0.017),
                pmat,
                col,
                rot=(0.0, 0.0, rng.uniform(-0.22, 0.22)),
                bevel=0.002,
            )


def _build_rocket_cart(
    loc: Tuple[float, float, float],
    mats: Dict[str, bpy.types.Material],
    rocket_col: bpy.types.Collection,
) -> None:
    """Visual Comedy 3D Prop: Clara's absurdly over-engineered 'Turbo Rocket Lift Booster' on a rolling cart!"""
    rx, ry, rz = loc
    # Rolling wooden workshop cart with 4 steel caster wheels
    _box("RocketCart_Deck", (0.86, 1.15, 0.07), (rx, ry, rz + 0.20), mats["walnut"], rocket_col, bevel=0.01)
    for wx in (-0.32, 0.32):
        for wy in (-0.42, 0.42):
            _cyl(f"RocketCart_Wheel_{wx}_{wy}", 0.09, 0.06, (rx + wx, ry + wy, rz + 0.09), mats["dark_bronze"], rocket_col, rot=(0, math.radians(90), 0))
    # Cart push handle
    _cyl("RocketCart_HandleL", 0.02, 0.72, (rx - 0.36, ry + 0.52, rz + 0.56), mats["steel"], rocket_col)
    _cyl("RocketCart_HandleR", 0.02, 0.72, (rx + 0.36, ry + 0.52, rz + 0.56), mats["steel"], rocket_col)
    _cyl("RocketCart_HandleBar", 0.022, 0.76, (rx, ry + 0.52, rz + 0.90), mats["crimson_lacquer"], rocket_col, rot=(0, math.radians(90), 0))

    # Brushed-steel retro-futuristic Rocket Thruster lying diagonally on wooden cradle!
    parent = _cyl(
        "TurboRocket_Body",
        radius=0.22,
        depth=1.05,
        loc=(rx, ry - 0.04, rz + 0.52),
        mat=mats["steel"],
        col=rocket_col,
        rot=(math.radians(74.0), 0.0, math.radians(-18.0)),
        verts=28,
    )
    nose = _cone("TurboRocket_Nose", 0.22, 0.01, 0.42, (0.0, 0.0, 0.73), mats["crimson_lacquer"], rocket_col)
    nose.parent = parent
    nozzle = _cone("TurboRocket_Nozzle", 0.14, 0.23, 0.26, (0.0, 0.0, -0.64), mats["dark_bronze"], rocket_col)
    nozzle.parent = parent
    band = _cyl("TurboRocket_BrassBand", 0.232, 0.09, (0.0, 0.0, 0.22), mats["brass"], rocket_col)
    band.parent = parent
    for f_i in range(4):
        ang = f_i * math.pi * 0.5
        fin = _box(
            f"TurboRocket_Fin_{f_i}",
            (0.03, 0.22, 0.32),
            (math.cos(ang) * 0.24, math.sin(ang) * 0.24, -0.34),
            mats["crimson_lacquer"],
            rocket_col,
            rot=(0.0, 0.0, ang + math.pi * 0.5),
            bevel=0.004,
        )
        fin.parent = parent


def _build_stanchions(mats: Dict[str, bpy.types.Material], col: bpy.types.Collection) -> None:
    """Brass Art Deco stanchion posts + burgundy velvet ropes framing the lobby carpet for parallax."""
    for side_tag, sx in (("L", -2.35), ("R", 2.35)):
        ys = (-1.6, 0.4)
        for i, sy in enumerate(ys):
            _cyl(f"Stanchion_{side_tag}_{i}_Base", 0.17, 0.05, (sx, sy, 0.025), mats["brass"], col)
            _cyl(f"Stanchion_{side_tag}_{i}_Pole", 0.026, 0.88, (sx, sy, 0.48), mats["brass"], col)
            _cyl(f"Stanchion_{side_tag}_{i}_Ball", 0.052, 0.09, (sx, sy, 0.94), mats["brass"], col)
        # Sagging crimson velvet rope curve between the two stanchions
        curve_data = bpy.data.curves.new(f"VelvetRope_{side_tag}", type="CURVE")
        curve_data.dimensions = "3D"
        curve_data.bevel_depth = 0.024
        curve_data.bevel_resolution = 4
        spline = curve_data.splines.new("BEZIER")
        spline.bezier_points.add(1)
        p0, p1 = spline.bezier_points[0], spline.bezier_points[1]
        p0.co = (sx, ys[0], 0.86)
        p0.handle_right = (sx, ys[0] + 0.65, 0.56)
        p0.handle_left = (sx, ys[0] - 0.2, 0.86)
        p1.co = (sx, ys[1], 0.86)
        p1.handle_left = (sx, ys[1] - 0.65, 0.56)
        p1.handle_right = (sx, ys[1] + 0.2, 0.86)
        rope_obj = bpy.data.objects.new(f"VelvetRope_{side_tag}", curve_data)
        _assign_mat(rope_obj, mats["carpet_red"])
        link_obj_exclusive(rope_obj, col)


def _build_dust_motes(mats: Dict[str, bpy.types.Material], dust_col: bpy.types.Collection) -> None:
    """Floating stylized golden dust motes for the magical golden-hour mirror climax mood."""
    rng = random.Random(108)
    for i in range(42):
        x = rng.uniform(-3.6, 3.6)
        y = rng.uniform(-1.5, 4.1)
        z = rng.uniform(0.5, 4.8)
        r = rng.uniform(0.012, 0.028)
        mesh = bpy.data.meshes.new(f"Dust_{i}_Mesh")
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(f"DustMote_{i}", mesh)
        obj.location = (x, y, z)
        _assign_mat(obj, mats["dust_mote"])
        link_obj_exclusive(obj, dust_col)


def build_art_deco_lobby(mats: Dict[str, bpy.types.Material]) -> Dict[str, object]:
    """Assemble the complete Grand Art Deco Skyscraper Lobby 3D environment."""
    env_col = get_or_create_collection("Env_3D")
    mirrors_col = get_or_create_collection("Env_Mirrors", parent=env_col)
    alcove_col = get_or_create_collection("Env_MirrorAlcove", parent=env_col)
    rocket_col = get_or_create_collection("Env_RocketCart", parent=env_col)
    dust_col = get_or_create_collection("FX_Dust")  # Deliberately outside Env_3D so Freestyle ignores motes!

    wall_y = 4.60
    ceil_z = 6.20

    # 1. FLOOR (Checkered Emerald & Ivory Marble + Crimson Art Deco Runner Carpet!)
    _box("Lobby_Floor", (10.4, 12.6, 0.16), (0.0, -0.5, -0.08), mats["floor_marble"], env_col, bevel=0.0)
    # Plush crimson runner carpet with raised golden Art Deco border trim!
    _box("Lobby_CarpetGold", (3.12, 9.2, 0.016), (0.0, -0.8, 0.008), mats["carpet_gold"], env_col, bevel=0.004)
    _box("Lobby_CarpetRed", (2.82, 8.9, 0.022), (0.0, -0.8, 0.011), mats["carpet_red"], env_col, bevel=0.005)
    # Subtle brass carpet threshold strip near elevators
    _box("Lobby_BrassThreshold", (4.6, 0.14, 0.014), (0.0, 3.85, 0.007), mats["brass"], env_col, bevel=0.003)

    # 2. BACK ELEVATOR WALL (Deep Emerald Lower Wall + Champagne Plaster Upper Wall + Fluted Brass Cornices)
    _box("BackWall_Left", (2.4, 0.30, 3.45), (-3.95, wall_y + 0.15, 1.725), mats["emerald_wall"], env_col, bevel=0.01)
    # Center pier split into 4 perimeter strips + toggleable center plug (opens cleanly for Zero-Raytracing Mirror Portal!)
    _box("BackWall_PierBot", (1.98, 0.30, 0.58), (0.0, wall_y + 0.15, 0.29), mats["emerald_wall"], env_col, bevel=0.008)
    _box("BackWall_PierTop", (1.98, 0.30, 0.72), (0.0, wall_y + 0.15, 3.10), mats["emerald_wall"], env_col, bevel=0.008)
    _box("BackWall_PierL", (0.38, 0.30, 2.22), (-0.80, wall_y + 0.15, 1.66), mats["emerald_wall"], env_col, bevel=0.008)
    _box("BackWall_PierR", (0.38, 0.30, 2.22), (0.80, wall_y + 0.15, 1.66), mats["emerald_wall"], env_col, bevel=0.008)
    center_plug = _box("BackWall_CenterPlug", (1.28, 0.30, 2.24), (0.0, wall_y + 0.15, 1.66), mats["emerald_wall"], env_col, bevel=0.006)
    _box("BackWall_Right", (2.4, 0.30, 3.45), (3.95, wall_y + 0.15, 1.725), mats["emerald_wall"], env_col, bevel=0.01)
    _box("BackWall_Upper", (10.4, 0.30, ceil_z - 3.35), (0.0, wall_y + 0.15, 3.35 + (ceil_z - 3.35) * 0.5), mats["warm_plaster"], env_col, bevel=0.01)

    # Stepped horizontal Art Deco brass cornice band separating emerald wainscoting & cream plaster!
    _box("BackWall_CorniceLow", (10.2, 0.24, 0.14), (0.0, wall_y - 0.04, 3.45), mats["brass"], env_col, bevel=0.01)
    _box("BackWall_CorniceTop", (10.2, 0.28, 0.22), (0.0, wall_y - 0.06, ceil_z - 0.14), mats["brass"], env_col, bevel=0.012)
    _box("BackWall_Baseboard", (10.2, 0.14, 0.24), (0.0, wall_y - 0.02, 0.12), mats["dark_bronze"], env_col, bevel=0.008)

    # Vertical fluted Art Deco brass pilasters flanking the elevators & clock!
    for px in (-4.4, -3.1, -0.78, 0.78, 3.1, 4.4):
        _box(f"BackPilaster_{px}", (0.18, 0.16, ceil_z - 0.3), (px, wall_y - 0.05, ceil_z * 0.5), mats["brass"], env_col, bevel=0.01)
        _box(f"BackPilasterTrim_{px}", (0.26, 0.12, 0.35), (px, wall_y - 0.04, 0.18), mats["dark_bronze"], env_col, bevel=0.008)

    # 3. TWIN ANIMATABLE ART DECO BRASS ELEVATOR BAYS
    elev_l = _build_elevator_bay("ElevL", -1.88, wall_y, mats, env_col)
    elev_r = _build_elevator_bay("ElevR", +1.88, wall_y, mats, env_col)

    # Elevator Call Button Panel mounted on center pier (X=0, Z=1.22m, moved slightly below mirror!)
    _box("CallPanel_Plate", (0.24, 0.05, 0.42), (0.0, wall_y - 0.03, 0.66), mats["brass"], env_col, bevel=0.008)
    _cyl("CallPanel_BtnUp", 0.042, 0.04, (0.0, wall_y - 0.065, 0.74), mats["button_glow"], env_col, (math.radians(90), 0, 0))
    _cyl("CallPanel_BtnDown", 0.042, 0.04, (0.0, wall_y - 0.065, 0.58), mats["button_glow"], env_col, (math.radians(90), 0, 0))
    # Also place a dedicated waist-height call button panel right beside Left Elevator so Pak Doni can furiously mash it!
    _box("CallPanelL_Plate", (0.20, 0.05, 0.38), (-0.82, wall_y - 0.12, 1.24), mats["brass"], env_col, bevel=0.008)
    _cyl("CallPanelL_BtnUp", 0.038, 0.04, (-0.82, wall_y - 0.155, 1.32), mats["button_glow"], env_col, (math.radians(90), 0, 0))
    _cyl("CallPanelL_BtnDown", 0.038, 0.04, (-0.82, wall_y - 0.155, 1.16), mats["button_glow"], env_col, (math.radians(90), 0, 0))

    # 4. HERO PROP #1: GIANT MECHANICAL ART DECO WALL CLOCK
    clock_handles = _build_hero_wall_clock(wall_y, mats, env_col)

    # 5. HERO PROP #2: TOGGLEABLE GRAND ART DECO FRAMED MIRRORS + ZERO-RAYTRACING OPTICAL ALCOVE
    mirror_handles = _build_art_deco_mirrors(wall_y, mats, mirrors_col, alcove_col)
    set_collection_visibility(alcove_col, False)

    # 6. LEFT WALL (X = -4.95) WITH TALL ARCHED ART DECO SKYSCRAPER WINDOWS!
    _box("LeftWall_Low", (0.28, 12.6, 1.15), (-5.05, -0.5, 0.575), mats["emerald_wall"], env_col, bevel=0.01)
    _box("LeftWall_Upper", (0.28, 12.6, 1.35), (-5.05, -0.5, 5.525), mats["warm_plaster"], env_col, bevel=0.01)
    # Wall piers between & around 2 giant sunlit windows (Y = -2.0 and Y = 0.7)
    for py, pw in ((-4.8, 3.6), (-0.65, 0.95), (3.45, 3.3)):
        _box(f"LeftWall_Pier_{py}", (0.28, pw, 3.85), (-5.05, py, 3.05), mats["emerald_wall"], env_col, bevel=0.01)
    # Art Deco Window Mullions + Glowing Sky Glass Backdrop right outside windows
    for w_i, wy in enumerate((-2.0, 0.7)):
        _box(f"Window_{w_i}_Frame", (0.22, 1.85, 3.8), (-4.94, wy, 3.05), mats["dark_bronze"], env_col, bevel=0.008)
        # Cut open interior look by placing glowing sky pane just outside bronze mullions
        _box(f"Window_{w_i}_Sky", (0.04, 1.65, 3.6), (-5.12, wy, 3.05), mats["window_sky"], env_col, bevel=0.0)
        for m_z in (2.0, 3.1, 4.1):
            _box(f"Window_{w_i}_BarH_{m_z}", (0.14, 1.72, 0.06), (-4.94, wy, m_z), mats["brass"], env_col, bevel=0.004)
        _box(f"Window_{w_i}_BarV", (0.14, 0.07, 3.68), (-4.94, wy, 3.05), mats["brass"], env_col, bevel=0.004)
    _box("LeftWall_Cornice", (0.26, 12.2, 0.20), (-4.86, -0.5, ceil_z - 0.14), mats["brass"], env_col, bevel=0.01)

    # 7. RIGHT WALL (X = +4.95) + WALNUT CONCIERGE DESK & OVERFLOWING COMPLAINTS
    _box("RightWall_Low", (0.28, 12.6, 3.45), (5.05, -0.5, 1.725), mats["emerald_wall"], env_col, bevel=0.01)
    _box("RightWall_Upper", (0.28, 12.6, ceil_z - 3.35), (5.05, -0.5, 3.35 + (ceil_z - 3.35) * 0.5), mats["warm_plaster"], env_col, bevel=0.01)
    _box("RightWall_CorniceLow", (0.24, 12.2, 0.14), (4.88, -0.5, 3.45), mats["brass"], env_col, bevel=0.01)
    _box("RightWall_CorniceTop", (0.26, 12.2, 0.20), (4.86, -0.5, ceil_z - 0.14), mats["brass"], env_col, bevel=0.01)

    # Back Entrance Wall behind camera (Y = -6.2) so reflections in mirrors look like a complete Grand Lobby!
    _box("RearWall_Low", (10.4, 0.28, 3.45), (0.0, -6.2, 1.725), mats["emerald_wall"], env_col, bevel=0.01)
    _box("RearWall_Upper", (10.4, 0.28, ceil_z - 3.35), (0.0, -6.2, 3.35 + (ceil_z - 3.35) * 0.5), mats["warm_plaster"], env_col, bevel=0.01)
    # Revolving Art Deco Brass Entrance Arch behind camera (visible in mirror reflections!)
    _box("RearWall_ArchDoor", (3.2, 0.24, 3.1), (0.0, -6.02, 1.55), mats["window_sky"], env_col, bevel=0.0)
    _box("RearWall_ArchFrameL", (0.24, 0.34, 3.3), (-1.65, -5.98, 1.65), mats["brass"], env_col, bevel=0.01)
    _box("RearWall_ArchFrameR", (0.24, 0.34, 3.3), (1.65, -5.98, 1.65), mats["brass"], env_col, bevel=0.01)
    _box("RearWall_ArchLintel", (3.6, 0.34, 0.26), (0.0, -5.98, 3.25), mats["brass"], env_col, bevel=0.01)

    # 8. COFFERED ART DECO CEILING + GRAND CHANDELIER
    _box("Lobby_Ceiling", (10.4, 12.6, 0.20), (0.0, -0.5, ceil_z + 0.10), mats["warm_plaster"], env_col, bevel=0.0)
    for by in (-3.2, -0.8, 1.6, 4.0):
        _box(f"CeilBeam_X_{by}", (10.0, 0.34, 0.28), (0.0, by, ceil_z - 0.14), mats["brass"], env_col, bevel=0.012)
    for bx in (-3.2, 3.2):
        _box(f"CeilBeam_Y_{bx}", (0.34, 11.4, 0.28), (bx, -0.5, ceil_z - 0.14), mats["brass"], env_col, bevel=0.012)
    _build_chandelier((0.0, 0.75, 4.85), mats, env_col)

    # 9. STRUCTURAL FLUTED COLUMNS + WARM ART DECO WALL SCONCES
    for side_tag, sx in (("L", -4.45), ("R", 4.45)):
        for cy in (-2.9, -0.65, 1.85, 4.15):
            _box(f"Col_{side_tag}_{cy}_Plinth", (0.78, 0.78, 0.42), (sx, cy, 0.21), mats["dark_bronze"], env_col, bevel=0.015)
            _box(f"Col_{side_tag}_{cy}_Shaft", (0.62, 0.62, ceil_z - 0.6), (sx, cy, ceil_z * 0.5), mats["emerald_wall"], env_col, bevel=0.018)
            _box(f"Col_{side_tag}_{cy}_Cap", (0.82, 0.82, 0.32), (sx, cy, ceil_z - 0.26), mats["brass"], env_col, bevel=0.015)
            # Vertical brass accent rib on inner face of column
            inner_x = sx + (0.32 if sx < 0 else -0.32)
            _box(f"Col_{side_tag}_{cy}_Rib", (0.06, 0.18, ceil_z - 0.9), (inner_x, cy, ceil_z * 0.5), mats["brass"], env_col, bevel=0.008)
            # Glowing frosted Art Deco sconce on lobby-facing side of columns!
            rot_z = math.radians(-90.0 if sx < 0 else 90.0)
            sconce_x = sx + (0.35 if sx < 0 else -0.35)
            _build_sconce(f"Sconce_{side_tag}_{cy}", (sconce_x, cy, 2.55), rot_z, mats, env_col)

    # Also mount 2 hero sconces flanking the elevators on the Back Wall!
    _build_sconce("Sconce_BackL", (-3.12, wall_y - 0.16, 2.65), 0.0, mats, env_col)
    _build_sconce("Sconce_BackR", (3.12, wall_y - 0.16, 2.65), 0.0, mats, env_col)

    # 10. LOBBY FURNITURE & STORY PROPS
    _build_concierge_desk((4.15, 0.45, 0.0), mats, env_col)
    _build_potted_palm("Palm_BackL", (-3.75, 3.85, 0.0), mats, env_col)
    _build_potted_palm("Palm_BackR", (3.75, 3.85, 0.0), mats, env_col)
    _build_potted_palm("Palm_ForeL", (-3.45, -1.65, 0.0), mats, env_col)
    _build_stanchions(mats, env_col)

    # Visual Gag 3D Prop: Clara's Mini Turbo-Rocket Booster Cart!
    _build_rocket_cart((2.35, 2.45, 0.0), mats, rocket_col)

    # Floating Golden Dust Motes (visible in golden_mirror climax!)
    _build_dust_motes(mats, dust_col)

    return {
        "env_col": env_col,
        "mirrors_col": mirrors_col,
        "alcove_col": alcove_col,
        "center_plug": center_plug,
        "rocket_col": rocket_col,
        "dust_col": dust_col,
        "elev_l": elev_l,
        "elev_r": elev_r,
        **clock_handles,
        **mirror_handles,
    }


def set_collection_visibility(col: bpy.types.Collection, visible: bool) -> None:
    col.hide_render = not visible
    col.hide_viewport = not visible


def set_mirror_portal_mode(env: dict, portal_active: bool) -> None:
    """Switch Center Mirror between Zero-Raytracing Optical Alcove (10x faster CI!) and solid mirror glass."""
    set_collection_visibility(env["alcove_col"], portal_active)
    plug = env["center_plug"]
    plug.hide_render = portal_active
    plug.hide_viewport = portal_active
    glass = env["mirror_center"]
    glass.hide_render = portal_active
    glass.hide_viewport = portal_active
