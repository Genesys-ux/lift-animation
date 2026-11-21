"""Stage 4 Final Production Renderer — Renders animated 30 FPS 9:16 scenes in Blender headless CLI.

Supports parallel per-scene execution for GitHub Actions matrix sharding:
    blender -b --python-exit-code 1 --python scripts/render_final.py -- --scene 1 --engine eevee --samples 16 --encode-clip
    blender -b --python-exit-code 1 --python scripts/render_final.py -- --scene all --keyframe-only
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import bpy

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.blender.characters_3d import load_character_manifest  # noqa: E402
from scripts.blender.compat import (  # noqa: E402
    clear_scene,
    configure_eevee_render,
    configure_freestyle_for_collection,
)
from scripts.blender.environment import build_art_deco_lobby  # noqa: E402
from scripts.blender.materials import build_material_library  # noqa: E402
from scripts.blender.scenes import build_scene  # noqa: E402
from scripts.storyboard import FPS, STORYBOARD  # noqa: E402


def _parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description="Render Stage 4 animated 2.5D/3D Blender scenes")
    parser.add_argument("--scene", type=str, default="all", help="Scene number 1..10, comma list, or 'all'")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--samples", type=int, default=16, help="EEVEE TAA or Cycles samples per frame")
    parser.add_argument("--engine", type=str, default="eevee", choices=["eevee", "cycles"])
    parser.add_argument("--no-freestyle", action="store_true", help="Disable Freestyle outlines for ultra-fast draft")
    parser.add_argument("--keyframe-only", action="store_true", help="Render only 1 hero mid-frame per scene for QA")
    parser.add_argument("--encode-clip", action="store_true", help="Encode scene PNG frames to MP4 clip & prune PNGs")
    parser.add_argument("--save-blend", action="store_true", help="Save generated .blend per scene")
    parser.add_argument("--output-dir", type=str, default=str(REPO_ROOT / "output"))
    return parser.parse_args(argv)


def _load_scene_frame_counts(output_dir: Path) -> Dict[int, int]:
    """Load exact voiceover-locked frame counts from timing_manifest.json (fallback to storyboard defaults)."""
    manifest_path = output_dir / "audio" / "timing_manifest.json"
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {int(s["scene_id"]): int(s["num_frames"]) for s in data["scenes"]}
    return {sc.scene_id: int(round(sc.default_duration_s * FPS)) for sc in STORYBOARD}


def _parse_scene_list(scene_arg: str) -> List[int]:
    if scene_arg.strip().lower() == "all":
        return [sc.scene_id for sc in STORYBOARD]
    return [int(x.strip()) for x in scene_arg.split(",") if x.strip()]


def _encode_frames_to_mp4(frames_dir: Path, clip_path: Path, fps: int = FPS) -> None:
    clip_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "16",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(clip_path),
    ]
    subprocess.run(cmd, check=True)
    print(f"[Render] Encoded clip {clip_path} ({clip_path.stat().st_size // 1024} KB)")


def render_single_scene(
    scene_id: int,
    num_frames: int,
    args: argparse.Namespace,
    out_dir: Path,
) -> None:
    print(f"\n[Render] === Building Scene {scene_id:02d} ({num_frames} frames @ {FPS} FPS, {args.width}x{args.height}, {args.engine}) ===")
    clear_scene()
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.fps_base = 1.0

    use_fs = not args.no_freestyle
    configure_eevee_render(
        scene,
        width=args.width,
        height=args.height,
        samples=args.samples,
        use_freestyle=use_fs,
        line_thickness=1.35,
        engine=args.engine,
    )

    # Optimize EEVEE shadow resolution slightly in animation mode for snappy headless CI render speed
    if args.engine == "eevee" and hasattr(scene.eevee, "shadow_resolution_scale"):
        scene.eevee.shadow_resolution_scale = 0.65

    mats = build_material_library()
    env = build_art_deco_lobby(mats)
    if use_fs:
        configure_freestyle_for_collection(
            scene,
            env_collection=env["env_col"],
            ink_color=(0.04, 0.03, 0.06),
            thickness=1.35,
            crease_angle_deg=132.0,
        )

    char_manifest = load_character_manifest()
    build_scene(scene_id, num_frames, env, mats, char_manifest)

    if args.save_blend:
        blend_dir = out_dir / "blend"
        blend_dir.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_dir / f"scene_{scene_id:02d}.blend"))

    if args.keyframe_only:
        # Render single hero midpoint frame (55% into scene) for rapid QA verification!
        hero_frame = max(1, min(num_frames, int(round(num_frames * 0.58))))
        scene.frame_set(hero_frame)
        kf_dir = out_dir / "keyframes"
        kf_dir.mkdir(parents=True, exist_ok=True)
        kf_path = kf_dir / f"scene_{scene_id:02d}_f{hero_frame:04d}.png"
        scene.render.filepath = str(kf_path)
        bpy.ops.render.render(write_still=True)
        print(f"[Render] Saved Scene {scene_id:02d} QA keyframe -> {kf_path}")
        return

    frames_dir = out_dir / "frames" / f"scene_{scene_id:02d}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(frames_dir / "frame_")
    scene.render.use_file_extension = True
    scene.frame_start = 1
    scene.frame_end = num_frames

    bpy.ops.render.render(animation=True)
    print(f"[Render] Finished Scene {scene_id:02d} frames in {frames_dir}")

    if args.encode_clip:
        clip_path = out_dir / "clips" / f"scene_{scene_id:02d}.mp4"
        _encode_frames_to_mp4(frames_dir, clip_path, fps=FPS)
        shutil.rmtree(frames_dir, ignore_errors=True)


def main() -> None:
    args = _parse_args()
    out_dir = Path(args.output_dir)
    frame_counts = _load_scene_frame_counts(out_dir)
    scene_ids = _parse_scene_list(args.scene)

    for sid in scene_ids:
        render_single_scene(sid, frame_counts[sid], args, out_dir)

    print("[Render] All requested Stage 4 scenes completed cleanly!")


if __name__ == "__main__":
    main()
