"""Generate 2.5D stylized character sprites (SVG + transparent PNG) and the Gate 2 Character Sheet preview.

Usage:
    python scripts/characters/generate_characters.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape as xml_esc

# Ensure repo root is importable when running script directly
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.characters.cast import (  # noqa: E402
    CAST_ORDER,
    CAST_SPECS,
    draw_character,
    draw_portrait_medallion,
)
from scripts.characters.svg_core import INK_COLOR, SvgBuilder, fmt  # noqa: E402
from scripts.characters.turnaround import TURNAROUND_ANGLES, draw_character_angle  # noqa: E402

FONT_STACK = "Segoe UI, Liberation Sans, DejaVu Sans, Arial, sans-serif"


def rasterize_svg(
    svg_content: str,
    png_path: Path,
    width: int,
    height: int,
    background: Optional[str] = None,
) -> None:
    """Rasterize SVG string to high-resolution PNG using resvg-py (or rsvg-convert fallback)."""
    png_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import resvg_py  # type: ignore

        data = resvg_py.svg_to_bytes(
            svg_string=svg_content,
            width=width,
            height=height,
            background=background,
            shape_rendering="geometric_precision",
            text_rendering="geometric_precision",
        )
        png_path.write_bytes(data)
        return
    except ImportError:
        pass

    rsvg_bin = shutil.which("rsvg-convert")
    if rsvg_bin:
        tmp_svg = png_path.with_suffix(".tmp.svg")
        tmp_svg.write_text(svg_content, encoding="utf-8")
        cmd = [rsvg_bin, "-w", str(width), "-h", str(height), "-o", str(png_path)]
        if background:
            cmd.extend(["-b", background])
        cmd.append(str(tmp_svg))
        subprocess.run(cmd, check=True)
        tmp_svg.unlink(missing_ok=True)
        return

    raise RuntimeError(
        "No SVG rasterizer available. Install 'resvg-py' (pip install resvg-py) or 'rsvg-convert' (librsvg2-bin)."
    )


# Exact SVG-space hand grip coordinates (hx, hy relative to cx=0, floor_y=0; 248 px = 1.0 m)
# Maps every prop cleanly onto each character's 2-bone IK gripping hands across all 5 turnaround angles!
HAND_ANCHORS_SVG = {
    "raka": {
        "front": {"coffee": (-124.0, -214.0, -0.05), "mirror": (124.0, -234.0, -0.05)},
        "three_quarter": {"coffee": (-110.0, -210.0, -0.08), "mirror": (112.0, -236.0, 0.08)},
        "side": {"coffee": (26.0, -182.0, -0.09), "mirror": (104.0, -226.0, 0.08)},
        "back_three_quarter": {"mirror": (-112.0, -228.0, -0.08), "coffee": (108.0, -212.0, 0.08)},
        "back": {"mirror": (-120.0, -234.0, 0.05), "coffee": (120.0, -214.0, 0.05)},
    },
    "bima": {
        "front": {"clipboard": (-132.0, -214.0, -0.06), "pen": (124.0, -226.0, -0.06)},
        "three_quarter": {"clipboard": (-120.0, -210.0, -0.08), "pen": (112.0, -222.0, 0.08)},
        "side": {"clipboard": (24.0, -176.0, -0.09), "pen": (108.0, -228.0, 0.08)},
        "back_three_quarter": {"pen": (-118.0, -222.0, -0.08), "clipboard": (116.0, -214.0, 0.08)},
        "back": {"pen": (-124.0, -224.0, 0.06), "clipboard": (128.0, -214.0, 0.06)},
    },
    "doni": {
        "front": {"comb": (-124.0, -206.0, -0.06), "watch": (-112.0, -188.0, -0.07), "briefcase": (114.0, -124.0, -0.05)},
        "three_quarter": {"comb": (-114.0, -206.0, -0.08), "watch": (-102.0, -188.0, -0.09), "briefcase": (104.0, -124.0, 0.07)},
        "side": {"comb": (96.0, -206.0, 0.08), "watch": (84.0, -190.0, 0.08), "briefcase": (-14.0, -118.0, -0.09)},
        "back_three_quarter": {"briefcase": (-106.0, -124.0, -0.08), "comb": (112.0, -204.0, 0.08), "watch": (100.0, -188.0, 0.08)},
        "back": {"briefcase": (-112.0, -124.0, 0.06), "comb": (120.0, -204.0, 0.06), "watch": (108.0, -188.0, 0.06)},
    },
    "clara": {
        "front": {"blueprint": (-120.0, -214.0, -0.06), "wrench": (120.0, -206.0, -0.06)},
        "three_quarter": {"blueprint": (-110.0, -212.0, -0.08), "wrench": (108.0, -206.0, 0.08)},
        "side": {"blueprint": (26.0, -162.0, -0.09), "wrench": (100.0, -208.0, 0.08)},
        "back_three_quarter": {"wrench": (-110.0, -206.0, -0.08), "blueprint": (108.0, -214.0, 0.08)},
        "back": {"wrench": (-118.0, -206.0, 0.06), "blueprint": (118.0, -214.0, 0.06)},
    },
}


def export_individual_sprites(assets_dir: Path) -> dict:
    """Export all 4 characters x 6 expressions + 5 turnaround angles (with AND without 2D props for 3D Art Deco props)."""
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Consistent card canvas so all Blender 2.5D character planes align identically on floor_y
    canvas_w = 480.0
    canvas_h = 560.0
    cx = canvas_w * 0.5
    floor_y = 528.0
    px_per_cm = 2.48  # 182 cm -> ~452 px tall
    px_per_m_svg = px_per_cm * 100.0  # 248.0 SVG px = 1.00 m

    out_w, out_h = 960, 1120  # 2x crisp supersampled resolution for Blender 3D cards

    manifest: dict = {
        "story": "Cermin Murah yang Mempercepat Lift Tanpa Menyentuh Mesinnya",
        "canvas_px": [out_w, out_h],
        "floor_uv_y": round(1.0 - (floor_y / canvas_h), 5),
        "center_uv_x": 0.5,
        "pixels_per_meter": round(px_per_m_svg * (out_h / canvas_h), 2),
        "characters": {},
    }

    for char_id in CAST_ORDER:
        spec = CAST_SPECS[char_id]
        char_dir = assets_dir / char_id
        noprops_dir = char_dir / "noprops"
        char_dir.mkdir(parents=True, exist_ok=True)
        noprops_dir.mkdir(parents=True, exist_ok=True)

        expr_files = {}
        expr_noprops_files = {}
        for expr in spec.expressions:
            svg = SvgBuilder(canvas_w, canvas_h, prefix=f"{char_id}_{expr}")
            svg.add(draw_character(svg, char_id, expression=expr, cx=cx, floor_y=floor_y, scale=1.0, with_props=True))
            svg_text = svg.render(background=None)

            svg_path = char_dir / f"{char_id}_{expr}.svg"
            png_path = char_dir / f"{char_id}_{expr}.png"
            svg_path.write_text(svg_text, encoding="utf-8")
            rasterize_svg(svg_text, png_path, width=out_w, height=out_h, background=None)

            expr_files[expr] = {
                "svg": str(svg_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "png": str(png_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "label": spec.expression_labels[expr],
            }

            # Prop-free sprite variant for pairing with true 3D Art Deco Blender props!
            np_svg = SvgBuilder(canvas_w, canvas_h, prefix=f"{char_id}_{expr}_np")
            np_svg.add(draw_character(np_svg, char_id, expression=expr, cx=cx, floor_y=floor_y, scale=1.0, with_props=False))
            np_png_path = noprops_dir / f"{char_id}_{expr}.png"
            rasterize_svg(np_svg.render(background=None), np_png_path, width=out_w, height=out_h, background=None)
            expr_noprops_files[expr] = {
                "png": str(np_png_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "label": spec.expression_labels[expr],
            }

        # Export 5-angle turnaround sprites (both 2D props & prop-free for 3D Art Deco props!)
        turn_dir = char_dir / "turnaround"
        turn_np_dir = char_dir / "turnaround_noprops"
        turn_dir.mkdir(parents=True, exist_ok=True)
        turn_np_dir.mkdir(parents=True, exist_ok=True)
        turn_files = {}
        turn_np_files = {}
        for angle_key, angle_deg, angle_label in TURNAROUND_ANGLES:
            t_svg = SvgBuilder(canvas_w, canvas_h, prefix=f"{char_id}_{angle_key}")
            t_svg.add(
                draw_character_angle(
                    t_svg,
                    char_id,
                    angle_key=angle_key,
                    expression=spec.default_expr,
                    cx=cx,
                    floor_y=floor_y,
                    scale=1.0,
                    with_props=True,
                )
            )
            t_text = t_svg.render(background=None)
            t_svg_path = turn_dir / f"{char_id}_{angle_key}.svg"
            t_png_path = turn_dir / f"{char_id}_{angle_key}.png"
            t_svg_path.write_text(t_text, encoding="utf-8")
            rasterize_svg(t_text, t_png_path, width=out_w, height=out_h, background=None)
            turn_files[angle_key] = {
                "yaw_deg": angle_deg,
                "label": angle_label,
                "svg": str(t_svg_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "png": str(t_png_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            }

            tnp_svg = SvgBuilder(canvas_w, canvas_h, prefix=f"{char_id}_{angle_key}_np")
            tnp_svg.add(
                draw_character_angle(
                    tnp_svg,
                    char_id,
                    angle_key=angle_key,
                    expression=spec.default_expr,
                    cx=cx,
                    floor_y=floor_y,
                    scale=1.0,
                    with_props=False,
                )
            )
            tnp_png_path = turn_np_dir / f"{char_id}_{angle_key}.png"
            rasterize_svg(tnp_svg.render(background=None), tnp_png_path, width=out_w, height=out_h, background=None)
            turn_np_files[angle_key] = {
                "yaw_deg": angle_deg,
                "label": angle_label,
                "png": str(tnp_png_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            }

        # Convert SVG hand anchors to metric Blender card-local (x_m, y_offset_m, z_m)
        hand_anchors_m = {}
        for akey, props_map in HAND_ANCHORS_SVG[char_id].items():
            hand_anchors_m[akey] = {
                prop_name: [round(hx / px_per_m_svg, 4), round(y_off, 4), round(-hy / px_per_m_svg, 4)]
                for prop_name, (hx, hy, y_off) in props_map.items()
            }

        manifest["characters"][char_id] = {
            "name": spec.name,
            "role": spec.role_id,
            "height_m": round(spec.height_cm / 100.0, 2),
            "default_expression": spec.default_expr,
            "palette": [{"name": n, "hex": h} for n, h in spec.palette],
            "props": spec.props_summary,
            "sprites": expr_files,
            "sprites_noprops": expr_noprops_files,
            "turnaround": turn_files,
            "turnaround_noprops": turn_np_files,
            "hand_anchors_m": hand_anchors_m,
        }

    manifest_path = assets_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def build_character_sheet_svg() -> str:
    """Compose the high-res Gate 2 Character Lineup & Swappable Expression Preview Sheet."""
    W, H = 2560.0, 1780.0
    svg = SvgBuilder(W, H, prefix="sheet")

    # Warm Art Deco studio cream background gradient
    bg_g = svg.add_linear_gradient(
        [(0.0, "#FBF6EA", 1.0), (0.55, "#F5ECD8", 1.0), (1.0, "#ECE0C8", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=0.2,
        y2=1.0,
    )
    svg.add(f'<rect x="0" y="0" width="{fmt(W)}" height="{fmt(H)}" fill="{bg_g}"/>')

    # Outer Art Deco brass double border frame
    svg.add(
        f'<rect x="28" y="24" width="{fmt(W - 56)}" height="{fmt(H - 48)}" rx="22" '
        f'fill="none" stroke="#C99A3B" stroke-width="4.0"/>'
        f'<rect x="38" y="34" width="{fmt(W - 76)}" height="{fmt(H - 68)}" rx="16" '
        f'fill="none" stroke="#22375C" stroke-width="2.0" opacity="0.55"/>'
    )

    # =========================================================================
    # HEADER BANNER
    # =========================================================================
    header_g = svg.add_linear_gradient(
        [(0.0, "#1B2E4B", 1.0), (0.5, "#233C5E", 1.0), (1.0, "#182842", 1.0)],
        0.0,
        0.0,
        1.0,
        0.0,
    )
    svg.add(
        f'<rect x="54" y="48" width="{fmt(W - 108)}" height="114" rx="14" '
        f'fill="{header_g}" stroke="#C99A3B" stroke-width="3.2"/>'
        # Decorative gold Art Deco corner accents
        f'<path d="M 74,72 L 114,72 M 74,72 L 74,104" stroke="#E8B948" stroke-width="3.2" stroke-linecap="round"/>'
        f'<path d="M {fmt(W - 74)},72 L {fmt(W - 114)},72 M {fmt(W - 74)},72 L {fmt(W - 74)},104" '
        f'stroke="#E8B948" stroke-width="3.2" stroke-linecap="round"/>'
        f'<text x="{fmt(W * 0.5)}" y="96" text-anchor="middle" font-family="{FONT_STACK}" '
        f'font-size="38" font-weight="800" letter-spacing="2.4" fill="#FFF7E2">'
        f'GATE 2 — CHARACTER DESIGN &amp; EXPRESSION SHEET</text>'
        f'<text x="{fmt(W * 0.5)}" y="136" text-anchor="middle" font-family="{FONT_STACK}" '
        f'font-size="21" font-weight="600" letter-spacing="0.8" fill="#E8C468">'
        f'Opsi 2: "Cermin Murah yang Mempercepat Lift"  •  2.5D Pill/Capsule Cutout  •  Variable-Width Ink  •  2-Bone IK Stick Limbs</text>'
    )

    # =========================================================================
    # SECTION 1: FULL CAST LINEUP & HEIGHT/PROPORTION COMPARISON
    # =========================================================================
    sec1_x, sec1_y, sec1_w, sec1_h = 54.0, 182.0, W - 108.0, 742.0
    stage_bg = svg.add_linear_gradient(
        [(0.0, "#FFFDF7", 1.0), (0.82, "#F9F3E4", 1.0), (1.0, "#E8DEC9", 1.0)],
        0.0,
        0.0,
        0.0,
        1.0,
    )
    svg.add(
        f'<rect x="{fmt(sec1_x)}" y="{fmt(sec1_y)}" width="{fmt(sec1_w)}" height="{fmt(sec1_h)}" rx="16" '
        f'fill="{stage_bg}" stroke="#C9A86A" stroke-width="2.6"/>'
    )
    svg.add(
        f'<rect x="{fmt(sec1_x + 22)}" y="{fmt(sec1_y + 18)}" width="540" height="38" rx="8" fill="#22375C"/>'
        f'<text x="{fmt(sec1_x + 42)}" y="{fmt(sec1_y + 44)}" font-family="{FONT_STACK}" '
        f'font-size="20" font-weight="800" letter-spacing="1.2" fill="#FFF6DC">'
        f'1. CAST LINEUP &amp; PERBANDINGAN PROPORSI</text>'
    )

    # Height ruler grid inside lineup stage (floor_y = 776, scale = 1.08)
    floor_y = 776.0
    lineup_scale = 1.08
    px_per_cm = 2.48 * lineup_scale

    # Marble floor strip below baseline
    svg.add(
        f'<rect x="{fmt(sec1_x + 2)}" y="{fmt(floor_y)}" width="{fmt(sec1_w - 4)}" height="{fmt(sec1_y + sec1_h - floor_y - 2)}" '
        f'rx="0" fill="#E3D7C0" opacity="0.65"/>'
    )

    for cm in (0, 50, 100, 150, 175):
        gy = floor_y - cm * px_per_cm
        is_ground = cm == 0
        stroke_col = "#22375C" if is_ground else "#C4B59B"
        stroke_w = "3.2" if is_ground else "1.5"
        dash = "" if is_ground else ' stroke-dasharray="9 7"'
        svg.add(
            f'<line x1="{fmt(sec1_x + 92)}" y1="{fmt(gy)}" x2="{fmt(sec1_x + sec1_w - 36)}" y2="{fmt(gy)}" '
            f'stroke="{stroke_col}" stroke-width="{stroke_w}"{dash} opacity="{"0.85" if is_ground else "0.52"}"/>'
            f'<text x="{fmt(sec1_x + 80)}" y="{fmt(gy + 6)}" text-anchor="end" font-family="{FONT_STACK}" '
            f'font-size="16" font-weight="700" fill="#5D5549">{cm} cm</text>'
        )

    # Place all 4 characters cleanly across the stage
    slot_xs = [445.0, 1010.0, 1575.0, 2135.0]
    shadow_g = svg.add_radial_gradient([(0.0, "#241E1A", 0.34), (0.65, "#241E1A", 0.14), (1.0, "#241E1A", 0.0)], 0.5, 0.5, 0.5)

    for char_id, slot_x in zip(CAST_ORDER, slot_xs):
        spec = CAST_SPECS[char_id]
        # Grounded contact shadow ellipse
        svg.add(f'<ellipse cx="{fmt(slot_x)}" cy="{fmt(floor_y + 4)}" rx="115" ry="18" fill="{shadow_g}"/>')

        # Subtle height callout marker at exact character crown
        top_marker_y = floor_y - spec.total_height_px * lineup_scale
        svg.add(
            f'<line x1="{fmt(slot_x - 135)}" y1="{fmt(top_marker_y)}" x2="{fmt(slot_x + 135)}" y2="{fmt(top_marker_y)}" '
            f'stroke="#C99A3B" stroke-width="1.8" stroke-dasharray="5 5" opacity="0.75"/>'
            f'<rect x="{fmt(slot_x + 94)}" y="{fmt(top_marker_y - 14)}" width="74" height="24" rx="6" fill="#C99A3B"/>'
            f'<text x="{fmt(slot_x + 131)}" y="{fmt(top_marker_y + 3)}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="14" font-weight="800" fill="#182336">{spec.height_cm} cm</text>'
        )

        # Full-body hero character with props!
        svg.add(
            draw_character(
                svg,
                char_id,
                expression=spec.default_expr,
                cx=slot_x,
                floor_y=floor_y,
                scale=lineup_scale,
                with_props=True,
            )
        )

        # Nameplate & Props Card below floor baseline
        plate_w = 480.0
        plate_x = slot_x - plate_w * 0.5
        plate_y = floor_y + 20.0
        svg.add(
            f'<rect x="{fmt(plate_x)}" y="{fmt(plate_y)}" width="{fmt(plate_w)}" height="114" rx="12" '
            f'fill="#FFFDF8" stroke="#22375C" stroke-width="2.4"/>'
            f'<rect x="{fmt(plate_x)}" y="{fmt(plate_y)}" width="{fmt(plate_w)}" height="36" rx="10" fill="#22375C"/>'
            f'<text x="{fmt(slot_x)}" y="{fmt(plate_y + 25)}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="21" font-weight="800" letter-spacing="1.0" fill="#FFF7E2">'
            f'{xml_esc(spec.name)}  —  {xml_esc(spec.role_id)}</text>'
            f'<text x="{fmt(slot_x)}" y="{fmt(plate_y + 62)}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="16" font-weight="700" fill="#2A3A52">Properti: {xml_esc(spec.props_summary)}</text>'
            f'<text x="{fmt(slot_x)}" y="{fmt(plate_y + 92)}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="15" font-weight="600" fill="#6D5838">"{xml_esc(spec.tagline)}"</text>'
        )

    # =========================================================================
    # SECTION 2: SWAPPABLE EXPRESSION SPRITES (5 PER CHAR) + PALETTE MATRIX
    # =========================================================================
    sec2_y = 944.0
    svg.add(
        f'<rect x="54" y="{fmt(sec2_y)}" width="860" height="38" rx="8" fill="#22375C"/>'
        f'<text x="74" y="{fmt(sec2_y + 26)}" font-family="{FONT_STACK}" '
        f'font-size="20" font-weight="800" letter-spacing="1.2" fill="#FFF6DC">'
        f'2. VARIASI EKSPRESI WAJAH (SWAPPABLE SPRITES) &amp; PALET WARNA</text>'
    )

    card_w = 1212.0
    card_h = 358.0
    gap_x = 28.0
    gap_y = 22.0
    grid_y0 = sec2_y + 52.0

    # Display 5 crisp expressions per character (exceeding the minimum 4!)
    card_positions = [
        (54.0, grid_y0),
        (54.0 + card_w + gap_x, grid_y0),
        (54.0, grid_y0 + card_h + gap_y),
        (54.0 + card_w + gap_x, grid_y0 + card_h + gap_y),
    ]

    accent_rings = {
        "raka": "#3E6E5F",
        "bima": "#22375C",
        "doni": "#8E2436",
        "clara": "#D98A1A",
    }

    for char_id, (cx0, cy0) in zip(CAST_ORDER, card_positions):
        spec = CAST_SPECS[char_id]
        accent = accent_rings[char_id]

        # Character expression card container
        svg.add(
            f'<rect x="{fmt(cx0)}" y="{fmt(cy0)}" width="{fmt(card_w)}" height="{fmt(card_h)}" rx="16" '
            f'fill="#FFFDF8" stroke="{accent}" stroke-width="3.0"/>'
            # Top title bar
            f'<path d="M {fmt(cx0)},{fmt(cy0 + 16)} Q {fmt(cx0)},{fmt(cy0)} {fmt(cx0 + 16)},{fmt(cy0)} '
            f'L {fmt(cx0 + card_w - 16)},{fmt(cy0)} Q {fmt(cx0 + card_w)},{fmt(cy0)} {fmt(cx0 + card_w)},{fmt(cy0 + 16)} '
            f'L {fmt(cx0 + card_w)},{fmt(cy0 + 46)} L {fmt(cx0)},{fmt(cy0 + 46)} Z" fill="{accent}"/>'
            f'<text x="{fmt(cx0 + 22)}" y="{fmt(cy0 + 31)}" font-family="{FONT_STACK}" '
            f'font-size="21" font-weight="800" fill="#FFF9EB">{xml_esc(spec.name)}  •  {xml_esc(spec.role_id)}</text>'
            f'<text x="{fmt(cx0 + card_w - 22)}" y="{fmt(cy0 + 30)}" text-anchor="end" font-family="{FONT_STACK}" '
            f'font-size="15" font-weight="700" fill="#FFE6A8">6 Sprite Ekspresi Siap Blender (5 Ditampilkan)</text>'
        )

        # 5 Expression Medallions evenly spaced in upper section of card
        shown_exprs = spec.expressions[:5]
        med_r = 69.0
        med_y = cy0 + 138.0
        spacing = (card_w - 104.0) / 5.0
        for idx, expr in enumerate(shown_exprs):
            mx = cx0 + 52.0 + spacing * (idx + 0.5)
            svg.add(
                draw_portrait_medallion(
                    svg,
                    char_id,
                    expression=expr,
                    cx=mx,
                    cy=med_y,
                    radius=med_r,
                    bg_color="#F5EEDB",
                    ring_color="#D9A841",
                )
            )
            label = spec.expression_labels[expr]
            svg.add(
                f'<rect x="{fmt(mx - 88)}" y="{fmt(med_y + med_r + 10)}" width="176" height="28" rx="14" '
                f'fill="#F2E9D4" stroke="{accent}" stroke-width="1.6"/>'
                f'<text x="{fmt(mx)}" y="{fmt(med_y + med_r + 29)}" text-anchor="middle" font-family="{FONT_STACK}" '
                f'font-size="14.5" font-weight="800" fill="#1F2937">{xml_esc(label)}</text>'
            )

        # Divider line above Palette & Comedy Hook strip
        div_y = cy0 + 258.0
        svg.add(
            f'<line x1="{fmt(cx0 + 20)}" y1="{fmt(div_y)}" x2="{fmt(cx0 + card_w - 20)}" y2="{fmt(div_y)}" '
            f'stroke="#DDD2BC" stroke-width="2.0"/>'
        )

        # 5 Color Palette Swatches
        sw_x0 = cx0 + 24.0
        sw_y = div_y + 16.0
        sw_step = 234.0
        for s_idx, (sw_name, sw_hex) in enumerate(spec.palette):
            sx = sw_x0 + s_idx * sw_step
            svg.add(
                f'<rect x="{fmt(sx)}" y="{fmt(sw_y)}" width="34" height="34" rx="8" '
                f'fill="{sw_hex}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
                f'<text x="{fmt(sx + 44)}" y="{fmt(sw_y + 15)}" font-family="{FONT_STACK}" '
                f'font-size="14" font-weight="800" fill="#1F2937">{xml_esc(sw_name)}</text>'
                f'<text x="{fmt(sx + 44)}" y="{fmt(sw_y + 32)}" font-family="{FONT_STACK}" '
                f'font-size="13" font-weight="600" fill="#6B6256">{xml_esc(sw_hex)}</text>'
            )

        # Comedy visual beat note at bottom of card
        svg.add(
            f'<text x="{fmt(cx0 + 24)}" y="{fmt(cy0 + card_h - 16)}" font-family="{FONT_STACK}" '
            f'font-size="15" font-weight="700" fill="{accent}">Komedi Visual: '
            f'<tspan font-weight="600" fill="#3B352D">{xml_esc(spec.comedy_hook)}</tspan></text>'
        )

    return svg.render(background="#FBF6EA")


def _angle_dial_icon(cx: float, cy: float, yaw_deg: int) -> str:
    """Mini top-down compass dial illustrating the exact rotation yaw angle."""
    import math

    # 0° faces down toward viewer (+Y), 90° faces right (+X), 180° faces away (-Y)
    rad = math.radians(90 - yaw_deg)
    tx = cx + math.cos(rad) * 14.0
    ty = cy + math.sin(rad) * 14.0
    return (
        f'<g>'
        f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="15" fill="#182842" stroke="#E8B948" stroke-width="2.2"/>'
        f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="3.2" fill="#FFF7E2"/>'
        f'<line x1="{fmt(cx)}" y1="{fmt(cy)}" x2="{fmt(tx)}" y2="{fmt(ty)}" stroke="#E8B948" stroke-width="3.2" stroke-linecap="round"/>'
        f'<circle cx="{fmt(tx)}" cy="{fmt(ty)}" r="3.2" fill="#FF6B57"/>'
        f"</g>"
    )


def build_turnaround_sheet_svg() -> str:
    """Compose the high-res 5-Angle Character Turnaround Sheet (0°, 45°, 90°, 135°, 180°) for all 4 characters."""
    W, H = 2560.0, 2240.0
    svg = SvgBuilder(W, H, prefix="turn")

    bg_g = svg.add_linear_gradient(
        [(0.0, "#FBF6EA", 1.0), (0.55, "#F5ECD8", 1.0), (1.0, "#ECE0C8", 1.0)],
        0.0,
        0.0,
        0.2,
        1.0,
    )
    svg.add(f'<rect x="0" y="0" width="{fmt(W)}" height="{fmt(H)}" fill="{bg_g}"/>')
    svg.add(
        f'<rect x="28" y="24" width="{fmt(W - 56)}" height="{fmt(H - 48)}" rx="22" fill="none" stroke="#C99A3B" stroke-width="4.0"/>'
        f'<rect x="38" y="34" width="{fmt(W - 76)}" height="{fmt(H - 68)}" rx="16" fill="none" stroke="#22375C" stroke-width="2.0" opacity="0.55"/>'
    )

    # Header Banner
    header_g = svg.add_linear_gradient(
        [(0.0, "#1B2E4B", 1.0), (0.5, "#233C5E", 1.0), (1.0, "#182842", 1.0)],
        0.0,
        0.0,
        1.0,
        0.0,
    )
    svg.add(
        f'<rect x="54" y="48" width="{fmt(W - 108)}" height="114" rx="14" fill="{header_g}" stroke="#C99A3B" stroke-width="3.2"/>'
        f'<path d="M 74,72 L 114,72 M 74,72 L 74,104" stroke="#E8B948" stroke-width="3.2" stroke-linecap="round"/>'
        f'<path d="M {fmt(W - 74)},72 L {fmt(W - 114)},72 M {fmt(W - 74)},72 L {fmt(W - 74)},104" stroke="#E8B948" stroke-width="3.2" stroke-linecap="round"/>'
        f'<text x="{fmt(W * 0.5)}" y="96" text-anchor="middle" font-family="{FONT_STACK}" '
        f'font-size="37" font-weight="800" letter-spacing="2.2" fill="#FFF7E2">'
        f'GATE 2B — MULTI-ANGLE CHARACTER TURNAROUND SHEET (360° PIPELINE)</text>'
        f'<text x="{fmt(W * 0.5)}" y="136" text-anchor="middle" font-family="{FONT_STACK}" '
        f'font-size="20" font-weight="600" letter-spacing="0.6" fill="#E8C468">'
        f'5 Sudut Rotasi (0° Depan → 45° 3/4 → 90° Samping → 135° Belakang 3/4 → 180° Belakang)  •  Siap Orbit Kamera 3D Blender</text>'
    )

    # Column header bar with angle compass dials
    col_x0 = 280.0
    col_w = (W - 54.0 - col_x0) / 5.0
    bar_y = 180.0
    svg.add(
        f'<rect x="54" y="{fmt(bar_y)}" width="{fmt(W - 108)}" height="56" rx="12" fill="#22375C" stroke="#C99A3B" stroke-width="2.2"/>'
        f'<text x="166" y="{fmt(bar_y + 35)}" text-anchor="middle" font-family="{FONT_STACK}" '
        f'font-size="19" font-weight="800" fill="#FFE6A8">KARAKTER</text>'
    )
    for idx, (akey, deg, alabel) in enumerate(TURNAROUND_ANGLES):
        cx = col_x0 + col_w * (idx + 0.5)
        svg.add(_angle_dial_icon(cx - 154.0, bar_y + 28.0, deg))
        svg.add(
            f'<text x="{fmt(cx + 16)}" y="{fmt(bar_y + 34)}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="17.5" font-weight="800" fill="#FFF7E2">{xml_esc(alabel)}</text>'
        )

    # 4 Character Rows
    row_y0 = 252.0
    row_h = 468.0
    row_gap = 18.0
    shadow_g = svg.add_radial_gradient([(0.0, "#241E1A", 0.30), (0.65, "#241E1A", 0.12), (1.0, "#241E1A", 0.0)], 0.5, 0.5, 0.5)
    accent_map = {"raka": "#3E6E5F", "bima": "#22375C", "doni": "#8E2436", "clara": "#D98A1A"}
    turn_notes = {
        "raka": "Kacamata + tangkai samping, syal rajut 360°, belahan jas belakang, cermin ukir emas.",
        "bima": "Dasi merah berkibar di profil samping, jas pinstripe + ventilasi kembar belakang.",
        "doni": "Jambul pompadour menonjol ikonik 90°, cocok untuk shot cermin dari sudut 135°!",
        "clara": "Visor helm + goggles + kuncir di profil 90°, tali silang X-strap denim di belakang.",
    }

    for r_idx, char_id in enumerate(CAST_ORDER):
        spec = CAST_SPECS[char_id]
        accent = accent_map[char_id]
        ry = row_y0 + r_idx * (row_h + row_gap)
        floor_y = ry + row_h - 32.0
        char_scale = 0.86

        # Row background card
        svg.add(
            f'<rect x="54" y="{fmt(ry)}" width="{fmt(W - 108)}" height="{fmt(row_h)}" rx="16" '
            f'fill="#FFFDF7" stroke="{accent}" stroke-width="2.8"/>'
            # Left character identity sidebar
            f'<path d="M 54,{fmt(ry + 16)} Q 54,{fmt(ry)} 70,{fmt(ry)} L 272,{fmt(ry)} '
            f'L 272,{fmt(ry + row_h)} L 70,{fmt(ry + row_h)} Q 54,{fmt(ry + row_h)} 54,{fmt(ry + row_h - 16)} Z" '
            f'fill="{accent}"/>'
            f'<text x="163" y="{fmt(ry + 125)}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="30" font-weight="900" letter-spacing="1.2" fill="#FFF8E6">{xml_esc(spec.name)}</text>'
            f'<text x="163" y="{fmt(ry + 158)}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="13.5" font-weight="700" fill="#FFE6A8">{xml_esc(spec.role_id)}</text>'
            f'<rect x="115" y="{fmt(ry + 178)}" width="96" height="30" rx="15" fill="#182336" opacity="0.55"/>'
            f'<text x="163" y="{fmt(ry + 199)}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="16" font-weight="800" fill="#FFF7E2">{spec.height_cm} cm</text>'
        )
        # Wrapped sidebar turnaround detail note
        note = turn_notes[char_id]
        words = note.split()
        lines = []
        cur = ""
        for w in words:
            if len(cur) + len(w) + 1 <= 22:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        for l_i, line in enumerate(lines):
            svg.add(
                f'<text x="163" y="{fmt(ry + 252 + l_i * 25)}" text-anchor="middle" font-family="{FONT_STACK}" '
                f'font-size="15.5" font-weight="600" fill="#F8EFE0">{xml_esc(line)}</text>'
            )

        # Horizontal proportion consistency guide lines (floor, mid-torso, crown)
        crown_y = floor_y - spec.total_height_px * char_scale
        svg.add(
            f'<line x1="286" y1="{fmt(floor_y)}" x2="{fmt(W - 72)}" y2="{fmt(floor_y)}" stroke="#22375C" stroke-width="2.6" opacity="0.72"/>'
            f'<line x1="286" y1="{fmt(crown_y)}" x2="{fmt(W - 72)}" y2="{fmt(crown_y)}" stroke="#C99A3B" stroke-width="1.6" stroke-dasharray="7 6" opacity="0.65"/>'
            f'<line x1="286" y1="{fmt((floor_y + crown_y) * 0.5)}" x2="{fmt(W - 72)}" y2="{fmt((floor_y + crown_y) * 0.5)}" stroke="#C4B59B" stroke-width="1.3" stroke-dasharray="5 6" opacity="0.45"/>'
        )

        # Render all 5 rotation angles across the row!
        for c_idx, (akey, deg, _alabel) in enumerate(TURNAROUND_ANGLES):
            slot_x = col_x0 + col_w * (c_idx + 0.5)
            # Subtle vertical column divider
            if c_idx > 0:
                div_x = col_x0 + col_w * c_idx
                svg.add(
                    f'<line x1="{fmt(div_x)}" y1="{fmt(ry + 16)}" x2="{fmt(div_x)}" y2="{fmt(ry + row_h - 16)}" '
                    f'stroke="#E5DBC6" stroke-width="1.6"/>'
                )
            # Grounded shadow
            svg.add(f'<ellipse cx="{fmt(slot_x)}" cy="{fmt(floor_y + 3)}" rx="84" ry="13" fill="{shadow_g}"/>')
            # Character at this exact rotation angle!
            svg.add(
                draw_character_angle(
                    svg,
                    char_id,
                    angle_key=akey,
                    expression=spec.default_expr,
                    cx=slot_x,
                    floor_y=floor_y,
                    scale=char_scale,
                    with_props=True,
                )
            )

    return svg.render(background="#FBF6EA")


def main() -> None:
    assets_dir = REPO_ROOT / "assets" / "characters"
    previews_dir = REPO_ROOT / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)

    print("[1/3] Generating 24 expression sprites + 20 multi-angle turnaround sprites (SVG + high-res PNG)...")
    manifest = export_individual_sprites(assets_dir)
    total_expr = sum(len(c["sprites"]) for c in manifest["characters"].values())
    total_turn = sum(len(c["turnaround"]) for c in manifest["characters"].values())
    print(f"      Exported {total_expr} expression + {total_turn} turnaround sprites + manifest.json to {assets_dir}")

    print("[2/3] Rendering Gate 2 Character Sheet preview...")
    sheet_svg = build_character_sheet_svg()
    sheet_svg_path = previews_dir / "characters_preview.svg"
    sheet_png_path = previews_dir / "characters_preview.png"
    sheet_svg_path.write_text(sheet_svg, encoding="utf-8")
    rasterize_svg(sheet_svg, sheet_png_path, width=2560, height=1780, background="#FBF6EA")
    print(f"      Saved {sheet_png_path} ({sheet_png_path.stat().st_size // 1024} KB)")

    print("[3/3] Rendering Gate 2B Multi-Angle Turnaround Sheet preview...")
    turn_svg = build_turnaround_sheet_svg()
    turn_svg_path = previews_dir / "characters_turnaround.svg"
    turn_png_path = previews_dir / "characters_turnaround.png"
    turn_svg_path.write_text(turn_svg, encoding="utf-8")
    rasterize_svg(turn_svg, turn_png_path, width=2560, height=2240, background="#FBF6EA")
    print(f"      Saved {turn_png_path} ({turn_png_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
