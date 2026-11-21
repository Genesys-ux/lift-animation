"""Gate 3 Preview Renderer: Renders 4 high-resolution 9:16 (1080x1920) Blender EEVEE screenshots.

Usage (inside Blender headless CLI):
    blender -b --python scripts/render_preview.py
    blender -b --python scripts/render_preview.py -- --samples 32 --scale 1.0
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Tuple

import bpy
from mathutils import Vector

# Ensure repo root is importable inside Blender's bundled Python
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.blender.characters_3d import clear_characters, load_character_manifest, spawn_character_card  # noqa: E402
from scripts.blender.compat import (  # noqa: E402
    clear_scene,
    configure_eevee_render,
    configure_freestyle_for_collection,
    get_or_create_collection,
    link_obj_exclusive,
)
from scripts.blender.environment import build_art_deco_lobby, set_collection_visibility  # noqa: E402
from scripts.blender.lighting import apply_lighting_mood  # noqa: E402
from scripts.blender.materials import build_material_library  # noqa: E402


def _parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description="Render Gate 3 9:16 Blender Environment Preview Shots")
    parser.add_argument("--width", type=int, default=1080, help="Render width (default 1080)")
    parser.add_argument("--height", type=int, default=1920, help="Render height (default 1920)")
    parser.add_argument("--samples", type=int, default=32, help="Render samples")
    parser.add_argument("--engine", type=str, default="eevee", choices=["eevee", "cycles"], help="Render engine")
    parser.add_argument("--shots", type=str, default="1,2,3,4", help="Comma-separated shot numbers to render")
    parser.add_argument("--output-dir", type=str, default=str(REPO_ROOT / "previews"), help="Output directory")
    return parser.parse_args(argv)


def _setup_camera(
    name: str,
    loc: Tuple[float, float, float],
    target: Tuple[float, float, float],
    lens_mm: float = 28.0,
    dof_fstop: float | None = None,
) -> bpy.types.Object:
    cam_col = get_or_create_collection("Cameras")
    if name in bpy.data.objects:
        cam_obj = bpy.data.objects[name]
    else:
        cam_data = bpy.data.cameras.new(name + "_Data")
        cam_obj = bpy.data.objects.new(name, cam_data)
        link_obj_exclusive(cam_obj, cam_col)

    cam_obj.location = Vector(loc)
    direction = Vector(target) - Vector(loc)
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    cam = cam_obj.data
    cam.lens = lens_mm
    cam.sensor_fit = "VERTICAL"
    cam.sensor_height = 36.0
    cam.clip_start = 0.08
    cam.clip_end = 120.0

    if dof_fstop is not None:
        cam.dof.use_dof = True
        cam.dof.focus_distance = direction.length
        cam.dof.aperture_fstop = dof_fstop
    else:
        cam.dof.use_dof = False

    bpy.context.scene.camera = cam_obj
    return cam_obj


def render_shot(scene: bpy.types.Scene, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"[Gate 3] Saved {out_path}")


def main() -> None:
    args = _parse_args()
    selected_shots = {int(s.strip()) for s in args.shots.split(",") if s.strip()}
    out_dir = Path(args.output_dir)

    print("[Gate 3] Building Grand Art Deco Skyscraper Lobby in Blender EEVEE...")
    clear_scene()
    scene = bpy.context.scene

    configure_eevee_render(
        scene,
        width=args.width,
        height=args.height,
        samples=args.samples,
        use_freestyle=True,
        line_thickness=1.35,
        engine=args.engine,
    )

    mats = build_material_library()
    env = build_art_deco_lobby(mats)
    configure_freestyle_for_collection(
        scene,
        env_collection=env["env_col"],
        ink_color=(0.04, 0.03, 0.06),
        thickness=1.35,
        crease_angle_deg=132.0,
    )
    manifest = load_character_manifest()

    # =========================================================================
    # SHOT 1: Wide Establishing Shot (Morning Busy, Mirrors OFF, Full Scale)
    # =========================================================================
    if 1 in selected_shots:
        print("[Gate 3] Rendering Shot 1: Wide Establishing Shot (Morning Busy)...")
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], True)
        apply_lighting_mood("morning_busy", mats, env["dust_col"])

        # Set Giant Clock & Floor Dials to crisp morning waiting posture
        env["clock_hour"].rotation_euler = (0.0, math.radians(60.0), 0.0)
        env["clock_min"].rotation_euler = (0.0, math.radians(-52.0), 0.0)
        env["clock_sec"].rotation_euler = (0.0, math.radians(-140.0), 0.0)

        clear_characters()
        # 4 completely unobstructed horizontal sightline lanes — all holding true 3D Art Deco props!
        spawn_character_card("Doni_S1", manifest, "doni", (-1.88, 3.25, 0.0), rot_z_deg=-8.0, angle="three_quarter", mats=mats)
        spawn_character_card("Raka_S1", manifest, "raka", (-0.72, 0.95, 0.0), rot_z_deg=14.0, angle="three_quarter", mats=mats)
        spawn_character_card("Bima_S1", manifest, "bima", (0.42, 2.38, 0.0), rot_z_deg=-4.0, expression="panic", mats=mats)
        spawn_character_card("Clara_S1", manifest, "clara", (1.68, 2.68, 0.0), rot_z_deg=-16.0, expression="excited", mats=mats)

        _setup_camera("Cam_Shot1", loc=(0.0, -4.95, 1.82), target=(0.0, 4.40, 2.48), lens_mm=24.0, dof_fstop=None)
        render_shot(scene, out_dir / "env_shot_1.png")

    # =========================================================================
    # SHOT 2: Medium Shot — 2.5D Character Interaction, 3D Art Deco Props & Stress Mood
    # =========================================================================
    if 2 in selected_shots:
        print("[Gate 3] Rendering Shot 2: Medium Character & 3D Prop Interaction (Midday Stress)...")
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], True)
        apply_lighting_mood("midday_stress", mats, env["dust_col"])

        clear_characters()
        spawn_character_card("Doni_S2", manifest, "doni", (-1.18, 3.45, 0.0), rot_z_deg=-10.0, angle="three_quarter", mats=mats)
        spawn_character_card("Bima_S2", manifest, "bima", (-0.02, 2.85, 0.0), rot_z_deg=-10.0, expression="stressed", mats=mats)
        spawn_character_card("Clara_S2", manifest, "clara", (1.16, 2.58, 0.0), rot_z_deg=-20.0, expression="determined", mats=mats)

        _setup_camera("Cam_Shot2", loc=(-0.85, -1.45, 1.28), target=(0.24, 3.10, 1.44), lens_mm=26.0, dof_fstop=4.8)
        render_shot(scene, out_dir / "env_shot_2.png")

    # =========================================================================
    # SHOT 3: Close-up Detail — Giant Mechanical Clock, Brass Doors & Raka + 3D Art Deco Mirror/Coffee!
    # =========================================================================
    if 3 in selected_shots:
        print("[Gate 3] Rendering Shot 3: Close-up Detail & 3D Art Deco Handheld Props...")
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("morning_busy", mats, env["dust_col"])

        env["clock_sec"].rotation_euler = (0.0, math.radians(-22.0), 0.0)
        clear_characters()
        spawn_character_card("Raka_S3", manifest, "raka", (0.36, 2.18, 0.0), rot_z_deg=-12.0, expression="aha", mats=mats)

        _setup_camera("Cam_Shot3", loc=(0.82, -0.55, 1.48), target=(-0.05, 4.45, 2.75), lens_mm=34.0, dof_fstop=4.2)
        render_shot(scene, out_dir / "env_shot_3.png")

    # =========================================================================
    # SHOT 4: Alternate Mood / Golden-Hour Mirror Climax (Live 3D Mirror + 3D Gold Comb & Briefcase!)
    # =========================================================================
    if 4 in selected_shots:
        print("[Gate 3] Rendering Shot 4: Golden-Hour Climax & Installed Art Deco Mirror...")
        set_collection_visibility(env["mirrors_col"], True)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("golden_mirror", mats, env["dust_col"])

        # Clock speeds forward effortlessly while Pak Doni admires himself!
        env["clock_hour"].rotation_euler = (0.0, math.radians(145.0), 0.0)
        env["clock_min"].rotation_euler = (0.0, math.radians(-115.0), 0.0)
        env["clock_sec"].rotation_euler = (0.0, math.radians(42.0), 0.0)

        clear_characters()
        # Smart Double-Sided Card + REAL 3D Art Deco Comb, Watch & Briefcase (reflected live in the 3D Mirror!)
        spawn_character_card(
            "Doni_MirrorHero",
            manifest,
            "doni",
            (0.14, 3.25, 0.0),
            rot_z_deg=12.0,
            angle="back_three_quarter",
            back_expression="narcissistic",
            flip_x=True,
            emission_boost=0.14,
            mats=mats,
        )
        # Framed cleanly so Pak Bima (left) and Raka (right) are BOTH nicely visible beside Pak Doni!
        spawn_character_card("Raka_S4", manifest, "raka", (1.28, 2.85, 0.0), rot_z_deg=-22.0, expression="smug", mats=mats)
        spawn_character_card("Bima_S4", manifest, "bima", (-1.18, 2.75, 0.0), rot_z_deg=16.0, expression="relieved", mats=mats)

        _setup_camera("Cam_Shot4", loc=(-1.12, -0.78, 1.44), target=(0.06, 4.35, 1.66), lens_mm=24.5, dof_fstop=5.0)
        render_shot(scene, out_dir / "env_shot_4.png")

    print("[Gate 3] All requested preview shots rendered successfully!")


if __name__ == "__main__":
    main()
