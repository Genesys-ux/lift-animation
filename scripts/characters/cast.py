"""Character cast builders for 'The Slow Elevator & Mirror' (Opsi 2).

Four distinct 2.5D stylized pill/capsule characters with:
- Volumetric 3D costumes, headwear, underlying hair, and faceted props
- Consistent top-left studio lighting (specular, core shadow, warm bounce, cast shadows)
- Variable-width organic ink outlines
- Biomechanical 2-bone IK flexible stick-figure limbs
- 6 swappable facial expressions per character
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .expressions import draw_expression
from .props import (
    draw_coffee_cup,
    draw_complaint_clipboard,
    draw_gold_hand_mirror,
    draw_gold_wristwatch,
    draw_leather_briefcase,
    draw_pocket_comb,
    draw_red_pen,
    draw_rocket_blueprint,
    draw_steel_wrench,
)
from .rig import clavicle_follow, draw_hand, draw_shoe, draw_sleeve_cap, draw_stick_limb, solve_2bone_ik
from .svg_core import (
    INK_COLOR,
    Point,
    SvgBuilder,
    darken,
    fmt,
    lighten,
    mix_color,
    pts_to_path,
    sample_rounded_capsule,
    variable_ink_closed,
)


@dataclass(frozen=True)
class CharacterSpec:
    char_id: str
    name: str
    role_id: str
    tagline: str
    height_cm: int
    total_height_px: float
    default_expr: str
    expressions: Tuple[str, ...]
    expression_labels: Dict[str, str]
    palette: Tuple[Tuple[str, str], ...]
    props_summary: str
    comedy_hook: str


CAST_SPECS: Dict[str, CharacterSpec] = {
    "raka": CharacterSpec(
        char_id="raka",
        name="RAKA",
        role_id="Psikolog Perilaku Santai",
        tagline="Tenang, tajam, pemecah masalah dengan ide sederhana",
        height_cm=182,
        total_height_px=452.0,
        default_expr="chill",
        expressions=("chill", "aha", "smug", "thinking", "deadpan", "laugh"),
        expression_labels={
            "chill": "Santai",
            "aha": "Ide Aha!",
            "smug": "Tahu Rahasianya",
            "thinking": "Menganalisis",
            "deadpan": "Datar / Tenang",
            "laugh": "Tertawa Puas",
        },
        palette=(
            ("Blazer Olive", "#3E6E5F"),
            ("Syal Mustard", "#E8A825"),
            ("Knit Krem", "#F5EBD6"),
            ("Kacamata Emas", "#E4B44B"),
            ("Rambut Espresso", "#2E1E16"),
        ),
        props_summary="Gelas Kopi Kertas + Cermin Emas Art Deco",
        comedy_hook="Menyeruput kopi santai & ekspresi deadpan saat semua orang panik",
    ),
    "bima": CharacterSpec(
        char_id="bima",
        name="PAK BIMA",
        role_id="Manajer Gedung Panik",
        tagline="Obsesif soal keluhan penghuni & selalu di ambang pingsan",
        height_cm=174,
        total_height_px=432.0,
        default_expr="panic",
        expressions=("panic", "stressed", "shocked", "skeptical", "relieved", "proud"),
        expression_labels={
            "panic": "Panik Total",
            "stressed": "Stres Berat",
            "shocked": "Kaget (O_O)",
            "skeptical": "Curiga / Ragu",
            "relieved": "Lega Sekali",
            "proud": "Bangga Pamer",
        },
        palette=(
            ("Jas Navy Deco", "#22375C"),
            ("Rompi Sampanye", "#E0C489"),
            ("Dasi Merah", "#D93829"),
            ("Kemeja Gading", "#FAF7F0"),
            ("Pin Kuningan", "#E8B73E"),
        ),
        props_summary="Clipboard 'Komplain 99%' + Pena Merah",
        comedy_hook="Dasi melayang, dua helai rambut berdiri & keringat muncrat saat panik",
    ),
    "doni": CharacterSpec(
        char_id="doni",
        name="PAK DONI",
        role_id="Penghuni Pemarah -> Narsis",
        tagline="Marah-marah soal lift lambat, mendadak lupa waktu depan cermin",
        height_cm=158,
        total_height_px=400.0,
        default_expr="furious",
        expressions=("furious", "impatient", "stunned", "narcissistic", "happy", "deadpan"),
        expression_labels={
            "furious": "Murka / Protes",
            "impatient": "Bosan & Kesal",
            "stunned": "Tercengang (O_o)",
            "narcissistic": "Narsis Cermin",
            "happy": "Senang Polos",
            "deadpan": "Datar",
        },
        palette=(
            ("Rompi Burgundy", "#8E2436"),
            ("Kemeja Langit", "#EAF2FA"),
            ("Koper Kulit", "#8C4720"),
            ("Jam Emas", "#F0BD38"),
            ("Jambul Hitam", "#1E2230"),
        ),
        props_summary="Koper Kulit + Jam Tangan Emas + Sisir Saku",
        comedy_hook="Marah memelototi jam, lalu langsung menyisir jambul pompadour di cermin",
    ),
    "clara": CharacterSpec(
        char_id="clara",
        name="CLARA",
        role_id="Insinyur Lift Over-Engineered",
        tagline="Solusi favoritnya: pasang mesin roket turbo ke semua hal",
        height_cm=166,
        total_height_px=414.0,
        default_expr="excited",
        expressions=("excited", "determined", "confused", "shocked", "deadpan", "laugh"),
        expression_labels={
            "excited": "Antusias Roket!",
            "determined": "Fokus Insinyur",
            "confused": "Bingung (o_O)",
            "shocked": "Syok Berat",
            "deadpan": "Kecewa Datar",
            "laugh": "Tawa Lepas",
        },
        palette=(
            ("Helm Kuning", "#F2B724"),
            ("Overall Denim", "#2D4F7E"),
            ("Kemeja Oranye", "#DE642B"),
            ("Goggles Cyan", "#44C4D8"),
            ("Blueprint Biru", "#2378C4"),
        ),
        props_summary="Blueprint 'Lift Roket Turbo' + Kunci Inggris Baja",
        comedy_hook="Helm proyek terangkat saat syok & kecewa berat ketika roketnya ditolak",
    ),
}

CAST_ORDER = ("raka", "bima", "doni", "clara")


def _draw_grounded_legs(
    svg: SvgBuilder,
    hip_l: Point,
    hip_r: Point,
    ankle_l: Point,
    ankle_r: Point,
    thigh_len: float,
    shin_len: float,
    shoe_color: str,
    sole_color: str,
    shoe_style: str,
    shoe_scale: float = 1.0,
) -> str:
    """Solve 2-bone IK for both legs with subtle natural knee stance and grounded 3D shoes."""
    # Auto-fit bone lengths to stance distance + tiny relaxed bend so standing legs look crisp, never bow-legged
    dl = math.hypot(ankle_l[0] - hip_l[0], ankle_l[1] - hip_l[1])
    dr = math.hypot(ankle_r[0] - hip_r[0], ankle_r[1] - hip_r[1])
    t_l = max(thigh_len, dl * 0.506)
    s_l = max(shin_len, dl * 0.506)
    if t_l + s_l > dl + 2.2:
        ratio = (dl + 1.8) / (t_l + s_l)
        t_l *= ratio
        s_l *= ratio
    t_r = max(thigh_len, dr * 0.506)
    s_r = max(shin_len, dr * 0.506)
    if t_r + s_r > dr + 2.2:
        ratio = (dr + 1.8) / (t_r + s_r)
        t_r *= ratio
        s_r *= ratio

    knee_l, end_l = solve_2bone_ik(hip_l, ankle_l, t_l, s_l, bend_dir=+1.0)
    knee_r, end_r = solve_2bone_ik(hip_r, ankle_r, t_r, s_r, bend_dir=-1.0)

    parts = [
        draw_stick_limb(svg, hip_l, knee_l, end_l, w_start=14.5, w_end=11.0, bend_softness=0.22),
        draw_stick_limb(svg, hip_r, knee_r, end_r, w_start=14.5, w_end=11.0, bend_softness=0.22),
        draw_shoe(svg, end_l, facing=-1.0, color=shoe_color, sole_color=sole_color, style=shoe_style, scale=shoe_scale),
        draw_shoe(svg, end_r, facing=+1.0, color=shoe_color, sole_color=sole_color, style=shoe_style, scale=shoe_scale),
    ]
    return "<g>" + "".join(parts) + "</g>"


def _draw_capsule_volume_overlay(svg: SvgBuilder, clip_id: str, cx: float, top_y: float, w: float, h: float) -> str:
    """Unified directional lighting overlay clipped to the pill torso: top-left specular & warm bottom-right rim bounce."""
    # Soft key highlight on upper-left cheek/shoulder (fades to transparent of SAME warm-white hue)
    hi_g = svg.add_radial_gradient(
        [(0.0, "#FFF9E8", 0.34), (0.65, "#FFF9E8", 0.08), (1.0, "#FFF9E8", 0.0)],
        cx=0.28,
        cy=0.22,
        r=0.58,
    )
    # Core shadow band on right side (fades to transparent of SAME deep navy-plum shadow hue)
    sh_g = svg.add_linear_gradient(
        [
            (0.0, "#1A1530", 0.0),
            (0.58, "#1A1530", 0.0),
            (0.84, "#1A1530", 0.24),
            (0.95, "#1A1530", 0.32),
            (1.0, "#E8B064", 0.14),  # subtle warm golden lobby bounce on far shadowed rim!
        ],
        x1=0.0,
        y1=0.1,
        x2=1.0,
        y2=0.45,
    )
    return (
        f'<g clip-path="{clip_id}">'
        f'<rect x="{fmt(cx - w * 0.65)}" y="{fmt(top_y - 10)}" width="{fmt(w * 1.3)}" height="{fmt(h + 20)}" fill="{hi_g}"/>'
        f'<rect x="{fmt(cx - w * 0.65)}" y="{fmt(top_y - 10)}" width="{fmt(w * 1.3)}" height="{fmt(h + 20)}" fill="{sh_g}"/>'
        f"</g>"
    )


# ==============================================================================
# 1. RAKA — Psikolog Perilaku Santai (Tall, Sleek Pill + Mustard Knit Scarf)
# ==============================================================================

def _raka_headwear_and_hair(svg: SvgBuilder, top_y: float, head_w: float) -> Tuple[str, str]:
    """Return (back_hair_svg, front_hair_and_glasses_svg) for Raka."""
    hair_base = "#2E1E16"
    hair_grad = svg.add_linear_gradient(
        [(0.0, "#593D2E", 1.0), (0.45, hair_base, 1.0), (1.0, "#170F0B", 1.0)],
        x1=0.15,
        y1=0.0,
        x2=0.85,
        y2=1.0,
    )
    # Back silhouette of wavy hair
    back = (
        f'<path d="M -68,{fmt(top_y + 42)} C -82,{fmt(top_y + 8)} -64,{fmt(top_y - 38)} -16,{fmt(top_y - 44)} '
        f'C 30,{fmt(top_y - 48)} 78,{fmt(top_y - 14)} 72,{fmt(top_y + 40)} Z" '
        f'fill="{hair_grad}" stroke="{INK_COLOR}" stroke-width="5.2" stroke-linejoin="round"/>'
    )
    # Layered wavy foreground fringe casting contoured shadow on forehead
    front_hair = (
        # Contoured cast shadow hugging wavy fringe
        f'<path d="M -56,{fmt(top_y + 34)} C -44,{fmt(top_y + 24)} -32,{fmt(top_y + 34)} -16,{fmt(top_y + 36)} '
        f'C 6,{fmt(top_y + 38)} 20,{fmt(top_y + 22)} 34,{fmt(top_y + 30)} C 45,{fmt(top_y + 24)} 52,{fmt(top_y + 30)} 58,{fmt(top_y + 42)} '
        f'L 58,{fmt(top_y + 18)} L -58,{fmt(top_y + 18)} Z" fill="#A66D4E" opacity="0.22"/>'
        # Sculpted wavy hair crown + sweeping bangs (lifted slightly for crisp eyebrow breathing room)
        f'<path d="M -64,{fmt(top_y + 44)} C -69,{fmt(top_y + 6)} -54,{fmt(top_y - 38)} -10,{fmt(top_y - 46)} '
        f'C 12,{fmt(top_y - 50)} 34,{fmt(top_y - 44)} 48,{fmt(top_y - 28)} '
        f'C 66,{fmt(top_y - 24)} 74,{fmt(top_y + 10)} 64,{fmt(top_y + 44)} '
        f'C 55,{fmt(top_y + 22)} 44,{fmt(top_y + 14)} 32,{fmt(top_y + 23)} '
        f'C 18,{fmt(top_y + 12)} -2,{fmt(top_y + 30)} -24,{fmt(top_y + 26)} '
        f'C -40,{fmt(top_y + 22)} -52,{fmt(top_y + 24)} -64,{fmt(top_y + 44)} Z" '
        f'fill="{hair_grad}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
        # Glossy hair highlight ribbons (consistent top-left light)
        f'<path d="M -38,{fmt(top_y - 20)} Q -14,{fmt(top_y - 36)} 14,{fmt(top_y - 28)}" '
        f'fill="none" stroke="#7A5643" stroke-width="5.5" stroke-linecap="round" opacity="0.72"/>'
        f'<path d="M -46,{fmt(top_y)} Q -26,{fmt(top_y - 12)} -4,{fmt(top_y - 6)}" '
        f'fill="none" stroke="#7A5643" stroke-width="3.6" stroke-linecap="round" opacity="0.55"/>'
    )
    return back, front_hair


def _raka_glasses(svg: SvgBuilder, face_cy: float) -> str:
    """Thin round brass spectacles with subtle tinted glass & diagonal specular glints."""
    ey = face_cy - 4.0
    lens_g = svg.add_linear_gradient(
        [(0.0, "#FFFFFF", 0.28), (0.5, "#D9F0FF", 0.08), (1.0, "#FFFFFF", 0.0)],
        0.0,
        0.0,
        1.0,
        1.0,
    )
    brass = "#D9A436"
    return (
        f'<g>'
        # Subtle cast shadow below lens frames
        f'<ellipse cx="-21" cy="{fmt(ey + 5)}" rx="18" ry="17" fill="none" stroke="#A66D4E" stroke-width="3.0" opacity="0.22"/>'
        f'<ellipse cx="21" cy="{fmt(ey + 5)}" rx="18" ry="17" fill="none" stroke="#A66D4E" stroke-width="3.0" opacity="0.22"/>'
        # Glass lenses
        f'<circle cx="-21" cy="{fmt(ey)}" r="18.5" fill="{lens_g}"/>'
        f'<circle cx="21" cy="{fmt(ey)}" r="18.5" fill="{lens_g}"/>'
        # Diagonal lens glints
        f'<line x1="-30" y1="{fmt(ey - 8)}" x2="-19" y2="{fmt(ey - 13)}" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" opacity="0.78"/>'
        f'<line x1="12" y1="{fmt(ey - 8)}" x2="23" y2="{fmt(ey - 13)}" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" opacity="0.78"/>'
        # Outer dark ink rim + warm brass wire rim
        f'<circle cx="-21" cy="{fmt(ey)}" r="18.5" fill="none" stroke="{INK_COLOR}" stroke-width="5.2"/>'
        f'<circle cx="21" cy="{fmt(ey)}" r="18.5" fill="none" stroke="{INK_COLOR}" stroke-width="5.2"/>'
        f'<circle cx="-21" cy="{fmt(ey)}" r="18.5" fill="none" stroke="{brass}" stroke-width="2.6"/>'
        f'<circle cx="21" cy="{fmt(ey)}" r="18.5" fill="none" stroke="{brass}" stroke-width="2.6"/>'
        # Nose bridge & temple arms
        f'<path d="M -2.5,{fmt(ey - 1)} Q 0,{fmt(ey - 5)} 2.5,{fmt(ey - 1)}" fill="none" stroke="{INK_COLOR}" stroke-width="4.4"/>'
        f'<path d="M -2.5,{fmt(ey - 1)} Q 0,{fmt(ey - 5)} 2.5,{fmt(ey - 1)}" fill="none" stroke="{brass}" stroke-width="2.2"/>'
        f'<line x1="-39.5" y1="{fmt(ey - 2)}" x2="-60" y2="{fmt(ey - 6)}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linecap="round"/>'
        f'<line x1="39.5" y1="{fmt(ey - 2)}" x2="60" y2="{fmt(ey - 6)}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linecap="round"/>'
        f"</g>"
    )


def _raka_scarf(svg: SvgBuilder, neck_y: float) -> str:
    """Chunky 3D-layered mustard knit scarf wrapping around Raka's cylindrical neck with hanging fringed tail."""
    scarf_g = svg.add_cylindrical_gradient("#E8A825", lit_shift=0.25, shadow_shift=0.35, bounce_color="#FFE082")
    tail_g = svg.add_linear_gradient(
        [(0.0, "#F5BE42", 1.0), (0.6, "#D9951A", 1.0), (1.0, "#A66A0C", 1.0)],
        0.0,
        0.0,
        1.0,
        1.0,
    )
    rib_col = "#B37412"
    return (
        f'<g>'
        # Cast shadow on chest beneath scarf & tail
        f'<path d="M -68,{fmt(neck_y + 14)} Q 0,{fmt(neck_y + 34)} 68,{fmt(neck_y + 14)} '
        f'L 66,{fmt(neck_y + 24)} Q 0,{fmt(neck_y + 44)} -66,{fmt(neck_y + 24)} Z" fill="#182C26" opacity="0.30"/>'
        # Hanging fringed scarf tail swaying slightly to viewer-left
        f'<path d="M -42,{fmt(neck_y + 10)} Q -56,{fmt(neck_y + 52)} -46,{fmt(neck_y + 84)} '
        f'L -18,{fmt(neck_y + 82)} Q -26,{fmt(neck_y + 48)} -16,{fmt(neck_y + 12)} Z" '
        f'fill="{tail_g}" stroke="{INK_COLOR}" stroke-width="3.8" stroke-linejoin="round"/>'
        # Knit stripes & fringe on scarf tail
        f'<path d="M -47,{fmt(neck_y + 66)} Q -34,{fmt(neck_y + 69)} -21,{fmt(neck_y + 65)}" '
        f'fill="none" stroke="#C44B27" stroke-width="4.5"/>'
        f'<line x1="-43" y1="{fmt(neck_y + 83)}" x2="-45" y2="{fmt(neck_y + 96)}" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linecap="round"/>'
        f'<line x1="-35" y1="{fmt(neck_y + 83)}" x2="-36" y2="{fmt(neck_y + 97)}" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linecap="round"/>'
        f'<line x1="-27" y1="{fmt(neck_y + 83)}" x2="-27" y2="{fmt(neck_y + 96)}" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linecap="round"/>'
        f'<line x1="-20" y1="{fmt(neck_y + 82)}" x2="-19" y2="{fmt(neck_y + 94)}" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linecap="round"/>'
        # Main wrapped scarf torus hugging curved pill contour
        f'<path d="M -69,{fmt(neck_y - 10)} Q 0,{fmt(neck_y + 8)} 69,{fmt(neck_y - 10)} '
        f'Q 77,{fmt(neck_y + 6)} 68,{fmt(neck_y + 20)} Q 0,{fmt(neck_y + 38)} -68,{fmt(neck_y + 20)} '
        f'Q -77,{fmt(neck_y + 6)} -69,{fmt(neck_y - 10)} Z" '
        f'fill="{scarf_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
        # Overlapping upper fold line & curved knit rib texture
        f'<path d="M -52,{fmt(neck_y + 2)} Q 2,{fmt(neck_y + 18)} 56,{fmt(neck_y + 4)}" '
        f'fill="none" stroke="{rib_col}" stroke-width="2.6" stroke-linecap="round" opacity="0.65"/>'
        f'<path d="M -38,{fmt(neck_y - 2)} Q -41,{fmt(neck_y + 12)} -36,{fmt(neck_y + 24)}" fill="none" stroke="{rib_col}" stroke-width="2.2" opacity="0.55"/>'
        f'<path d="M -8,{fmt(neck_y + 3)} Q -10,{fmt(neck_y + 16)} -6,{fmt(neck_y + 28)}" fill="none" stroke="{rib_col}" stroke-width="2.2" opacity="0.55"/>'
        f'<path d="M 24,{fmt(neck_y + 1)} Q 22,{fmt(neck_y + 14)} 26,{fmt(neck_y + 26)}" fill="none" stroke="{rib_col}" stroke-width="2.2" opacity="0.55"/>'
        f'<path d="M 48,{fmt(neck_y - 3)} Q 46,{fmt(neck_y + 9)} 49,{fmt(neck_y + 20)}" fill="none" stroke="{rib_col}" stroke-width="2.2" opacity="0.55"/>'
        # Crisp top-left knit highlight
        f'<path d="M -56,{fmt(neck_y - 3)} Q -26,{fmt(neck_y + 5)} 4,{fmt(neck_y + 5)}" '
        f'fill="none" stroke="#FFF1B8" stroke-width="3.2" stroke-linecap="round" opacity="0.65"/>'
        f"</g>"
    )


