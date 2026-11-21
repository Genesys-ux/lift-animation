"""Time-of-Day Storytelling Lighting System (morning_busy, midday_stress, golden_mirror).

Calibrated for rich, punchy AgX contrast so deep emerald marble, brushed Art Deco brass,
crimson carpet, and 2.5D character ink colors pop vividly without highlight washout.
"""

from __future__ import annotations

import math
from typing import Dict

import bpy
from mathutils import Euler

from .compat import get_or_create_collection, link_obj_exclusive
from .environment import set_collection_visibility


def _clear_collection(col: bpy.types.Collection) -> None:
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _add_area_light(
    name: str,
    loc: tuple[float, float, float],
    rot_deg: tuple[float, float, float],
    energy: float,
    color: tuple[float, float, float],
    size_x: float,
    size_y: float,
    col: bpy.types.Collection,
    spread_deg: float = 82.0,
) -> bpy.types.Object:
    ldata = bpy.data.lights.new(name=name + "_Data", type="AREA")
    ldata.energy = energy
    ldata.color = color
    ldata.shape = "RECTANGLE"
    ldata.size = size_x
    ldata.size_y = size_y
    if hasattr(ldata, "spread"):
        ldata.spread = math.radians(spread_deg)
    lobj = bpy.data.objects.new(name, ldata)
    lobj.location = loc
    lobj.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
    # Prevent invisible studio area-light boxes from showing up as white rectangles inside mirrors!
    if hasattr(lobj, "visible_glossy"):
        lobj.visible_glossy = False
    if hasattr(lobj, "visible_camera"):
        lobj.visible_camera = False
    link_obj_exclusive(lobj, col)
    return lobj


def _add_point_light(
    name: str,
    loc: tuple[float, float, float],
    energy: float,
    color: tuple[float, float, float],
    radius: float,
    col: bpy.types.Collection,
) -> bpy.types.Object:
    ldata = bpy.data.lights.new(name=name + "_Data", type="POINT")
    ldata.energy = energy
    ldata.color = color
    ldata.shadow_soft_size = radius
    lobj = bpy.data.objects.new(name, ldata)
    lobj.location = loc
    link_obj_exclusive(lobj, col)
    return lobj


def _set_material_emission(mat: bpy.types.Material, color: tuple[float, float, float, float], strength: float) -> None:
    if not mat or not mat.use_nodes:
        return
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            if "Emission Color" in node.inputs:
                node.inputs["Emission Color"].default_value = color
            if "Emission Strength" in node.inputs:
                node.inputs["Emission Strength"].default_value = strength


def _set_world_ambient(color: tuple[float, float, float], strength: float) -> None:
    world = bpy.context.scene.world
    world.use_nodes = True
    nt = world.node_tree
    bg = None
    for n in nt.nodes:
        if n.type == "BACKGROUND":
            bg = n
            break
    if bg is None:
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputWorld")
        bg = nt.nodes.new("ShaderNodeBackground")
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Color"].default_value = (*color, 1.0)
    bg.inputs["Strength"].default_value = strength


