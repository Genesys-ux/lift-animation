"""Final FFmpeg Composer: Stitches rendered Blender scene clips + master audio + burned-in bold ASS subtitles.

Usage:
    python scripts/compose.py                    # Final production render -> output/output_short_9x16.mp4
    python scripts/compose.py --from-keyframes   # Local QA animatic from 10 Blender keyframes -> output/animatic_preview_9x16.mp4
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.storyboard import FPS, HEIGHT, STORYBOARD, WIDTH  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose final 9:16 YouTube Short MP4 via FFmpeg")
    parser.add_argument("--output-dir", type=str, default=str(REPO_ROOT / "output"))
    parser.add_argument("--from-keyframes", action="store_true", help="Assemble timed animatic QA MP4 from scene keyframes")
    parser.add_argument("--out-file", type=str, default="", help="Override output MP4 path")
    return parser.parse_args()


def _ensure_scene_clips(out_dir: Path, scene_ids: List[int]) -> List[Path]:
    """Locate either sharded scene_XX_p1/p2.mp4 clips or whole scene_XX.mp4 clips in exact order."""
    clips_dir = out_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clips: List[Path] = []

    for sid in scene_ids:
        # First check for multi-part sharded clips (scene_XX_p1.mp4, scene_XX_p2.mp4, ...)
        sharded = sorted(
            out_dir.rglob(f"scene_{sid:02d}_p*.mp4"),
            key=lambda p: int(p.stem.rsplit("_p", 1)[1]) if "_p" in p.stem else 0,
        )
        if sharded:
            clips.extend(sharded)
            continue

        clip_path = clips_dir / f"scene_{sid:02d}.mp4"
        if not clip_path.exists():
            nested = sorted(out_dir.rglob(f"scene_{sid:02d}.mp4"))
            if nested:
                clip_path = nested[0]
        if not clip_path.exists():
            frames_dir = out_dir / "frames" / f"scene_{sid:02d}"
            if frames_dir.exists() and any(frames_dir.glob("frame_*.png")):
                print(f"[Compose] Encoding PNG sequence for Scene {sid:02d}...")
                subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-framerate", str(FPS),
                        "-i", str(frames_dir / "frame_%04d.png"),
                        "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                        "-pix_fmt", "yuv420p", str(clip_path),
                    ],
                    check=True,
                )
            else:
                raise FileNotFoundError(
                    f"Missing rendered clip(s) for Scene {sid:02d} in {clips_dir}. "
                    f"Render scenes via scripts/render_final.py first."
                )
        clips.append(clip_path)
    return clips


def _build_animatic_clips_from_keyframes(out_dir: Path, timing_scenes: List[dict]) -> List[Path]:
    """Turn each scene's rendered Blender hero keyframe into a timed smooth-zoom MP4 clip for end-to-end QA."""
    kf_dir = out_dir / "keyframes"
    tmp_dir = out_dir / "clips_animatic"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    clips: List[Path] = []

    for entry in timing_scenes:
        sid = int(entry["scene_id"])
        dur = float(entry["duration_s"])
        matches = sorted(kf_dir.glob(f"scene_{sid:02d}_*.png"))
        if not matches:
            raise FileNotFoundError(f"Missing keyframe PNG for Scene {sid:02d} in {kf_dir}")
        img_path = matches[0]
        clip_path = tmp_dir / f"animatic_{sid:02d}.mp4"

        n_frames = int(entry["num_frames"])
        # Gentle cinematic 1.00 -> 1.06 subtle push-in over scene duration
        vf = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"zoompan=z='1+0.06*(on/{max(1, n_frames)})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={n_frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(img_path),
                "-vf", vf,
                "-t", f"{dur:.4f}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-pix_fmt", "yuv420p",
                str(clip_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        clips.append(clip_path)
    return clips


def main() -> None:
    args = _parse_args()
    out_dir = Path(args.output_dir).resolve()
    audio_dir = out_dir / "audio"
    timing_path = audio_dir / "timing_manifest.json"
    audio_wav = audio_dir / "master_mix.wav"
    ass_path = audio_dir / "subtitles.ass"

    if not timing_path.exists() or not audio_wav.exists() or not ass_path.exists():
        raise FileNotFoundError(
            "Audio & subtitle artifacts missing. Run 'python scripts/audio/generate_audio.py' first."
        )

    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    timing_scenes = timing["scenes"]
    scene_ids = [int(s["scene_id"]) for s in timing_scenes]

    if args.from_keyframes:
        print("[Compose] Assembling 60s Animatic QA clips from Blender scene keyframes...")
        clips = _build_animatic_clips_from_keyframes(out_dir, timing_scenes)
        final_mp4 = Path(args.out_file) if args.out_file else (out_dir / "animatic_preview_9x16.mp4")
    else:
        print("[Compose] Collecting all 10 rendered Blender scene clips...")
        clips = _ensure_scene_clips(out_dir, scene_ids)
        final_mp4 = Path(args.out_file) if args.out_file else (out_dir / "output_short_9x16.mp4")

    # Write FFmpeg concat demuxer list using clean forward-slash relative paths
    concat_file = out_dir / "concat_list.txt"
    lines = []
    for c in clips:
        rel = c.resolve().relative_to(out_dir).as_posix()
        lines.append(f"file '{rel}'\n")
    concat_file.write_text("".join(lines), encoding="utf-8")

    # Use relative path from REPO_ROOT for ASS filter so FFmpeg handles Windows & Linux identically!
    ass_rel = ass_path.resolve().relative_to(REPO_ROOT).as_posix()
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
        f"ass={ass_rel}"
    )

    print(f"[Compose] Muxing video + master audio + burning in bold pop-in subtitles -> {final_mp4}")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", str(audio_wav),
        "-vf", vf,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-shortest",
        "-movflags", "+faststart",
        str(final_mp4),
    ]
    subprocess.run(cmd, cwd=str(REPO_ROOT), check=True)
    size_mb = final_mp4.stat().st_size / (1024 * 1024)
    print(f"[Compose] SUCCESS! Final 9:16 YouTube Short saved to {final_mp4} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