def draw_raka(
    svg: SvgBuilder,
    expression: str = "chill",
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    """Build Raka (Tall Chill Behavioral Psychologist) grounded at (cx, floor_y)."""
    skin = "#FAD6B4"
    blazer = "#3E6E5F"
    turtleneck = "#F5EBD6"
    pants = "#2B343B"
    top_y = -402.0
    pill_h = 304.0
    face_cy = -322.0
    neck_y = -270.0

    pts = sample_rounded_capsule(0.0, top_y, w_top=128.0, w_mid=144.0, w_bot=132.0, height=pill_h, dome_ratio=0.25, bot_ratio=0.20)
    pill_d = pts_to_path(pts, closed=True)
    pill_clip = svg.add_clip_path(f'<path d="{pill_d}"/>')

    skin_g = svg.add_cylindrical_gradient(skin, lit_shift=0.16, shadow_shift=0.20, bounce_color="#F7C28E")
    blazer_g = svg.add_cylindrical_gradient(blazer, lit_shift=0.20, shadow_shift=0.36, bounce_color="#E8B968")
    lapel_g = svg.add_linear_gradient([(0.0, lighten(blazer, 0.24), 1.0), (1.0, darken(blazer, 0.22), 1.0)], 0, 0, 1, 1)
    knit_g = svg.add_cylindrical_gradient(turtleneck, lit_shift=0.14, shadow_shift=0.22)
    pants_g = svg.add_cylindrical_gradient(pants, lit_shift=0.18, shadow_shift=0.32)

    # Legs (2-Bone IK grounded cleanly at y = 0)
    legs_svg = _draw_grounded_legs(
        svg,
        hip_l=(-26.0, -110.0),
        hip_r=(26.0, -110.0),
        ankle_l=(-30.0, -19.5),
        ankle_r=(32.0, -19.5),
        thigh_len=48.0,
        shin_len=47.0,
        shoe_color="#6E442B",
        sole_color="#261812",
        shoe_style="loafer",
        shoe_scale=1.02,
    )

    # Arms (2-Bone IK with natural downward elbow flexion & clavicle follow)
    sh_l = clavicle_follow((-64.0, -236.0), (-124.0, -214.0), 0.12)
    el_l, hand_l = solve_2bone_ik(sh_l, (-124.0, -214.0), 50.0, 48.0, bend_dir=-1.0)
    sh_r = clavicle_follow((64.0, -236.0), (124.0, -234.0), 0.12)
    el_r, hand_r = solve_2bone_ik(sh_r, (124.0, -234.0), 50.0, 48.0, bend_dir=+1.0)

    back_hair, front_hair = _raka_headwear_and_hair(svg, top_y, 128.0)

    parts = [f'<g transform="translate({fmt(cx)},{fmt(floor_y)}) scale({fmt(scale)})">']
    parts.append(legs_svg)
    parts.append(back_hair)

    # Arms behind/beside body
    parts.append(draw_stick_limb(svg, sh_l, el_l, hand_l, w_start=13.5, w_end=10.5))
    parts.append(draw_stick_limb(svg, sh_r, el_r, hand_r, w_start=13.5, w_end=10.5))

    # Base pill skin fill
    parts.append(f'<path d="{pill_d}" fill="{skin_g}"/>')

    # Clipped 3D Outfit Layers inside the pill contour
    parts.append(f'<g clip-path="{pill_clip}">')
    # Lower trousers hem sealing bottom dome cleanly
    parts.append(f'<path d="M -85,-138 Q 0,-124 85,-138 L 85,-80 L -85,-80 Z" fill="{pants_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>')
    # Olive blazer torso wrapping cleanly around cylindrical pill
    parts.append(
        f'<path d="M -86,{fmt(neck_y + 4)} Q 0,{fmt(neck_y + 18)} 86,{fmt(neck_y + 4)} '
        f'L 86,-132 Q 0,-118 -86,-132 Z" fill="{blazer_g}"/>'
    )
    # Corduroy vertical subtle texture lines
    for x_rib in (-48, -32, 32, 48):
        parts.append(
            f'<line x1="{x_rib}" y1="{fmt(neck_y + 24)}" x2="{x_rib}" y2="-130" '
            f'stroke="{darken(blazer, 0.28)}" stroke-width="1.8" opacity="0.32"/>'
        )
    # Cream turtleneck center V-panel
    parts.append(
        f'<path d="M -30,{fmt(neck_y + 4)} L 30,{fmt(neck_y + 4)} L 20,-130 Q 0,-124 -20,-130 Z" '
        f'fill="{knit_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
    )
    # Curved notched blazer lapels (left & right) with cast shadow underneath
    parts.append(
        f'<path d="M -34,{fmt(neck_y + 8)} L -52,-216 L -38,-212 L -46,-196 L -20,-130 L -15,-130 L -24,{fmt(neck_y + 8)} Z" '
        f'fill="#1B332B" opacity="0.28"/>'
    )
    parts.append(
        f'<path d="M -32,{fmt(neck_y + 4)} L -56,-218 L -40,-213 L -48,-196 L -20,-130 L -22,{fmt(neck_y + 4)} Z" '
        f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
    )
    parts.append(
        f'<path d="M 32,{fmt(neck_y + 4)} L 56,-218 L 40,-213 L 48,-196 L 20,-130 L 22,{fmt(neck_y + 4)} Z" '
        f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
    )
    # Breast pocket + peeking tan psychologist notebook + brass lapel pin on visible right lapel
    parts.append(
        f'<rect x="27" y="-218" width="20" height="14" rx="2" transform="rotate(6 37 -211)" '
        f'fill="#E8C987" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        f'<path d="M 24,-207 Q 38,-204 52,-208 L 51,-192 Q 38,-189 25,-192 Z" '
        f'fill="{lighten(blazer, 0.08)}" stroke="{INK_COLOR}" stroke-width="2.6" stroke-linejoin="round"/>'
        f'<circle cx="42" cy="-224" r="4.6" fill="#F0C24B" stroke="{INK_COLOR}" stroke-width="2.0"/>'
    )
    # Lower stitched jacket pockets & bottom hem crease
    parts.append(
        f'<path d="M -62,-162 Q -46,-158 -31,-162 L -32,-142 Q -46,-139 -60,-142 Z" '
        f'fill="{darken(blazer, 0.14)}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<path d="M 31,-162 Q 46,-158 62,-162 L 60,-142 Q 46,-139 32,-142 Z" '
        f'fill="{darken(blazer, 0.14)}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<path d="M -80,-132 Q 0,-118 80,-132" fill="none" stroke="{INK_COLOR}" stroke-width="3.4"/>'
    )
    parts.append("</g>")

    # Unified 3D cylindrical volume lighting overlay inside capsule
    parts.append(_draw_capsule_volume_overlay(svg, pill_clip, 0.0, top_y, 148.0, pill_h))

    # Variable-width organic ink outline around the whole capsule body!
    parts.append(variable_ink_closed(pts, min_w=3.2, max_w=7.6))

    # Sleeve caps sealing shoulder sockets cleanly
    parts.append(draw_sleeve_cap(svg, sh_l, el_l, blazer, radius=14.5))
    parts.append(draw_sleeve_cap(svg, sh_r, el_r, blazer, radius=14.5))

    # Layered chunky 3D scarf wrapping OVER pill contour + hairline
    parts.append(_raka_scarf(svg, neck_y))
    parts.append(front_hair)

    # Swappable Face + Round Brass Glasses
    parts.append(draw_expression(svg, expression, 0.0, face_cy, skin_color=skin, brow_color="#2E1E16", scale=0.96))
    parts.append(_raka_glasses(svg, face_cy))

    # Handheld Props + Articulated Cartoon Hands
    if with_props:
        parts.append(draw_coffee_cup(svg, (hand_l[0] - 8, hand_l[1] - 4), angle_deg=-8.0, scale=0.95))
        parts.append(draw_hand(svg, hand_l, angle_deg=-15.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_gold_hand_mirror(svg, (hand_r[0] + 6, hand_r[1] - 18), angle_deg=14.0, scale=0.96))
        parts.append(draw_hand(svg, hand_r, angle_deg=15.0, skin_color=skin, pose="grip"))
    else:
        # Clean gripping hands ready to hold real 3D Art Deco Blender props!
        parts.append(draw_hand(svg, hand_l, angle_deg=-15.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_hand(svg, hand_r, angle_deg=15.0, skin_color=skin, pose="grip"))

    parts.append("</g>")
    return "".join(parts)


# ==============================================================================
# 2. PAK BIMA — Manajer Gedung Panik (Broad Art Deco Suit + Flying Crimson Tie)
# ==============================================================================

def _bima_hair(svg: SvgBuilder, top_y: float) -> Tuple[str, str]:
    hair_col = "#343A4A"
    hair_g = svg.add_linear_gradient([(0.0, "#5C657D", 1.0), (0.5, hair_col, 1.0), (1.0, "#1C202B", 1.0)], 0.1, 0, 0.9, 1)
    # Two springy stress cowlick strands popping up from crown
    back = (
        f'<path d="M -12,{fmt(top_y + 4)} Q -26,{fmt(top_y - 36)} -4,{fmt(top_y - 46)} '
        f'Q -6,{fmt(top_y - 26)} 8,{fmt(top_y - 10)} Z" fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        f'<path d="M 4,{fmt(top_y + 4)} Q 16,{fmt(top_y - 38)} 34,{fmt(top_y - 34)} '
        f'Q 18,{fmt(top_y - 18)} 22,{fmt(top_y - 2)} Z" fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
    )
    front = (
        # Contoured cast shadow hugging wavy executive hairline
        f'<path d="M -60,{fmt(top_y + 42)} C -50,{fmt(top_y + 24)} -38,{fmt(top_y + 26)} -24,{fmt(top_y + 32)} '
        f'C -14,{fmt(top_y + 20)} -2,{fmt(top_y + 22)} 14,{fmt(top_y + 31)} '
        f'C 36,{fmt(top_y + 25)} 52,{fmt(top_y + 30)} 60,{fmt(top_y + 42)} '
        f'L 58,{fmt(top_y + 12)} L -58,{fmt(top_y + 12)} Z" fill="#A67456" opacity="0.22"/>'
        # Neat-turned-frazzled side-parted executive hair
        f'<path d="M -65,{fmt(top_y + 48)} C -70,{fmt(top_y + 4)} -52,{fmt(top_y - 24)} 0,{fmt(top_y - 24)} '
        f'C 52,{fmt(top_y - 24)} 70,{fmt(top_y + 4)} 65,{fmt(top_y + 48)} '
        f'C 55,{fmt(top_y + 26)} 36,{fmt(top_y + 18)} 14,{fmt(top_y + 24)} '
        f'C -4,{fmt(top_y + 14)} -16,{fmt(top_y + 12)} -24,{fmt(top_y + 26)} '
        f'C -40,{fmt(top_y + 18)} -54,{fmt(top_y + 26)} -65,{fmt(top_y + 48)} Z" '
        f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
        # Silver-grey executive temple streaks + top specular
        f'<path d="M -42,{fmt(top_y - 8)} Q -12,{fmt(top_y - 20)} 22,{fmt(top_y - 14)}" '
        f'fill="none" stroke="#8C96B0" stroke-width="4.6" stroke-linecap="round" opacity="0.65"/>'
        f'<path d="M -62,{fmt(top_y + 30)} Q -58,{fmt(top_y + 18)} -50,{fmt(top_y + 18)}" '
        f'fill="none" stroke="#B4BED6" stroke-width="3.2" stroke-linecap="round" opacity="0.65"/>'
        f'<path d="M 62,{fmt(top_y + 30)} Q 58,{fmt(top_y + 18)} 50,{fmt(top_y + 18)}" '
        f'fill="none" stroke="#B4BED6" stroke-width="3.2" stroke-linecap="round" opacity="0.65"/>'
    )
    return back, front


def draw_bima(
    svg: SvgBuilder,
    expression: str = "panic",
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    """Build Pak Bima (Panicked Art Deco Building Manager) grounded at (cx, floor_y)."""
    skin = "#F7CEA8"
    suit = "#22375C"
    vest = "#DFC387"
    shirt = "#FAF7F0"
    tie = "#D93829"
    top_y = -384.0
    pill_h = 292.0
    face_cy = -306.0
    neck_y = -252.0

    pts = sample_rounded_capsule(0.0, top_y, w_top=134.0, w_mid=168.0, w_bot=150.0, height=pill_h, dome_ratio=0.25, bot_ratio=0.20)
    pill_d = pts_to_path(pts, closed=True)
    pill_clip = svg.add_clip_path(f'<path d="{pill_d}"/>')

    skin_g = svg.add_cylindrical_gradient(skin, lit_shift=0.15, shadow_shift=0.22, bounce_color="#F5BA84")
    suit_g = svg.add_cylindrical_gradient(suit, lit_shift=0.24, shadow_shift=0.38, bounce_color="#E8B86B")
    lapel_g = svg.add_linear_gradient([(0.0, lighten(suit, 0.24), 1.0), (1.0, darken(suit, 0.26), 1.0)], 0, 0, 1, 1)
    vest_g = svg.add_cylindrical_gradient(vest, lit_shift=0.18, shadow_shift=0.30)
    tie_g = svg.add_linear_gradient([(0.0, "#F55B4A", 1.0), (0.55, tie, 1.0), (1.0, "#8C1911", 1.0)], 0.1, 0, 0.9, 1)

    legs_svg = _draw_grounded_legs(
        svg,
        hip_l=(-30.0, -104.0),
        hip_r=(30.0, -104.0),
        ankle_l=(-38.0, -19.5),
        ankle_r=(38.0, -19.5),
        thigh_len=45.0,
        shin_len=44.0,
        shoe_color="#1E1D24",
        sole_color="#121116",
        shoe_style="oxford",
        shoe_scale=1.02,
    )

    sh_l = clavicle_follow((-73.0, -220.0), (-132.0, -214.0), 0.14)
    el_l, hand_l = solve_2bone_ik(sh_l, (-132.0, -214.0), 50.0, 48.0, bend_dir=-1.0)
    sh_r = clavicle_follow((73.0, -220.0), (124.0, -226.0), 0.14)
    el_r, hand_r = solve_2bone_ik(sh_r, (124.0, -226.0), 50.0, 48.0, bend_dir=+1.0)

    back_hair, front_hair = _bima_hair(svg, top_y)

    parts = [f'<g transform="translate({fmt(cx)},{fmt(floor_y)}) scale({fmt(scale)})">']
    parts.append(legs_svg)
    parts.append(back_hair)
    parts.append(draw_stick_limb(svg, sh_l, el_l, hand_l, w_start=14.0, w_end=11.0))
    parts.append(draw_stick_limb(svg, sh_r, el_r, hand_r, w_start=14.0, w_end=11.0))

    # Base capsule skin
    parts.append(f'<path d="{pill_d}" fill="{skin_g}"/>')

    # Clipped Art Deco Manager Suit inside pill contour
    parts.append(f'<g clip-path="{pill_clip}">')
    # Dark navy suit body wrapping torso + trousers with crisp shoulder-seam ink
    parts.append(
        f'<path d="M -95,{fmt(neck_y)} Q 0,{fmt(neck_y + 18)} 95,{fmt(neck_y)} '
        f'L 95,-80 L -95,-80 Z" fill="{suit_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
    )
    # Subtle Art Deco pinstripes
    for px in (-62, -48, -34, 34, 48, 62):
        parts.append(f'<line x1="{px}" y1="{fmt(neck_y + 10)}" x2="{px}" y2="-95" stroke="#4D6896" stroke-width="1.4" opacity="0.32"/>')
    # Champagne waistcoat center panel
    parts.append(
        f'<path d="M -36,{fmt(neck_y + 2)} L 36,{fmt(neck_y + 2)} L 32,-124 Q 0,-112 -32,-124 Z" '
        f'fill="{vest_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
    )
    # Crisp ivory shirt upper V
    parts.append(
        f'<path d="M -32,{fmt(neck_y - 2)} L 32,{fmt(neck_y - 2)} L 0,-188 Z" '
        f'fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
    )
    # Gold waistcoat buttons + draped brass pocket-watch chain (catenary!)
    for by in (-178, -158, -138):
        parts.append(f'<circle cx="0" cy="{by}" r="3.8" fill="#E8B844" stroke="{INK_COLOR}" stroke-width="1.8"/>')
    parts.append(
        f'<path d="M -26,-156 Q -12,-142 0,-154 Q 14,-142 27,-156" '
        f'fill="none" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linecap="round"/>'
        f'<path d="M -26,-156 Q -12,-142 0,-154 Q 14,-142 27,-156" '
        f'fill="none" stroke="#F5C954" stroke-width="2.2" stroke-linecap="round"/>'
    )
    # Wide Art Deco peaked lapels
    parts.append(
        f'<path d="M -34,{fmt(neck_y)} L -64,-214 L -44,-208 L -52,-192 L -26,-122 L -36,-122 L -42,{fmt(neck_y)} Z" '
        f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
    )
    parts.append(
        f'<path d="M 34,{fmt(neck_y)} L 64,-214 L 44,-208 L 52,-192 L 26,-122 L 36,-122 L 42,{fmt(neck_y)} Z" '
        f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
    )
    # Crimson pocket square + beveled gold MGR badge
    parts.append(
        f'<polygon points="34,-196 42,-208 48,-197 54,-205 58,-194" fill="#D93829" stroke="{INK_COLOR}" stroke-width="2.2" stroke-linejoin="round"/>'
        f'<line x1="31" y1="-195" x2="60" y2="-195" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linecap="round"/>'
        f'<rect x="-62" y="-194" width="24" height="12" rx="3" fill="#F0C24B" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        f'<line x1="-58" y1="-188" x2="-42" y2="-188" stroke="#6E470A" stroke-width="2.4" stroke-linecap="round"/>'
    )
    # Suit lower waist seam + belt line
    parts.append(
        f'<path d="M -88,-124 Q 0,-110 88,-124" fill="none" stroke="{INK_COLOR}" stroke-width="3.6"/>'
    )
    # Cast shadow under chin onto collar
    parts.append(
        f'<path d="M -46,{fmt(neck_y - 2)} Q 0,{fmt(neck_y + 18)} 46,{fmt(neck_y - 2)} '
        f'L 42,{fmt(neck_y + 12)} Q 0,{fmt(neck_y + 26)} -42,{fmt(neck_y + 12)} Z" fill="#2A1F18" opacity="0.22"/>'
    )
    # Pointed crisp white shirt collars
    parts.append(
        f'<polygon points="-36,{fmt(neck_y - 4)} 0,{fmt(neck_y + 8)} -18,{fmt(neck_y + 22)}" '
        f'fill="{shirt}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
        f'<polygon points="36,{fmt(neck_y - 4)} 0,{fmt(neck_y + 8)} 18,{fmt(neck_y + 22)}" '
        f'fill="{shirt}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
    )
    parts.append("</g>")

    # Unified 3D shading overlay + variable-width ink outline
    parts.append(_draw_capsule_volume_overlay(svg, pill_clip, 0.0, top_y, 170.0, pill_h))
    parts.append(variable_ink_closed(pts, min_w=3.2, max_w=7.8))

    # Dynamic crimson & gold striped tie flaring slightly outward (overlaps cleanly with spring energy!)
    tie_flare = 12.0 if expression in ("panic", "shocked", "stressed") else 4.0
    tie_clip = svg.add_clip_path(
        f'<path d="M -6,{fmt(neck_y + 16)} L 6,{fmt(neck_y + 16)} '
        f'Q {fmt(14 + tie_flare * 0.5)},-200 {fmt(14 + tie_flare)},-170 '
        f'L {fmt(tie_flare)},-155 L {fmt(-12 + tie_flare * 0.6)},-172 '
        f'Q {fmt(-9 + tie_flare * 0.3)},-202 -6,{fmt(neck_y + 16)} Z"/>'
    )
    parts.append(
        # Tie cast shadow
        f'<path d="M -4,{fmt(neck_y + 20)} L 9,{fmt(neck_y + 20)} '
        f'Q {fmt(18 + tie_flare * 0.5)},-198 {fmt(18 + tie_flare)},-168 '
        f'L {fmt(4 + tie_flare)},-152 L {fmt(-8 + tie_flare * 0.6)},-169 Z" fill="#181224" opacity="0.22"/>'
        f'<path d="M -6,{fmt(neck_y + 16)} L 6,{fmt(neck_y + 16)} '
        f'Q {fmt(14 + tie_flare * 0.5)},-200 {fmt(14 + tie_flare)},-170 '
        f'L {fmt(tie_flare)},-155 L {fmt(-12 + tie_flare * 0.6)},-172 '
        f'Q {fmt(-9 + tie_flare * 0.3)},-202 -6,{fmt(neck_y + 16)} Z" fill="{tie_g}"/>'
        f'<g clip-path="{tie_clip}">'
        f'<line x1="-18" y1="-224" x2="28" y2="-204" stroke="#F5C84B" stroke-width="4.2"/>'
        f'<line x1="-18" y1="-206" x2="30" y2="-186" stroke="#F5C84B" stroke-width="4.2"/>'
        f'<line x1="-16" y1="-188" x2="32" y2="-168" stroke="#F5C84B" stroke-width="4.2"/>'
        f"</g>"
        f'<path d="M -6,{fmt(neck_y + 16)} L 6,{fmt(neck_y + 16)} '
        f'Q {fmt(14 + tie_flare * 0.5)},-200 {fmt(14 + tie_flare)},-170 '
        f'L {fmt(tie_flare)},-155 L {fmt(-12 + tie_flare * 0.6)},-172 '
        f'Q {fmt(-9 + tie_flare * 0.3)},-202 -6,{fmt(neck_y + 16)} Z" fill="none" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linejoin="round"/>'
        # Windsor tie knot
        f'<path d="M -9,{fmt(neck_y + 6)} L 9,{fmt(neck_y + 6)} L 6,{fmt(neck_y + 20)} L -6,{fmt(neck_y + 20)} Z" '
        f'fill="{tie_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
    )

    # Sleeve caps
    parts.append(draw_sleeve_cap(svg, sh_l, el_l, suit, radius=15.5))
    parts.append(draw_sleeve_cap(svg, sh_r, el_r, suit, radius=15.5))

    parts.append(front_hair)
    parts.append(
        draw_expression(
            svg,
            expression,
            0.0,
            face_cy,
            skin_color=skin,
            brow_color="#343A4A",
            scale=0.96,
            has_mustache=True,
            mustache_color="#343A4A",
        )
    )

    if with_props:
        parts.append(draw_complaint_clipboard(svg, (hand_l[0] - 12, hand_l[1] - 18), angle_deg=-12.0, scale=0.96))
        parts.append(draw_hand(svg, hand_l, angle_deg=-20.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_red_pen(svg, (hand_r[0] + 6, hand_r[1] - 10), angle_deg=-35.0, scale=1.0))
        parts.append(draw_hand(svg, hand_r, angle_deg=-10.0, skin_color=skin, pose="grip"))
    else:
        parts.append(draw_hand(svg, hand_l, angle_deg=-20.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_hand(svg, hand_r, angle_deg=-10.0, skin_color=skin, pose="grip"))

    parts.append("</g>")
    return "".join(parts)


# ==============================================================================
# 3. PAK DONI — Penghuni Pemarah -> Narsis (Stocky Pill + Iconic 3D Pompadour!)
# ==============================================================================

def _doni_pompadour(svg: SvgBuilder, top_y: float) -> Tuple[str, str]:
    """Monumental glossy 3D pompadour wave — Pak Doni's comedic signature!"""
    hair_g = svg.add_linear_gradient(
        [(0.0, "#3D4663", 1.0), (0.38, "#1E2230", 1.0), (1.0, "#0F111A", 1.0)],
        x1=0.1,
        y1=0.0,
        x2=0.85,
        y2=1.0,
    )
    back = (
        f'<path d="M -68,{fmt(top_y + 42)} C -78,{fmt(top_y - 12)} -46,{fmt(top_y - 68)} 16,{fmt(top_y - 64)} '
        f'C 72,{fmt(top_y - 60)} 96,{fmt(top_y - 18)} 74,{fmt(top_y + 38)} Z" '
        f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="5.2" stroke-linejoin="round"/>'
    )
    front = (
        # Contoured cast shadow under sweeping pompadour overhang across forehead
        f'<path d="M -56,{fmt(top_y + 30)} C -30,{fmt(top_y + 36)} 12,{fmt(top_y + 36)} 38,{fmt(top_y + 22)} '
        f'C 48,{fmt(top_y + 22)} 54,{fmt(top_y + 28)} 58,{fmt(top_y + 38)} '
        f'L 58,{fmt(top_y + 8)} L -58,{fmt(top_y + 8)} Z" fill="#9E6548" opacity="0.24"/>'
        # Sculpted glossy pompadour crest curving dramatically upward & right!
        f'<path d="M -64,{fmt(top_y + 44)} C -76,{fmt(top_y - 4)} -54,{fmt(top_y - 60)} 8,{fmt(top_y - 64)} '
        f'C 58,{fmt(top_y - 66)} 94,{fmt(top_y - 38)} 88,{fmt(top_y - 8)} '
        f'C 84,{fmt(top_y + 14)} 68,{fmt(top_y + 22)} 64,{fmt(top_y + 44)} '
        f'C 54,{fmt(top_y + 24)} 48,{fmt(top_y + 14)} 36,{fmt(top_y + 14)} '
        f'C 10,{fmt(top_y + 28)} -32,{fmt(top_y + 28)} -54,{fmt(top_y + 22)} '
        f'C -58,{fmt(top_y + 30)} -60,{fmt(top_y + 38)} -64,{fmt(top_y + 44)} Z" '
        f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
        # Inner spiral curl line of the pompadour wave
        f'<path d="M 54,{fmt(top_y - 26)} C 72,{fmt(top_y - 26)} 76,{fmt(top_y - 4)} 56,{fmt(top_y + 2)} '
        f'C 42,{fmt(top_y + 6)} 32,{fmt(top_y - 4)} 42,{fmt(top_y - 14)}" '
        f'fill="none" stroke="#0C0D14" stroke-width="3.6" stroke-linecap="round"/>'
        # High-gloss pomade specular ribbons!
        f'<path d="M -38,{fmt(top_y - 26)} C -12,{fmt(top_y - 52)} 34,{fmt(top_y - 54)} 64,{fmt(top_y - 36)}" '
        f'fill="none" stroke="#7A8BB8" stroke-width="6.4" stroke-linecap="round" opacity="0.72"/>'
        f'<path d="M -26,{fmt(top_y - 24)} C -4,{fmt(top_y - 44)} 26,{fmt(top_y - 46)} 46,{fmt(top_y - 36)}" '
        f'fill="none" stroke="#E4EEFF" stroke-width="2.6" stroke-linecap="round" opacity="0.78"/>'
        # Crisp sideburns
        f'<path d="M -64,{fmt(top_y + 40)} L -62,{fmt(top_y + 64)} L -54,{fmt(top_y + 56)} Z" fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<path d="M 64,{fmt(top_y + 40)} L 62,{fmt(top_y + 64)} L 54,{fmt(top_y + 56)} Z" fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
    )
    return back, front


def draw_doni(
    svg: SvgBuilder,
    expression: str = "furious",
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    """Build Pak Doni (Compact Impatient Commuter Turned Mirror-Obsessed) grounded at (cx, floor_y)."""
    skin = "#F6C8A2"
    vest = "#8E2436"
    shirt = "#EAF2FA"
    slacks = "#2E3340"
    top_y = -336.0
    pill_h = 260.0
    face_cy = -264.0
    neck_y = -212.0

    pts = sample_rounded_capsule(0.0, top_y, w_top=132.0, w_mid=162.0, w_bot=152.0, height=pill_h, dome_ratio=0.27, bot_ratio=0.22)
    pill_d = pts_to_path(pts, closed=True)
    pill_clip = svg.add_clip_path(f'<path d="{pill_d}"/>')

    skin_g = svg.add_cylindrical_gradient(skin, lit_shift=0.16, shadow_shift=0.22, bounce_color="#F5B582")
    vest_g = svg.add_cylindrical_gradient(vest, lit_shift=0.22, shadow_shift=0.36, bounce_color="#F2B872")
    shirt_g = svg.add_cylindrical_gradient(shirt, lit_shift=0.10, shadow_shift=0.18)
    slacks_g = svg.add_cylindrical_gradient(slacks, lit_shift=0.18, shadow_shift=0.34)
    buckle_g = svg.add_linear_gradient([(0.0, "#FFF0A6", 1.0), (0.5, "#E3B034", 1.0), (1.0, "#996814", 1.0)], 0, 0, 1, 1)

    legs_svg = _draw_grounded_legs(
        svg,
        hip_l=(-30.0, -88.0),
        hip_r=(30.0, -88.0),
        ankle_l=(-35.0, -19.5),
        ankle_r=(35.0, -19.5),
        thigh_len=38.0,
        shin_len=36.0,
        shoe_color="#3B2014",
        sole_color="#1A0E08",
        shoe_style="oxford",
        shoe_scale=0.98,
    )

    # Left arm raised with natural downward elbow displaying gold wristwatch on wrist + comb cleanly angled up;
    # right arm hangs naturally holding leather briefcase!
    sh_l = clavicle_follow((-70.0, -184.0), (-124.0, -206.0), 0.14)
    el_l, hand_l = solve_2bone_ik(sh_l, (-124.0, -206.0), 48.0, 48.0, bend_dir=-1.0)
    sh_r = clavicle_follow((70.0, -184.0), (114.0, -124.0), 0.12)
    el_r, hand_r = solve_2bone_ik(sh_r, (114.0, -124.0), 44.0, 42.0, bend_dir=-1.0)

    back_hair, front_hair = _doni_pompadour(svg, top_y)

    parts = [f'<g transform="translate({fmt(cx)},{fmt(floor_y)}) scale({fmt(scale)})">']
    parts.append(legs_svg)
    parts.append(back_hair)
    parts.append(draw_stick_limb(svg, sh_l, el_l, hand_l, w_start=14.0, w_end=11.0))
    parts.append(draw_stick_limb(svg, sh_r, el_r, hand_r, w_start=14.0, w_end=11.0))

    # Base pill skin
    parts.append(f'<path d="{pill_d}" fill="{skin_g}"/>')

    # Clipped Outfit inside capsule
    parts.append(f'<g clip-path="{pill_clip}">')
    # Charcoal slacks sealing lower pill
    parts.append(f'<path d="M -90,-114 Q 0,-100 90,-114 L 90,-65 L -90,-65 Z" fill="{slacks_g}"/>')
    # Burgundy V-neck knit vest wrapping cleanly with crisp shoulder-seam ink
    parts.append(
        f'<path d="M -90,{fmt(neck_y)} Q 0,{fmt(neck_y + 14)} 90,{fmt(neck_y)} '
        f'L 90,-118 Q 0,-104 -90,-118 Z" fill="{vest_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
    )
    # Subtle argyle diamond pattern curving across chest
    for ax in (-44, 0, 44):
        parts.append(
            f'<polygon points="{ax},-174 {ax + 16},-152 {ax},-130 {ax - 16},-152" '
            f'fill="#B5384B" opacity="0.34"/>'
            f'<polygon points="{ax},-174 {ax + 16},-152 {ax},-130 {ax - 16},-152" '
            f'fill="none" stroke="#F0C674" stroke-width="1.3" opacity="0.45"/>'
        )
    # Ribbed vest bottom hem
    parts.append(
        f'<path d="M -88,-126 Q 0,-112 88,-126 L 88,-115 Q 0,-101 -88,-115 Z" '
        f'fill="{darken(vest, 0.24)}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
    )
    # Leather belt + beveled gold buckle right beneath vest hem
    parts.append(
        f'<path d="M -86,-116 Q 0,-102 86,-116 L 86,-104 Q 0,-90 -86,-104 Z" '
        f'fill="#3D2114" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        f'<rect x="-12" y="-110" width="24" height="14" rx="3" fill="{buckle_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<rect x="-5" y="-106" width="10" height="6" rx="1.5" fill="#3D2114"/>'
    )
    # Crisp light-sky dress shirt V-neck inset + neat charcoal tie
    parts.append(
        f'<path d="M -38,{fmt(neck_y - 2)} L 38,{fmt(neck_y - 2)} L 0,-156 Z" '
        f'fill="{shirt_g}" stroke="{darken(vest, 0.35)}" stroke-width="5.5" stroke-linejoin="round"/>'
        f'<path d="M -38,{fmt(neck_y - 2)} L 38,{fmt(neck_y - 2)} L 0,-156 Z" '
        f'fill="{shirt_g}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        # Neat slate tie tucked inside vest
        f'<polygon points="-5,{fmt(neck_y + 12)} 5,{fmt(neck_y + 12)} 8,-168 0,-158 -8,-168" '
        f'fill="#2F3B4D" stroke="{INK_COLOR}" stroke-width="2.6" stroke-linejoin="round"/>'
        f'<polygon points="-7,{fmt(neck_y + 4)} 7,{fmt(neck_y + 4)} 5,{fmt(neck_y + 15)} -5,{fmt(neck_y + 15)}" '
        f'fill="#41516B" stroke="{INK_COLOR}" stroke-width="2.4" stroke-linejoin="round"/>'
    )
    # Cast shadow under chin + folded white collar tips
    parts.append(
        f'<path d="M -42,{fmt(neck_y - 2)} Q 0,{fmt(neck_y + 14)} 42,{fmt(neck_y - 2)} '
        f'L 38,{fmt(neck_y + 10)} Q 0,{fmt(neck_y + 22)} -38,{fmt(neck_y + 10)} Z" fill="#2A1C16" opacity="0.22"/>'
        f'<polygon points="-36,{fmt(neck_y - 4)} 0,{fmt(neck_y + 6)} -18,{fmt(neck_y + 20)}" '
        f'fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        f'<polygon points="36,{fmt(neck_y - 4)} 0,{fmt(neck_y + 6)} 18,{fmt(neck_y + 20)}" '
        f'fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
    )
    parts.append("</g>")

    # 3D shading + variable-width ink outline
    parts.append(_draw_capsule_volume_overlay(svg, pill_clip, 0.0, top_y, 166.0, pill_h))
    parts.append(variable_ink_closed(pts, min_w=3.2, max_w=7.8))

    # Rolled sky-white shirt sleeves sealing shoulders cleanly!
    parts.append(draw_sleeve_cap(svg, sh_l, el_l, shirt, radius=15.0))
    parts.append(draw_sleeve_cap(svg, sh_r, el_r, shirt, radius=15.0))

    parts.append(front_hair)
    parts.append(draw_expression(svg, expression, 0.0, face_cy, skin_color=skin, brow_color="#1E2230", scale=0.95))

    if with_props:
        # Gleaming gold wristwatch strapped cleanly on forearm just below wrist (zero overlap with hand/comb!)
        wx = el_l[0] + (hand_l[0] - el_l[0]) * 0.66
        wy = el_l[1] + (hand_l[1] - el_l[1]) * 0.66
        forearm_ang = math.degrees(math.atan2(hand_l[1] - el_l[1], hand_l[0] - el_l[0]))
        parts.append(draw_gold_wristwatch(svg, (wx, wy), angle_deg=forearm_ang + 90.0, scale=1.06))
        # Tortoiseshell pocket comb held cleanly upward & clear of watch dial
        parts.append(draw_pocket_comb(svg, (hand_l[0] - 14, hand_l[1] - 18), angle_deg=-38.0, scale=0.94))
        parts.append(draw_hand(svg, hand_l, angle_deg=-25.0, skin_color=skin, pose="grip", flip_y=True))
        # Vintage saddle-leather briefcase hanging from viewer-right hand
        parts.append(draw_leather_briefcase(svg, (hand_r[0] + 4, hand_r[1] + 4), angle_deg=6.0, scale=0.94))
        parts.append(draw_hand(svg, hand_r, angle_deg=70.0, skin_color=skin, pose="grip"))
    else:
        parts.append(draw_hand(svg, hand_l, angle_deg=-25.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_hand(svg, hand_r, angle_deg=70.0, skin_color=skin, pose="grip"))

    parts.append("</g>")
    return "".join(parts)


# ==============================================================================
# 4. CLARA — Insinyur Lift Over-Engineered (Hard Hat + Goggles + Denim Overalls)
# ==============================================================================

def _clara_hair_and_hardhat(svg: SvgBuilder, top_y: float, helmet_pop: float = 0.0) -> Tuple[str, str]:
    """Domed 3D safety hard hat with strapped cyan goggles + full underlying chestnut hair & side ponytail!"""
    hair_col = "#6E3A24"
    hair_g = svg.add_linear_gradient([(0.0, "#9E5A3C", 1.0), (0.55, hair_col, 1.0), (1.0, "#3D1E11", 1.0)], 0.1, 0, 0.9, 1)
    hat_g = svg.add_radial_gradient(
        [(0.0, "#FFE484", 1.0), (0.45, "#F2B724", 1.0), (0.85, "#C78710", 1.0), (1.0, "#E3A729", 1.0)],
        cx=0.32,
        cy=0.28,
        r=0.72,
    )
    brim_g = svg.add_linear_gradient([(0.0, "#FFD86B", 1.0), (0.6, "#E3A419", 1.0), (1.0, "#A6700B", 1.0)], 0, 0, 1, 1)
    lens_g = svg.add_linear_gradient([(0.0, "#C7FAFF", 1.0), (0.5, "#44C4D8", 1.0), (1.0, "#1D7891", 1.0)], 0.1, 0, 0.9, 1)

    # Bouncy side ponytail behind head (visible even if helmet shifts!)
    back = (
        f'<g>'
        f'<path d="M 54,{fmt(top_y + 42)} C 84,{fmt(top_y + 26)} 104,{fmt(top_y + 58)} 88,{fmt(top_y + 92)} '
        f'C 80,{fmt(top_y + 104)} 68,{fmt(top_y + 94)} 70,{fmt(top_y + 80)} '
        f'C 72,{fmt(top_y + 68)} 62,{fmt(top_y + 62)} 50,{fmt(top_y + 58)} Z" '
        f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
        f'<path d="M 68,{fmt(top_y + 44)} Q 84,{fmt(top_y + 54)} 82,{fmt(top_y + 76)}" '
        f'fill="none" stroke="#B87352" stroke-width="3.6" stroke-linecap="round" opacity="0.65"/>'
        # Yellow hair band
        f'<ellipse cx="58" cy="{fmt(top_y + 50)}" rx="7" ry="11" transform="rotate(-18 58 {fmt(top_y + 50)})" '
        f'fill="#F2B724" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        f"</g>"
    )

    hy = top_y - helmet_pop
    front = (
        f'<g>'
        # UNDERLYING CHESTNUT BANGS (always complete beneath helmet!)
        f'<path d="M -62,{fmt(top_y + 50)} C -64,{fmt(top_y + 16)} -44,{fmt(top_y - 4)} 0,{fmt(top_y - 4)} '
        f'C 44,{fmt(top_y - 4)} 64,{fmt(top_y + 16)} 62,{fmt(top_y + 50)} '
        f'C 52,{fmt(top_y + 30)} 38,{fmt(top_y + 24)} 24,{fmt(top_y + 38)} '
        f'C 12,{fmt(top_y + 22)} -8,{fmt(top_y + 26)} -20,{fmt(top_y + 40)} '
        f'C -34,{fmt(top_y + 24)} -50,{fmt(top_y + 30)} -62,{fmt(top_y + 50)} Z" '
        f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linejoin="round"/>'
        # Cast shadow of helmet brim across forehead & bangs
        f'<path d="M -60,{fmt(top_y + 36)} Q 0,{fmt(top_y + 48)} 60,{fmt(top_y + 36)} '
        f'L 58,{fmt(top_y + 24)} Q 0,{fmt(top_y + 34)} -58,{fmt(top_y + 24)} Z" fill="#2A160B" opacity="0.30"/>'
        # DOMED 3D SAFETY HARD HAT (can lift subtly on shock beat!)
        f'<g transform="translate(0,{fmt(-helmet_pop)})">'
        # Domed crown
        f'<path d="M -68,{fmt(top_y + 20)} C -70,{fmt(top_y - 36)} -36,{fmt(top_y - 56)} 0,{fmt(top_y - 56)} '
        f'C 36,{fmt(top_y - 56)} 70,{fmt(top_y - 36)} 68,{fmt(top_y + 20)} Z" '
        f'fill="{hat_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
        # Center structural crest rib on helmet crown
        f'<path d="M -12,{fmt(top_y - 55)} L 12,{fmt(top_y - 55)} L 16,{fmt(top_y + 12)} L -16,{fmt(top_y + 12)} Z" '
        f'fill="{lighten("#F2B724", 0.16)}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
        # Helmet glossy specular highlight arc
        f'<path d="M -46,{fmt(top_y - 18)} Q -34,{fmt(top_y - 42)} -16,{fmt(top_y - 46)}" '
        f'fill="none" stroke="#FFF9D6" stroke-width="6.0" stroke-linecap="round" opacity="0.82"/>'
        # Goggle strap wrapping cleanly around dome
        f'<path d="M -68,{fmt(top_y + 6)} Q 0,{fmt(top_y + 16)} 68,{fmt(top_y + 6)} '
        f'L 68,{fmt(top_y - 5)} Q 0,{fmt(top_y + 5)} -68,{fmt(top_y - 5)} Z" '
        f'fill="#2F3847" stroke="{INK_COLOR}" stroke-width="3.0"/>'
        # Curved hard-hat brim/visor
        f'<path d="M -78,{fmt(top_y + 20)} Q 0,{fmt(top_y + 38)} 78,{fmt(top_y + 20)} '
        f'Q 74,{fmt(top_y + 8)} 64,{fmt(top_y + 12)} Q 0,{fmt(top_y + 25)} -64,{fmt(top_y + 12)} '
        f'Q -74,{fmt(top_y + 8)} -78,{fmt(top_y + 20)} Z" '
        f'fill="{brim_g}" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linejoin="round"/>'
        # Strapped protective cyan goggles resting on helmet front
        f'<rect x="-46" y="{fmt(top_y - 18)}" width="38" height="28" rx="13" fill="#525D6E" stroke="{INK_COLOR}" stroke-width="3.4"/>'
        f'<rect x="8" y="{fmt(top_y - 18)}" width="38" height="28" rx="13" fill="#525D6E" stroke="{INK_COLOR}" stroke-width="3.4"/>'
        f'<rect x="-40" y="{fmt(top_y - 13)}" width="26" height="18" rx="8" fill="{lens_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<rect x="14" y="{fmt(top_y - 13)}" width="26" height="18" rx="8" fill="{lens_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        # Goggle bridge + diagonal cyan glass reflections
        f'<rect x="-8" y="{fmt(top_y - 8)}" width="16" height="8" rx="3" fill="#3B4452" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<line x1="-34" y1="{fmt(top_y - 4)}" x2="-24" y2="{fmt(top_y - 10)}" stroke="#FFFFFF" stroke-width="3.0" stroke-linecap="round" opacity="0.85"/>'
        f'<line x1="20" y1="{fmt(top_y - 4)}" x2="30" y2="{fmt(top_y - 10)}" stroke="#FFFFFF" stroke-width="3.0" stroke-linecap="round" opacity="0.85"/>'
        + (
            f'<line x1="-38" y1="{fmt(top_y - 62)}" x2="-46" y2="{fmt(top_y - 74)}" stroke="#E85A2A" stroke-width="3.4" stroke-linecap="round"/>'
            f'<line x1="0" y1="{fmt(top_y - 66)}" x2="0" y2="{fmt(top_y - 80)}" stroke="#E85A2A" stroke-width="3.4" stroke-linecap="round"/>'
            f'<line x1="38" y1="{fmt(top_y - 62)}" x2="46" y2="{fmt(top_y - 74)}" stroke="#E85A2A" stroke-width="3.4" stroke-linecap="round"/>'
            if helmet_pop > 0.1
            else ""
        )
        + f"</g></g>"
    )
    return back, front


def draw_clara(
    svg: SvgBuilder,
    expression: str = "excited",
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    """Build Clara (Over-Ambitious Rocket-Lift Engineer) grounded at (cx, floor_y)."""
    skin = "#F9D5B5"
    shirt = "#DE642B"
    denim = "#2D4F7E"
    top_y = -356.0
    pill_h = 272.0
    face_cy = -280.0
    neck_y = -226.0

    pts = sample_rounded_capsule(0.0, top_y, w_top=124.0, w_mid=146.0, w_bot=142.0, height=pill_h, dome_ratio=0.26, bot_ratio=0.22)
    pill_d = pts_to_path(pts, closed=True)
    pill_clip = svg.add_clip_path(f'<path d="{pill_d}"/>')

    skin_g = svg.add_cylindrical_gradient(skin, lit_shift=0.16, shadow_shift=0.20, bounce_color="#F7BC88")
    shirt_g = svg.add_cylindrical_gradient(shirt, lit_shift=0.22, shadow_shift=0.34, bounce_color="#FFC57A")
    denim_g = svg.add_cylindrical_gradient(denim, lit_shift=0.22, shadow_shift=0.36, bounce_color="#E8B874")
    brass_g = svg.add_linear_gradient([(0.0, "#FFF2AD", 1.0), (0.5, "#E3B234", 1.0), (1.0, "#996A14", 1.0)], 0, 0, 1, 1)

    legs_svg = _draw_grounded_legs(
        svg,
        hip_l=(-27.0, -96.0),
        hip_r=(27.0, -96.0),
        ankle_l=(-34.0, -20.0),
        ankle_r=(34.0, -20.0),
        thigh_len=42.0,
        shin_len=41.0,
        shoe_color="#73411F",
        sole_color="#1C1410",
        shoe_style="boot",
        shoe_scale=1.02,
    )

    sh_l = clavicle_follow((-64.0, -198.0), (-120.0, -214.0), 0.14)
    el_l, hand_l = solve_2bone_ik(sh_l, (-120.0, -214.0), 48.0, 46.0, bend_dir=-1.0)
    sh_r = clavicle_follow((64.0, -198.0), (120.0, -206.0), 0.14)
    el_r, hand_r = solve_2bone_ik(sh_r, (120.0, -206.0), 48.0, 46.0, bend_dir=+1.0)

    helmet_pop = 8.0 if expression == "shocked" else 0.0
    back_hair, front_hat = _clara_hair_and_hardhat(svg, top_y, helmet_pop=helmet_pop)

    parts = [f'<g transform="translate({fmt(cx)},{fmt(floor_y)}) scale({fmt(scale)})">']
    parts.append(legs_svg)
    parts.append(back_hair)
    parts.append(draw_stick_limb(svg, sh_l, el_l, hand_l, w_start=13.5, w_end=10.5))
    parts.append(draw_stick_limb(svg, sh_r, el_r, hand_r, w_start=13.5, w_end=10.5))

    # Base capsule skin
    parts.append(f'<path d="{pill_d}" fill="{skin_g}"/>')

    # Clipped Industrial Work Shirt + Indigo Denim Overalls + Leather Tool Belt
    parts.append(f'<g clip-path="{pill_clip}">')
    # Burnt-orange industrial shirt with crisp curved neckline ink
    parts.append(
        f'<path d="M -86,{fmt(neck_y)} Q 0,{fmt(neck_y + 14)} 86,{fmt(neck_y)} '
        f'L 86,-120 L -86,-120 Z" fill="{shirt_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
    )
    # Shirt collar flap + placket
    parts.append(
        f'<path d="M -34,{fmt(neck_y - 2)} Q 0,{fmt(neck_y + 18)} 34,{fmt(neck_y - 2)} '
        f'L 22,{fmt(neck_y + 16)} L 0,{fmt(neck_y + 10)} L -22,{fmt(neck_y + 16)} Z" '
        f'fill="{lighten(shirt, 0.16)}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
    )
    # Indigo denim overalls (lower body + front bib + curved shoulder straps)
    parts.append(
        f'<path d="M -84,-154 Q 0,-142 84,-154 L 84,-72 L -84,-72 Z" fill="{denim_g}" '
        f'stroke="{INK_COLOR}" stroke-width="3.2"/>'
        f'<path d="M -42,-206 Q 0,-198 42,-206 L 46,-146 Q 0,-138 -46,-146 Z" fill="{denim_g}" '
        f'stroke="{INK_COLOR}" stroke-width="3.2" stroke-linejoin="round"/>'
        # Curved overall straps hugging capsule contour
        f'<path d="M -46,{fmt(neck_y + 2)} L -32,{fmt(neck_y + 4)} L -28,-196 L -42,-196 Z" '
        f'fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        f'<path d="M 32,{fmt(neck_y + 4)} L 46,{fmt(neck_y + 2)} L 42,-196 L 28,-196 Z" '
        f'fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        # Faceted brass overall buttons/buckles
        f'<circle cx="-35" cy="-195" r="5.5" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        f'<circle cx="35" cy="-195" r="5.5" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        f'<circle cx="-36.5" cy="-196.5" r="1.5" fill="#FFFFFF"/>'
        f'<circle cx="33.5" cy="-196.5" r="1.5" fill="#FFFFFF"/>'
        # Front bib pocket with tucked yellow drafting pencil & silver ruler!
        f'<rect x="6" y="-204" width="6" height="22" rx="1.5" transform="rotate(14 9 -193)" fill="#F7D046" stroke="{INK_COLOR}" stroke-width="1.8"/>'
        f'<rect x="-14" y="-202" width="7" height="20" rx="1" transform="rotate(-10 -10 -192)" fill="#D2DCE6" stroke="{INK_COLOR}" stroke-width="1.8"/>'
        f'<path d="M -25,-184 Q 0,-180 25,-184 L 22,-158 Q 0,-152 -22,-158 Z" '
        f'fill="{lighten(denim, 0.10)}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        # Cream overall stitch lines
        f'<path d="M -21,-180 L -19,-162 Q 0,-157 19,-162 L 21,-180" fill="none" stroke="#F5D99B" '
        f'stroke-width="1.6" stroke-dasharray="4 3" opacity="0.8"/>'
    )
    # Brown leather tool belt with pouch & brass buckle wrapping lower torso
    parts.append(
        f'<path d="M -82,-134 Q 0,-120 82,-134 L 82,-120 Q 0,-106 -82,-120 Z" '
        f'fill="#69391B" stroke="{INK_COLOR}" stroke-width="3.0"/>'
        # Side leather tool pouch
        f'<path d="M -54,-129 L -26,-125 L -28,-102 Q -40,-98 -52,-104 Z" '
        f'fill="#8A4E27" stroke="{INK_COLOR}" stroke-width="2.6" stroke-linejoin="round"/>'
        # Brass buckle
        f'<rect x="-11" y="-128" width="22" height="15" rx="3" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<rect x="-5" y="-124" width="10" height="7" rx="1.5" fill="#69391B"/>'
    )
    parts.append("</g>")

    # 3D shading + variable-width organic ink outline
    parts.append(_draw_capsule_volume_overlay(svg, pill_clip, 0.0, top_y, 150.0, pill_h))
    parts.append(variable_ink_closed(pts, min_w=3.2, max_w=7.6))

    # Rolled orange work sleeves
    parts.append(draw_sleeve_cap(svg, sh_l, el_l, shirt, radius=14.0))
    parts.append(draw_sleeve_cap(svg, sh_r, el_r, shirt, radius=14.0))

    parts.append(front_hat)
    parts.append(draw_expression(svg, expression, 0.0, face_cy, skin_color=skin, brow_color="#592C19", scale=0.94))

    if with_props:
        parts.append(draw_rocket_blueprint(svg, (hand_l[0] - 8, hand_l[1] - 12), angle_deg=-22.0, scale=0.94))
        parts.append(draw_hand(svg, hand_l, angle_deg=-18.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_steel_wrench(svg, (hand_r[0] + 6, hand_r[1] - 14), angle_deg=26.0, scale=0.94))
        parts.append(draw_hand(svg, hand_r, angle_deg=18.0, skin_color=skin, pose="grip"))
    else:
        parts.append(draw_hand(svg, hand_l, angle_deg=-18.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_hand(svg, hand_r, angle_deg=18.0, skin_color=skin, pose="grip"))

    parts.append("</g>")
    return "".join(parts)


CHARACTER_DRAWERS = {
    "raka": draw_raka,
    "bima": draw_bima,
    "doni": draw_doni,
    "clara": draw_clara,
}

# Face vertical centers (relative to floor_y = 0) for crisp portrait close-up cropping on Character Sheet
CHARACTER_PORTRAIT_ANCHOR = {
    "raka": (0.0, -326.0, 0.72),
    "bima": (0.0, -300.0, 0.68),
    "doni": (0.0, -274.0, 0.70),
    "clara": (0.0, -286.0, 0.70),
}


def draw_character(
    svg: SvgBuilder,
    char_id: str,
    expression: str,
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    return CHARACTER_DRAWERS[char_id](svg, expression=expression, cx=cx, floor_y=floor_y, scale=scale, with_props=with_props)


def draw_portrait_medallion(
    svg: SvgBuilder,
    char_id: str,
    expression: str,
    cx: float,
    cy: float,
    radius: float = 64.0,
    bg_color: str = "#F7F1E3",
    ring_color: str = "#D4A843",
) -> str:
    """Render a close-up expression portrait clipped cleanly inside an Art Deco circular medallion."""
    clip = svg.add_clip_path(f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(radius - 3.5)}"/>')
    ax, ay, p_scale = CHARACTER_PORTRAIT_ANCHOR[char_id]
    s = (radius / 64.0) * p_scale
    char_x = cx - ax * s
    char_y = cy - ay * s + radius * 0.08

    bg_g = svg.add_radial_gradient(
        [(0.0, lighten(bg_color, 0.14), 1.0), (1.0, darken(bg_color, 0.08), 1.0)],
        cx=0.35,
        cy=0.30,
        r=0.75,
    )
    char_svg = draw_character(svg, char_id, expression=expression, cx=char_x, floor_y=char_y, scale=s, with_props=False)
    return (
        f'<g>'
        f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(radius)}" fill="{bg_g}"/>'
        f'<g clip-path="{clip}">{char_svg}</g>'
        f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(radius - 1.5)}" fill="none" stroke="{ring_color}" stroke-width="4.0"/>'
        f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(radius + 0.8)}" fill="none" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        f"</g>"
    )