def apply_lighting_mood(
    mood: str,
    mats: Dict[str, bpy.types.Material],
    dust_col: bpy.types.Collection | None = None,
) -> None:
    """Switch the 3D lobby lighting, practical fixtures, window sky, and world ambient to a story mood."""
    light_col = get_or_create_collection("Lighting_Rig")
    _clear_collection(light_col)

    m = mood.lower().strip()
    scene = bpy.context.scene

    if m == "morning_busy":
        # Crisp bright morning sun shafts from tall left windows + cool sky shadows + warm brass gleam!
        _set_world_ambient((0.36, 0.50, 0.74), 0.10)
        scene.view_settings.exposure = -0.22

        # Directional warm morning window key shafts (casts bold grounded shadows across marble floor!)
        _add_area_light("Key_MorningWindow1", (-4.3, 0.7, 3.6), (52, 0, -68), 380.0, (1.0, 0.88, 0.68), 1.4, 2.8, light_col, 62.0)
        _add_area_light("Key_MorningWindow2", (-4.3, -1.9, 3.6), (54, 0, -62), 260.0, (1.0, 0.90, 0.74), 1.4, 2.6, light_col, 68.0)

        # Grand Chandelier warm ceiling pool
        _add_point_light("Practical_Chandelier", (0.0, 0.75, 4.10), 175.0, (1.0, 0.84, 0.56), 0.45, light_col)

        # Soft cool sky bounce fill from lobby entrance for clean depth separation
        _add_area_light("Fill_CoolEntrance", (0.6, -4.6, 2.9), (78, 0, 8), 95.0, (0.62, 0.80, 1.0), 3.8, 2.4, light_col, 110.0)

        # Architectural wash grazing Hero Clock & Brass Elevator Doors
        _add_area_light("Accent_ClockWash", (0.0, 2.1, 5.1), (42, 0, 0), 105.0, (1.0, 0.90, 0.72), 3.2, 1.0, light_col, 78.0)

        # Warm practical sconce pools flanking elevators
        _add_point_light("SconceGlow_L", (-3.05, 4.05, 2.65), 38.0, (1.0, 0.78, 0.42), 0.22, light_col)
        _add_point_light("SconceGlow_R", (3.05, 4.05, 2.65), 38.0, (1.0, 0.78, 0.42), 0.22, light_col)

        _set_material_emission(mats["sconce_glass"], (1.0, 0.84, 0.48, 1.0), 3.6)
        _set_material_emission(mats["window_sky"], (0.86, 0.94, 1.0, 1.0), 2.4)
        _set_material_emission(mats["clock_face"], (1.0, 0.94, 0.80, 1.0), 0.24)
        if dust_col:
            set_collection_visibility(dust_col, False)

    elif m == "midday_stress":
        # High-contrast tense crimson-amber heat vs deep slate-indigo shadows while complaints skyrocket!
        _set_world_ambient((0.12, 0.14, 0.28), 0.08)
        scene.view_settings.exposure = -0.25

        # Intense dramatic overhead spotlighting on waiting zone
        _add_area_light("Key_StressOverhead", (-0.4, 2.0, 5.1), (18, 0, -10), 310.0, (1.0, 0.66, 0.36), 2.0, 2.0, light_col, 55.0)
        # Hot orange-amber slash from left window
        _add_area_light("Key_StressWindow", (-4.3, 1.2, 3.2), (56, 0, -76), 270.0, (1.0, 0.44, 0.18), 1.4, 2.6, light_col, 58.0)
        # Dramatic crimson stress rim glowing near elevator call panel & floor dial!
        _add_point_light("Rim_StressElevatorL", (-1.15, 3.85, 2.05), 85.0, (1.0, 0.16, 0.08), 0.28, light_col)
        _add_point_light("Rim_StressElevatorR", (1.65, 3.85, 2.25), 55.0, (1.0, 0.32, 0.14), 0.28, light_col)
        # Cool indigo counter-fill for rich teal-vs-crimson contrast
        _add_area_light("Fill_StressIndigo", (2.4, -2.5, 2.4), (72, 0, 32), 85.0, (0.30, 0.46, 0.98), 3.2, 2.2, light_col, 105.0)
        _add_point_light("Practical_Chandelier", (0.0, 0.75, 4.10), 95.0, (1.0, 0.56, 0.24), 0.45, light_col)

        _set_material_emission(mats["sconce_glass"], (1.0, 0.44, 0.14, 1.0), 4.6)
        _set_material_emission(mats["window_sky"], (1.0, 0.56, 0.26, 1.0), 2.2)
        _set_material_emission(mats["clock_face"], (1.0, 0.74, 0.44, 1.0), 0.35)
        if dust_col:
            set_collection_visibility(dust_col, False)

    else:  # golden_mirror — Lush Golden-Hour Sunset vs Twilight Violet-Blue Magic + Glowing Mirror!
        _set_world_ambient((0.12, 0.16, 0.44), 0.14)
        scene.view_settings.exposure = -0.15

        # Rich low-angle golden sunset shaft slashing dramatically across the lobby!
        _add_area_light("Key_SunsetWindow1", (-4.3, 0.9, 2.9), (66, 0, -68), 480.0, (1.0, 0.54, 0.18), 1.5, 2.8, light_col, 52.0)
        _add_area_light("Key_SunsetWindow2", (-4.3, -1.8, 2.7), (68, 0, -62), 260.0, (1.0, 0.48, 0.16), 1.4, 2.6, light_col, 60.0)

        # Warm glowing Art Deco chandelier & practical wall sconces (reflected magically in mirror!)
        _add_point_light("Practical_Chandelier", (0.0, 0.75, 4.10), 220.0, (1.0, 0.74, 0.36), 0.50, light_col)
        _add_point_light("SconceGlow_BackL", (-3.05, 4.05, 2.65), 65.0, (1.0, 0.70, 0.28), 0.24, light_col)
        _add_point_light("SconceGlow_BackR", (3.05, 4.05, 2.65), 65.0, (1.0, 0.70, 0.28), 0.24, light_col)

        # Dedicated soft golden hero light right above the Center Art Deco Mirror illuminating Pak Doni's reflection!
        _add_area_light("Accent_MirrorHero", (0.0, 3.45, 3.05), (42, 0, 0), 110.0, (1.0, 0.84, 0.52), 1.2, 0.6, light_col, 72.0)

        # Deep twilight violet-blue cool fill from rear lobby for gorgeous warm-vs-cool complementary lighting!
        _add_area_light("Fill_TwilightBlue", (2.0, -4.4, 3.0), (76, 0, 20), 125.0, (0.34, 0.42, 0.98), 3.8, 2.6, light_col, 110.0)

        _set_material_emission(mats["sconce_glass"], (1.0, 0.76, 0.32, 1.0), 5.6)
        _set_material_emission(mats["window_sky"], (1.0, 0.48, 0.18, 1.0), 2.8)
        _set_material_emission(mats["clock_face"], (1.0, 0.84, 0.54, 1.0), 0.38)
        if dust_col:
            set_collection_visibility(dust_col, True)
