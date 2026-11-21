"""Multi-angle 2.5D Character Turnaround System (0° Front, 45° 3/4, 90° Side, 135° Back 3/4, 180° Back).

Enables smooth camera orbits and directional sprite switching inside Blender 3D environments
while preserving consistent volume, variable-width ink outlines, 3D-wrapped outfits, and
biomechanical 2-bone IK stick-limb depth layering across every angle.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

from .cast import CAST_ORDER, CAST_SPECS, _draw_capsule_volume_overlay, draw_character
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

TURNAROUND_ANGLES: Tuple[Tuple[str, int, str], ...] = (
    ("front", 0, "0° Depan (Front)"),
    ("three_quarter", 45, "45° Tiga Perempat (3/4)"),
    ("side", 90, "90° Samping (Side Profile)"),
    ("back_three_quarter", 135, "135° Belakang 3/4"),
    ("back", 180, "180° Belakang (Back)"),
)


# ==============================================================================
# SHARED SIDE / BACK LIMB, SHOE & PROFILE FACE HELPERS
# ==============================================================================

def _draw_shoe_back(
    svg: SvgBuilder,
    ankle: Point,
    color: str,
    sole_color: str,
    scale: float = 1.0,
) -> str:
    """Grounded rear-view 3D shoe heel counter + sole."""
    x, y = ankle
    grad = svg.add_cylindrical_gradient(color, lit_shift=0.22, shadow_shift=0.36)
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) scale({fmt(scale)})">'
        f'<path d="M -16,-3 L 16,-3 Q 19,6 18,16 L -18,16 Q -19,6 -16,-3 Z" '
        f'fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        # Heel stitch tab & subtle specular
        f'<line x1="0" y1="-1" x2="0" y2="12" stroke="{darken(color, 0.4)}" stroke-width="2.2"/>'
        f'<path d="M -11,2 Q -5,0 0,2" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" opacity="0.35"/>'
        # Thick sole heel
        f'<rect x="-19" y="13" width="38" height="6.8" rx="3" fill="{sole_color}" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        f"</g>"
    )


def _draw_turned_legs(
    svg: SvgBuilder,
    angle_key: str,
    hip_y: float,
    hip_spread: float,
    shoe_color: str,
    sole_color: str,
    shoe_style: str,
    shoe_scale: float = 1.0,
) -> str:
    """Render depth-ordered biomechanical 2-bone IK legs matched to each turnaround angle."""
    ankle_y = -19.5

    def _fit_leg(hip: Point, ankle: Point, bend_dir: float, color: str, hi: str) -> str:
        d = math.hypot(ankle[0] - hip[0], ankle[1] - hip[1])
        bone = (d + 2.0) * 0.505
        knee, end = solve_2bone_ik(hip, ankle, bone, bone, bend_dir=bend_dir)
        return draw_stick_limb(svg, hip, knee, end, w_start=14.2, w_end=11.0, limb_color=color, highlight_color=hi, bend_softness=0.28)

    if angle_key == "three_quarter":
        # Back-left leg tucked slightly behind, front-right leg leading smoothly at 3/4 facing right
        hip_far = (-hip_spread * 0.62, hip_y)
        ank_far = (-hip_spread * 0.80, ankle_y - 2.0)
        hip_near = (hip_spread * 0.52, hip_y + 2.0)
        ank_near = (hip_spread * 0.72, ankle_y)
        return (
            "<g>"
            + _fit_leg(hip_far, ank_far, -1.0, "#14121B", "#3B374D")
            + draw_shoe(svg, ank_far, facing=+1.0, color=darken(shoe_color, 0.14), sole_color=sole_color, style=shoe_style, scale=shoe_scale * 0.96)
            + _fit_leg(hip_near, ank_near, -1.0, "#1C1A24", "#4E4A63")
            + draw_shoe(svg, ank_near, facing=+1.0, color=shoe_color, sole_color=sole_color, style=shoe_style, scale=shoe_scale)
            + "</g>"
        )

    if angle_key == "side":
        # Natural contrapposto / mid-stride side profile facing right!
        hip_far = (6.0, hip_y - 1.0)
        ank_far = (22.0, ankle_y - 2.5)
        hip_near = (-8.0, hip_y + 1.0)
        ank_near = (-20.0, ankle_y)
        return (
            "<g>"
            + _fit_leg(hip_far, ank_far, -1.0, "#131119", "#353145")
            + draw_shoe(svg, ank_far, facing=+1.0, color=darken(shoe_color, 0.18), sole_color=sole_color, style=shoe_style, scale=shoe_scale * 0.96)
            + _fit_leg(hip_near, ank_near, -1.0, "#1C1A24", "#4E4A63")
            + draw_shoe(svg, ank_near, facing=+1.0, color=shoe_color, sole_color=sole_color, style=shoe_style, scale=shoe_scale)
            + "</g>"
        )

    if angle_key == "back_three_quarter":
        # Turned away toward back-right: far-right leg forward, near-left heel closer to viewer
        hip_far = (hip_spread * 0.62, hip_y)
        ank_far = (hip_spread * 0.78, ankle_y - 2.0)
        hip_near = (-hip_spread * 0.52, hip_y + 2.0)
        ank_near = (-hip_spread * 0.72, ankle_y)
        return (
            "<g>"
            + _fit_leg(hip_far, ank_far, -1.0, "#14121B", "#3B374D")
            + draw_shoe(svg, ank_far, facing=+1.0, color=darken(shoe_color, 0.16), sole_color=sole_color, style=shoe_style, scale=shoe_scale * 0.94)
            + _fit_leg(hip_near, ank_near, +1.0, "#1C1A24", "#4E4A63")
            + _draw_shoe_back(svg, ank_near, color=shoe_color, sole_color=sole_color, scale=shoe_scale)
            + "</g>"
        )

    # Full 180° Back view
    hip_l = (-hip_spread, hip_y)
    hip_r = (hip_spread, hip_y)
    ank_l = (-hip_spread * 1.08, ankle_y)
    ank_r = (hip_spread * 1.08, ankle_y)
    return (
        "<g>"
        + _fit_leg(hip_l, ank_l, +1.0, "#1C1A24", "#4E4A63")
        + _fit_leg(hip_r, ank_r, -1.0, "#1C1A24", "#4E4A63")
        + _draw_shoe_back(svg, ank_l, color=shoe_color, sole_color=sole_color, scale=shoe_scale)
        + _draw_shoe_back(svg, ank_r, color=shoe_color, sole_color=sole_color, scale=shoe_scale)
        + "</g>"
    )


def _draw_side_profile_face(
    svg: SvgBuilder,
    char_id: str,
    expression: str,
    cx: float,
    cy: float,
    skin_color: str,
    brow_color: str,
    has_mustache: bool = False,
    mustache_color: str = "#343A4A",
) -> str:
    """Clean 2.5D stylized side-profile face (facing right) along the front-right contour of the pill."""
    lid_col = mix_color(skin_color, "#D49B7A", 0.25)
    parts = [f'<g transform="translate({fmt(cx)},{fmt(cy)})">']

    # Subtle stylized cheek/ear contour on side of capsule
    ear_g = svg.add_radial_gradient([(0.0, lighten(skin_color, 0.12), 1.0), (1.0, darken(skin_color, 0.18), 1.0)], 0.35, 0.3, 0.75)
    parts.append(
        f'<ellipse cx="-44" cy="4" rx="8.5" ry="11.5" fill="{ear_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>'
        f'<path d="M -45,0 Q -41,4 -45,8" fill="none" stroke="{darken(skin_color, 0.38)}" stroke-width="2.2" stroke-linecap="round"/>'
    )

    # Subtle warm cheek blush on cheerful/narcissistic/furious characters
    if expression in ("excited", "happy", "narcissistic", "furious"):
        bcol = "#E04438" if expression == "furious" else "#F57E72"
        bg = svg.add_radial_gradient([(0.0, bcol, 0.40), (1.0, bcol, 0.0)], 0.5, 0.5, 0.5)
        parts.append(f'<ellipse cx="14" cy="13" rx="13" ry="8" fill="{bg}"/>')

    # Stylized projecting nose bump along right profile contour
    parts.append(
        f'<path d="M 38,-4 Q 49,3 45,10 Q 41,13 36,12" fill="{skin_color}" stroke="{INK_COLOR}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>'
    )

    # Side-profile Eye (at x=+20, y=-5, facing right!)
    ex, ey = 22.0, -5.0
    erx, ery = 9.5, 13.5
    if expression == "panic":
        erx, ery = 11.0, 15.5
    clip = svg.add_clip_path(f'<ellipse cx="{fmt(ex)}" cy="{fmt(ey)}" rx="{fmt(erx)}" ry="{fmt(ery)}"/>')
    pupil_r = 3.6 if expression in ("panic", "shocked") else 5.2
    px, py = ex + erx * 0.38, ey + (1.0 if expression == "furious" else 0.0)

    parts.append(f'<ellipse cx="{fmt(ex)}" cy="{fmt(ey)}" rx="{fmt(erx)}" ry="{fmt(ery)}" fill="#FFFFFF"/>')
    parts.append(f'<g clip-path="{clip}">')
    parts.append(f'<circle cx="{fmt(px)}" cy="{fmt(py)}" r="{fmt(pupil_r)}" fill="{INK_COLOR}"/>')
    parts.append(f'<circle cx="{fmt(px - pupil_r * 0.32)}" cy="{fmt(py - pupil_r * 0.32)}" r="{fmt(max(1.7, pupil_r * 0.35))}" fill="#FFFFFF"/>')

    # Expression-specific upper eyelid
    if expression in ("chill", "smug", "narcissistic"):
        lid_h = ery * 0.72
        parts.append(
            f'<rect x="{fmt(ex - erx - 4)}" y="{fmt(ey - ery - 2)}" width="{fmt(erx * 2 + 8)}" height="{fmt(lid_h)}" fill="{lid_col}"/>'
            f'<line x1="{fmt(ex - erx - 4)}" y1="{fmt(ey - ery - 2 + lid_h)}" x2="{fmt(ex + erx + 4)}" y2="{fmt(ey - ery - 2 + lid_h)}" stroke="{INK_COLOR}" stroke-width="3.2"/>'
        )
    elif expression == "furious":
        parts.append(
            f'<polygon points="{fmt(ex - erx - 5)},{fmt(ey - ery - 4)} {fmt(ex + erx + 5)},{fmt(ey - ery - 4)} '
            f'{fmt(ex + erx + 5)},{fmt(ey - 1)} {fmt(ex - erx - 5)},{fmt(ey - 10)}" fill="{lid_col}" stroke="{INK_COLOR}" stroke-width="3.0"/>'
        )
    parts.append("</g>")
    parts.append(f'<ellipse cx="{fmt(ex)}" cy="{fmt(ey)}" rx="{fmt(erx)}" ry="{fmt(ery)}" fill="none" stroke="{INK_COLOR}" stroke-width="3.3"/>')

    # Side-profile Eyebrow
    if expression == "furious":
        parts.append(f'<path d="M 8,-24 Q 22,-20 34,-13" fill="none" stroke="{brow_color}" stroke-width="5.8" stroke-linecap="round"/>')
        # Crimson anger vein on side temple!
        parts.append(
            f'<g transform="translate(-12,-24) scale(0.85)" fill="none" stroke="#D92B2B" stroke-width="3.2" stroke-linecap="round">'
            f'<path d="M -8,-2 Q -3,-2 -2,-8"/><path d="M 8,-2 Q 3,-2 2,-8"/>'
            f'<path d="M -8,3 Q -3,3 -2,9"/><path d="M 8,3 Q 3,3 2,9"/></g>'
        )
    elif expression == "panic":
        parts.append(f'<path d="M 8,-22 Q 20,-34 34,-28" fill="none" stroke="{brow_color}" stroke-width="5.2" stroke-linecap="round"/>')
        # Glossy sweat drop on cheek!
        parts.append(
            f'<g transform="translate(-8,-18) scale(0.82)">'
            f'<path d="M 0,-12 C 6,-3 9,3 8,9 C 7,14 4,15 0,15 C -4,15 -7,14 -8,9 C -9,3 -6,-3 0,-12 Z" '
            f'fill="#6AD5F5" stroke="{INK_COLOR}" stroke-width="2.6"/>'
            f'<path d="M -3,2 C -4,6 -3,9 -1,10" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round"/></g>'
        )
    elif expression == "excited":
        parts.append(f'<path d="M 9,-26 Q 22,-34 35,-24" fill="none" stroke="{brow_color}" stroke-width="5.2" stroke-linecap="round"/>')
    else:
        parts.append(f'<path d="M 9,-22 Q 22,-28 34,-22" fill="none" stroke="{brow_color}" stroke-width="4.8" stroke-linecap="round"/>')

    # Side-profile Mouth (plus optional mustache for Pak Bima)
    my = 22.0 + (4.5 if has_mustache else 0.0)
    if expression == "chill":
        parts.append(f'<path d="M 16,{fmt(my + 2)} Q 28,{fmt(my + 5)} 39,{fmt(my - 2)}" fill="none" stroke="{INK_COLOR}" stroke-width="3.8" stroke-linecap="round"/>')
    elif expression == "panic":
        parts.append(
            f'<path d="M 18,{fmt(my + 5)} Q 24,{fmt(my - 7)} 38,{fmt(my - 4)} Q 40,{fmt(my + 11)} 28,{fmt(my + 12)} Q 20,{fmt(my + 12)} 18,{fmt(my + 5)} Z" '
            f'fill="#6B1D29" stroke="{INK_COLOR}" stroke-width="3.4" stroke-linejoin="round"/>'
            f'<ellipse cx="30" cy="{fmt(my + 9)}" rx="7" ry="3.5" fill="#EC6A74"/>'
        )
    elif expression == "furious":
        parts.append(
            f'<path d="M 15,{fmt(my - 1)} L 38,{fmt(my - 4)} L 36,{fmt(my + 9)} L 16,{fmt(my + 9)} Z" '
            f'fill="#FFFFFF" stroke="{INK_COLOR}" stroke-width="3.4" stroke-linejoin="round"/>'
            f'<line x1="16" y1="{fmt(my + 3)}" x2="37" y2="{fmt(my + 2)}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<line x1="26" y1="{fmt(my - 3)}" x2="26" y2="{fmt(my + 9)}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
        )
    elif expression == "excited":
        parts.append(
            f'<path d="M 16,{fmt(my - 3)} L 39,{fmt(my - 4)} Q 37,{fmt(my + 14)} 24,{fmt(my + 14)} Q 16,{fmt(my + 12)} 16,{fmt(my - 3)} Z" '
            f'fill="#6B1D29" stroke="{INK_COLOR}" stroke-width="3.4" stroke-linejoin="round"/>'
            f'<rect x="18" y="{fmt(my - 4)}" width="19" height="6" rx="1.5" fill="#FFFFFF"/>'
            f'<ellipse cx="27" cy="{fmt(my + 11)}" rx="7" ry="4" fill="#EC6A74"/>'
        )
    else:
        parts.append(f'<path d="M 17,{fmt(my + 1)} Q 28,{fmt(my + 7)} 39,{fmt(my - 1)}" fill="none" stroke="{INK_COLOR}" stroke-width="3.8" stroke-linecap="round"/>')

    if has_mustache:
        m_y = my - 8.5
        parts.append(
            f'<path d="M 22,{fmt(m_y + 2)} Q 32,{fmt(m_y - 6)} 46,{fmt(m_y + 1)} Q 36,{fmt(m_y + 7)} 22,{fmt(m_y + 2)} Z" '
            f'fill="{mustache_color}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        )

    parts.append("</g>")
    return "".join(parts)


def _draw_mirror_back(svg: SvgBuilder, pos: Point, angle_deg: float = -12.0, scale: float = 0.92) -> str:
    """Engraved Art Deco solid brass backside of Raka's hand mirror (visible on 135°/180° views!)."""
    gold_g = svg.add_linear_gradient([(0.0, "#FFF0A6", 1.0), (0.45, "#DFAA34", 1.0), (1.0, "#8C5C10", 1.0)], 0, 0, 1, 1)
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        f'<path d="M -6,-5 L 6,-5 L 8,28 Q 0,34 -8,28 Z" fill="{gold_g}" stroke="{INK_COLOR}" stroke-width="3.4" stroke-linejoin="round"/>'
        f'<ellipse cx="0" cy="-34" rx="29" ry="35" fill="{gold_g}" stroke="{INK_COLOR}" stroke-width="4.0"/>'
        f'<path d="M -11,-66 L 0,-77 L 11,-66 Z" fill="{gold_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
        # Engraved Art Deco sunburst rays on gold mirror backplate!
        f'<ellipse cx="0" cy="-34" rx="21" ry="26" fill="none" stroke="#8C5C10" stroke-width="2.2"/>'
        f'<line x1="0" y1="-58" x2="0" y2="-10" stroke="#9E6A14" stroke-width="1.8" opacity="0.7"/>'
        f'<line x1="-18" y1="-34" x2="18" y2="-34" stroke="#9E6A14" stroke-width="1.8" opacity="0.7"/>'
        f'<polygon points="0,-46 10,-34 0,-22 -10,-34" fill="#FFF3B8" stroke="#8C5C10" stroke-width="1.8"/>'
        f"</g>"
    )


def _draw_clipboard_back(svg: SvgBuilder, pos: Point, angle_deg: float = 10.0, scale: float = 0.92) -> str:
    """Walnut wood back of Pak Bima's clipboard (visible on 135°/180° views)."""
    wood_g = svg.add_linear_gradient([(0.0, "#9E633A", 1.0), (0.6, "#754320", 1.0), (1.0, "#4D2A12", 1.0)], 0, 0, 1, 1)
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        f'<rect x="-32" y="-44" width="64" height="86" rx="8" fill="{wood_g}" stroke="{INK_COLOR}" stroke-width="3.6"/>'
        f'<circle cx="-10" cy="-34" r="2.8" fill="#D9A83A" stroke="{INK_COLOR}" stroke-width="1.6"/>'
        f'<circle cx="10" cy="-34" r="2.8" fill="#D9A83A" stroke="{INK_COLOR}" stroke-width="1.6"/>'
        f'<line x1="-22" y1="-22" x2="-22" y2="30" stroke="#C48554" stroke-width="2.4" opacity="0.35" stroke-linecap="round"/>'
        f"</g>"
    )


# ==============================================================================
# 1. RAKA — MULTI-ANGLE TURNAROUND
# ==============================================================================

def draw_raka_angle(
    svg: SvgBuilder,
    angle_key: str,
    expression: str = "chill",
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    if angle_key == "front":
        return draw_character(svg, "raka", expression=expression, cx=cx, floor_y=floor_y, scale=scale, with_props=with_props)

    skin = "#FAD6B4"
    blazer = "#3E6E5F"
    turtleneck = "#F5EBD6"
    pants = "#2B343B"
    hair_base = "#2E1E16"
    top_y = -402.0
    pill_h = 304.0
    face_cy = -322.0
    neck_y = -270.0

    # Side profile capsule is slightly sleeker front-to-back (~88% width)
    w_fac = 0.88 if angle_key == "side" else (0.95 if "three_quarter" in angle_key else 1.0)
    pts = sample_rounded_capsule(0.0, top_y, 128 * w_fac, 144 * w_fac, 132 * w_fac, pill_h, 0.25, 0.20)
    pill_d = pts_to_path(pts, closed=True)
    pill_clip = svg.add_clip_path(f'<path d="{pill_d}"/>')

    skin_g = svg.add_cylindrical_gradient(skin, 0.16, 0.20, "#F7C28E")
    blazer_g = svg.add_cylindrical_gradient(blazer, 0.20, 0.36, "#E8B968")
    lapel_g = svg.add_linear_gradient([(0.0, lighten(blazer, 0.24), 1.0), (1.0, darken(blazer, 0.22), 1.0)], 0, 0, 1, 1)
    knit_g = svg.add_cylindrical_gradient(turtleneck, 0.14, 0.22)
    pants_g = svg.add_cylindrical_gradient(pants, 0.18, 0.32)
    hair_g = svg.add_linear_gradient([(0.0, "#593D2E", 1.0), (0.45, hair_base, 1.0), (1.0, "#170F0B", 1.0)], 0.15, 0, 0.85, 1)
    scarf_g = svg.add_cylindrical_gradient("#E8A825", 0.25, 0.35, "#FFE082")
    tail_g = svg.add_linear_gradient([(0.0, "#F5BE42", 1.0), (0.6, "#D9951A", 1.0), (1.0, "#A66A0C", 1.0)], 0, 0, 1, 1)

    legs_svg = _draw_turned_legs(svg, angle_key, -110.0, 26.0, "#6E442B", "#261812", "loafer", 1.02)

    parts = [f'<g transform="translate({fmt(cx)},{fmt(floor_y)}) scale({fmt(scale)})">']
    parts.append(legs_svg)

    # ---- BACK ARM (rendered BEHIND torso on 3/4, side, back_3/4) ----
    if angle_key == "three_quarter":
        sh_far = (52.0, -238.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (112.0, -236.0), 46.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 12.5, 10.0, "#15131C", "#3A364D"))
        if with_props:
            parts.append(draw_gold_hand_mirror(svg, (hand_far[0] + 6, hand_far[1] - 18), angle_deg=12.0, scale=0.90))
        parts.append(draw_hand(svg, hand_far, angle_deg=14.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "side":
        # Far hand extending forward holding the brass hand mirror!
        sh_far = (34.0, -236.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (104.0, -226.0), 46.0, 46.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 12.5, 10.0, "#14121B", "#3A364D"))
        if with_props:
            parts.append(draw_gold_hand_mirror(svg, (hand_far[0] + 4, hand_far[1] - 18), angle_deg=10.0, scale=0.88))
        parts.append(draw_hand(svg, hand_far, angle_deg=10.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "back_three_quarter":
        # Far-right arm peeking around front holding coffee cup
        sh_far = (52.0, -236.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (108.0, -212.0), 46.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 12.5, 10.0, "#14121B", "#3A364D"))
        if with_props:
            parts.append(draw_coffee_cup(svg, (hand_far[0] + 6, hand_far[1] - 6), angle_deg=8.0, scale=0.90))
        parts.append(draw_hand(svg, hand_far, angle_deg=12.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "back":
        # Mirror backplate in viewer-left hand, coffee cup in viewer-right hand (true mirrored L/R from back!)
        sh_l = clavicle_follow((-64.0, -236.0), (-120.0, -234.0), 0.12)
        el_l, hand_l = solve_2bone_ik(sh_l, (-120.0, -234.0), 48.0, 46.0, bend_dir=-1.0)
        sh_r = clavicle_follow((64.0, -236.0), (120.0, -214.0), 0.12)
        el_r, hand_r = solve_2bone_ik(sh_r, (120.0, -214.0), 48.0, 46.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_l, el_l, hand_l, 13.5, 10.5))
        parts.append(draw_stick_limb(svg, sh_r, el_r, hand_r, 13.5, 10.5))
        if with_props:
            parts.append(_draw_mirror_back(svg, (hand_l[0] - 6, hand_l[1] - 18), angle_deg=-14.0, scale=0.94))
            parts.append(draw_coffee_cup(svg, (hand_r[0] + 8, hand_r[1] - 4), angle_deg=8.0, scale=0.94))
        parts.append(draw_hand(svg, hand_l, angle_deg=-15.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_hand(svg, hand_r, angle_deg=15.0, skin_color=skin, pose="grip"))

    # Hair back contour behind pill
    if angle_key in ("three_quarter", "side"):
        parts.append(
            f'<path d="M -68,{fmt(top_y + 44)} C -78,{fmt(top_y + 4)} -58,{fmt(top_y - 42)} -8,{fmt(top_y - 46)} '
            f'C 38,{fmt(top_y - 48)} 74,{fmt(top_y - 12)} 66,{fmt(top_y + 38)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="5.0" stroke-linejoin="round"/>'
        )

    # Base pill fill
    parts.append(f'<path d="{pill_d}" fill="{skin_g}"/>')

    # ---- CLIPPED 3D OUTFIT WRAPPED BY ANGLE ----
    parts.append(f'<g clip-path="{pill_clip}">')
    parts.append(f'<path d="M -85,-138 Q 0,-124 85,-138 L 85,-80 L -85,-80 Z" fill="{pants_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>')
    parts.append(
        f'<path d="M -86,{fmt(neck_y + 4)} Q 0,{fmt(neck_y + 18)} 86,{fmt(neck_y + 4)} '
        f'L 86,-132 Q 0,-118 -86,-132 Z" fill="{blazer_g}"/>'
    )
    if angle_key == "three_quarter":
        # Center V shifted right (+22) in 3/4 cylindrical wrap!
        parts.append(
            f'<path d="M -4,{fmt(neck_y + 4)} L 46,{fmt(neck_y + 4)} L 38,-130 Q 20,-124 4,-130 Z" '
            f'fill="{knit_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            f'<path d="M -6,{fmt(neck_y + 4)} L -28,-216 L -14,-212 L -20,-195 L 4,-130 L 2,{fmt(neck_y + 4)} Z" '
            f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            f'<path d="M 46,{fmt(neck_y + 4)} L 64,-216 L 54,-211 L 58,-195 L 38,-130 L 40,{fmt(neck_y + 4)} Z" '
            f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            f'<path d="M -52,-162 Q -34,-158 -18,-162 L -19,-142 Q -35,-139 -50,-142 Z" '
            f'fill="{darken(blazer, 0.14)}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        )
    elif angle_key == "side":
        # Side profile: turtleneck edge peeking at far front-right, clean blazer side seam + side flap pocket!
        parts.append(
            f'<path d="M 38,{fmt(neck_y + 4)} L 66,{fmt(neck_y + 4)} L 66,-130 L 42,-130 Z" '
            f'fill="{knit_g}" stroke="{INK_COLOR}" stroke-width="3.0"/>'
            f'<path d="M 34,{fmt(neck_y + 4)} L 18,-214 L 32,-208 L 24,-192 L 42,-130 L 46,-130 L 42,{fmt(neck_y + 4)} Z" '
            f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            # Side blazer seam & pocket
            f'<line x1="-12" y1="{fmt(neck_y + 20)}" x2="-12" y2="-130" stroke="{darken(blazer, 0.35)}" stroke-width="2.2" opacity="0.55"/>'
            f'<path d="M -28,-164 Q -8,-160 12,-164 L 10,-143 Q -8,-140 -26,-143 Z" '
            f'fill="{darken(blazer, 0.14)}" stroke="{INK_COLOR}" stroke-width="2.5"/>'
        )
    elif angle_key == "back_three_quarter":
        # Tailored back blazer seam shifted left (-18) + back vent split!
        parts.append(
            f'<line x1="-18" y1="{fmt(neck_y + 18)}" x2="-18" y2="-128" stroke="{INK_COLOR}" stroke-width="2.8" opacity="0.65"/>'
            f'<path d="M -18,-160 L -10,-128 L -18,-128 Z" fill="{darken(blazer, 0.36)}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<line x1="22" y1="{fmt(neck_y + 22)}" x2="22" y2="-132" stroke="{darken(blazer, 0.30)}" stroke-width="2.0" opacity="0.45"/>'
        )
    else:
        # Full 180° back blazer: center seam, crisp back vent, shoulder yoke darts!
        parts.append(
            f'<line x1="0" y1="{fmt(neck_y + 16)}" x2="0" y2="-126" stroke="{INK_COLOR}" stroke-width="3.0" opacity="0.72"/>'
            f'<path d="M 0,-160 L 9,-126 L 0,-126 Z" fill="{darken(blazer, 0.38)}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<line x1="-38" y1="{fmt(neck_y + 22)}" x2="-34" y2="-132" stroke="{darken(blazer, 0.30)}" stroke-width="2.0" opacity="0.45"/>'
            f'<line x1="38" y1="{fmt(neck_y + 22)}" x2="34" y2="-132" stroke="{darken(blazer, 0.30)}" stroke-width="2.0" opacity="0.45"/>'
        )
    parts.append(f'<path d="M -80,-132 Q 0,-118 80,-132" fill="none" stroke="{INK_COLOR}" stroke-width="3.4"/>')
    parts.append("</g>")

    parts.append(_draw_capsule_volume_overlay(svg, pill_clip, 0.0, top_y, 148 * w_fac, pill_h))
    parts.append(variable_ink_closed(pts, min_w=3.2, max_w=7.6))

    # ---- SCARF 360° WRAP ----
    sw = 68.0 * w_fac
    if angle_key in ("three_quarter", "side"):
        tail_x = 12.0 if angle_key == "three_quarter" else 36.0
        parts.append(
            f'<path d="M {fmt(tail_x - 14)},{fmt(neck_y + 10)} Q {fmt(tail_x - 18)},{fmt(neck_y + 52)} {fmt(tail_x - 10)},{fmt(neck_y + 82)} '
            f'L {fmt(tail_x + 14)},{fmt(neck_y + 80)} Q {fmt(tail_x + 8)},{fmt(neck_y + 48)} {fmt(tail_x + 12)},{fmt(neck_y + 12)} Z" '
            f'fill="{tail_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
            f'<path d="M {fmt(tail_x - 11)},{fmt(neck_y + 66)} Q {fmt(tail_x + 2)},{fmt(neck_y + 69)} {fmt(tail_x + 12)},{fmt(neck_y + 65)}" '
            f'fill="none" stroke="#C44B27" stroke-width="4.2"/>'
        )
    parts.append(
        f'<path d="M {fmt(-sw)},{fmt(neck_y - 10)} Q 0,{fmt(neck_y + 8)} {fmt(sw)},{fmt(neck_y - 10)} '
        f'Q {fmt(sw + 8)},{fmt(neck_y + 6)} {fmt(sw - 1)},{fmt(neck_y + 20)} Q 0,{fmt(neck_y + 36)} {fmt(-sw + 1)},{fmt(neck_y + 20)} '
        f'Q {fmt(-sw - 8)},{fmt(neck_y + 6)} {fmt(-sw)},{fmt(neck_y - 10)} Z" '
        f'fill="{scarf_g}" stroke="{INK_COLOR}" stroke-width="4.2" stroke-linejoin="round"/>'
        f'<path d="M {fmt(-sw * 0.72)},{fmt(neck_y + 2)} Q 0,{fmt(neck_y + 16)} {fmt(sw * 0.72)},{fmt(neck_y + 2)}" '
        f'fill="none" stroke="#B37412" stroke-width="2.5" opacity="0.65"/>'
        f'<path d="M {fmt(-sw * 0.78)},{fmt(neck_y - 3)} Q {fmt(-sw * 0.2)},{fmt(neck_y + 6)} {fmt(sw * 0.15)},{fmt(neck_y + 5)}" '
        f'fill="none" stroke="#FFF1B8" stroke-width="3.0" stroke-linecap="round" opacity="0.62"/>'
    )
    if angle_key in ("back_three_quarter", "back"):
        # Overlapping knit scarf back fold crease
        kx = -14.0 if angle_key == "back_three_quarter" else 0.0
        parts.append(
            f'<path d="M {fmt(kx - 16)},{fmt(neck_y - 4)} Q {fmt(kx)},{fmt(neck_y + 12)} {fmt(kx + 18)},{fmt(neck_y + 24)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linecap="round"/>'
        )

    # ---- HAIR & FACE & GLASSES PER ANGLE ----
    if angle_key == "three_quarter":
        parts.append(
            f'<path d="M -62,{fmt(top_y + 50)} C -66,{fmt(top_y + 6)} -48,{fmt(top_y - 38)} -4,{fmt(top_y - 46)} '
            f'C 32,{fmt(top_y - 48)} 62,{fmt(top_y - 24)} 60,{fmt(top_y + 28)} '
            f'C 48,{fmt(top_y + 14)} 34,{fmt(top_y + 24)} 14,{fmt(top_y + 26)} '
            f'C -8,{fmt(top_y + 28)} -24,{fmt(top_y + 16)} -36,{fmt(top_y + 44)} '
            f'C -46,{fmt(top_y + 62)} -56,{fmt(top_y + 62)} -62,{fmt(top_y + 50)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
            f'<path d="M -38,{fmt(top_y - 16)} Q -10,{fmt(top_y - 34)} 20,{fmt(top_y - 26)}" '
            f'fill="none" stroke="#7A5643" stroke-width="5.2" stroke-linecap="round" opacity="0.7"/>'
        )
        # Shifted 3/4 face + glasses
        parts.append(
            f'<g transform="translate(22,0) scale(0.86,1.0)">'
            + draw_expression(svg, expression, 0.0, face_cy, skin_color=skin, brow_color=hair_base, scale=0.94, gaze=(0.35, 0.0))
            + "</g>"
        )
        # 3/4 Brass Glasses with near temple arm extending cleanly to ear
        ey = face_cy - 4.0
        parts.append(
            f'<g>'
            f'<ellipse cx="5" cy="{fmt(ey)}" rx="16.5" ry="17.5" fill="#FFFFFF" fill-opacity="0.16" stroke="{INK_COLOR}" stroke-width="5.0"/>'
            f'<ellipse cx="5" cy="{fmt(ey)}" rx="16.5" ry="17.5" fill="none" stroke="#D9A436" stroke-width="2.6"/>'
            f'<ellipse cx="40" cy="{fmt(ey)}" rx="13.5" ry="17.0" fill="#FFFFFF" fill-opacity="0.16" stroke="{INK_COLOR}" stroke-width="5.0"/>'
            f'<ellipse cx="40" cy="{fmt(ey)}" rx="13.5" ry="17.0" fill="none" stroke="#D9A436" stroke-width="2.6"/>'
            f'<path d="M 21,{fmt(ey - 1)} Q 24,{fmt(ey - 5)} 27,{fmt(ey - 1)}" fill="none" stroke="{INK_COLOR}" stroke-width="4.0"/>'
            f'<line x1="-11" y1="{fmt(ey - 2)}" x2="-48" y2="{fmt(ey - 5)}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linecap="round"/>'
            f'<line x1="-11" y1="{fmt(ey - 2)}" x2="-48" y2="{fmt(ey - 5)}" stroke="#D9A436" stroke-width="2.0" stroke-linecap="round"/>'
            f"</g>"
        )
    elif angle_key == "side":
        parts.append(_draw_side_profile_face(svg, "raka", expression, 16.0, face_cy, skin, hair_base))
        # Sweeping side-profile espresso hair wrapping around back of skull down to nape!
        parts.append(
            f'<path d="M -56,{fmt(top_y + 118)} C -66,{fmt(top_y + 62)} -66,{fmt(top_y - 14)} -26,{fmt(top_y - 44)} '
            f'C 16,{fmt(top_y - 54)} 64,{fmt(top_y - 24)} 58,{fmt(top_y + 22)} '
            f'C 42,{fmt(top_y + 16)} 22,{fmt(top_y + 28)} 2,{fmt(top_y + 20)} '
            f'C -18,{fmt(top_y + 14)} -24,{fmt(top_y + 44)} -24,{fmt(top_y + 72)} '
            f'C -36,{fmt(top_y + 76)} -38,{fmt(top_y + 106)} -56,{fmt(top_y + 118)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
            f'<path d="M -36,{fmt(top_y - 12)} Q -8,{fmt(top_y - 38)} 26,{fmt(top_y - 28)}" '
            f'fill="none" stroke="#7A5643" stroke-width="5.2" stroke-linecap="round" opacity="0.72"/>'
        )
        # Side-profile brass glasses: narrow oval front lens + sleek temple arm hooking over ear!
        ey = face_cy - 5.0
        parts.append(
            f'<ellipse cx="44" cy="{fmt(ey)}" rx="7.5" ry="17.5" fill="#D9F0FF" fill-opacity="0.28" stroke="{INK_COLOR}" stroke-width="5.0"/>'
            f'<ellipse cx="44" cy="{fmt(ey)}" rx="7.5" ry="17.5" fill="none" stroke="#D9A436" stroke-width="2.6"/>'
            f'<path d="M 36,{fmt(ey - 2)} L -26,{fmt(ey - 2)} Q -34,{fmt(ey - 2)} -36,{fmt(ey + 8)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="4.8" stroke-linecap="round"/>'
            f'<path d="M 36,{fmt(ey - 2)} L -26,{fmt(ey - 2)} Q -34,{fmt(ey - 2)} -36,{fmt(ey + 8)}" '
            f'fill="none" stroke="#D9A436" stroke-width="2.2" stroke-linecap="round"/>'
        )
    elif angle_key == "back_three_quarter":
        # Ear & hint of glasses temple on far right + lush wavy back-3/4 hair covering 80% of skull
        ey = face_cy - 4.0
        parts.append(
            f'<line x1="36" y1="{fmt(ey - 2)}" x2="62" y2="{fmt(ey - 2)}" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linecap="round"/>'
            f'<ellipse cx="38" cy="{fmt(ey + 8)}" rx="7.5" ry="10.5" fill="{skin_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>'
            f'<path d="M -62,{fmt(top_y + 114)} C -72,{fmt(top_y + 42)} -66,{fmt(top_y - 34)} -8,{fmt(top_y - 46)} '
            f'C 42,{fmt(top_y - 48)} 66,{fmt(top_y - 12)} 62,{fmt(top_y + 44)} '
            f'C 48,{fmt(top_y + 44)} 44,{fmt(top_y + 78)} 34,{fmt(top_y + 112)} '
            f'Q -14,{fmt(top_y + 126)} -62,{fmt(top_y + 114)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
            f'<path d="M -38,{fmt(top_y - 16)} Q -6,{fmt(top_y - 36)} 28,{fmt(top_y - 24)}" '
            f'fill="none" stroke="#7A5643" stroke-width="5.2" stroke-linecap="round" opacity="0.68"/>'
            f'<path d="M -36,{fmt(top_y + 62)} Q -8,{fmt(top_y + 74)} 18,{fmt(top_y + 62)}" '
            f'fill="none" stroke="#4D3326" stroke-width="3.4" stroke-linecap="round" opacity="0.55"/>'
        )
    else:
        # Full 180° Back Hair (lush wavy espresso crown wrapping all the way down to scarf!)
        parts.append(
            f'<path d="M -64,{fmt(top_y + 118)} C -74,{fmt(top_y + 42)} -66,{fmt(top_y - 40)} 0,{fmt(top_y - 46)} '
            f'C 66,{fmt(top_y - 40)} 74,{fmt(top_y + 42)} 64,{fmt(top_y + 118)} '
            f'Q 0,{fmt(top_y + 132)} -64,{fmt(top_y + 118)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.8" stroke-linejoin="round"/>'
            f'<path d="M -38,{fmt(top_y - 16)} Q 0,{fmt(top_y - 34)} 36,{fmt(top_y - 18)}" '
            f'fill="none" stroke="#7A5643" stroke-width="5.2" stroke-linecap="round" opacity="0.7"/>'
            f'<path d="M -38,{fmt(top_y + 66)} Q 0,{fmt(top_y + 82)} 38,{fmt(top_y + 66)}" '
            f'fill="none" stroke="#4D3326" stroke-width="3.6" stroke-linecap="round" opacity="0.58"/>'
        )

    # ---- FOREGROUND NEAR ARM (rendered IN FRONT of torso!) ----
    if angle_key == "three_quarter":
        sh_n = clavicle_follow((-54.0, -236.0), (-110.0, -210.0), 0.12)
        el_n, hand_n = solve_2bone_ik(sh_n, (-110.0, -210.0), 48.0, 46.0, bend_dir=-1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 13.5, 10.5))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, blazer, 14.5))
        if with_props:
            parts.append(draw_coffee_cup(svg, (hand_n[0] - 8, hand_n[1] - 4), angle_deg=-8.0, scale=0.95))
        parts.append(draw_hand(svg, hand_n, angle_deg=-15.0, skin_color=skin, pose="grip", flip_y=True))
    elif angle_key == "side":
        sh_n = clavicle_follow((-18.0, -234.0), (26.0, -182.0), 0.12)
        el_n, hand_n = solve_2bone_ik(sh_n, (26.0, -182.0), 46.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 13.5, 10.5))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, blazer, 14.5))
        if with_props:
            parts.append(draw_coffee_cup(svg, (hand_n[0] + 10, hand_n[1] - 6), angle_deg=6.0, scale=0.94))
        parts.append(draw_hand(svg, hand_n, angle_deg=12.0, skin_color=skin, pose="grip"))
    elif angle_key == "back_three_quarter":
        sh_n = clavicle_follow((-54.0, -236.0), (-112.0, -228.0), 0.12)
        el_n, hand_n = solve_2bone_ik(sh_n, (-112.0, -228.0), 48.0, 46.0, bend_dir=-1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 13.5, 10.5))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, blazer, 14.5))
        if with_props:
            parts.append(_draw_mirror_back(svg, (hand_n[0] - 8, hand_n[1] - 18), angle_deg=-14.0, scale=0.94))
        parts.append(draw_hand(svg, hand_n, angle_deg=-16.0, skin_color=skin, pose="grip", flip_y=True))
    elif angle_key == "back":
        parts.append(draw_sleeve_cap(svg, sh_l, el_l, blazer, 14.5))
        parts.append(draw_sleeve_cap(svg, sh_r, el_r, blazer, 14.5))

    parts.append("</g>")
    return "".join(parts)


# ==============================================================================
# 2. PAK BIMA — MULTI-ANGLE TURNAROUND
# ==============================================================================

def draw_bima_angle(
    svg: SvgBuilder,
    angle_key: str,
    expression: str = "panic",
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    if angle_key == "front":
        return draw_character(svg, "bima", expression=expression, cx=cx, floor_y=floor_y, scale=scale, with_props=with_props)

    skin = "#F7CEA8"
    suit = "#22375C"
    vest = "#DFC387"
    shirt = "#FAF7F0"
    tie = "#D93829"
    hair_col = "#343A4A"
    top_y = -384.0
    pill_h = 292.0
    face_cy = -306.0
    neck_y = -252.0

    w_fac = 0.86 if angle_key == "side" else (0.94 if "three_quarter" in angle_key else 1.0)
    pts = sample_rounded_capsule(0.0, top_y, 134 * w_fac, 168 * w_fac, 150 * w_fac, pill_h, 0.25, 0.20)
    pill_d = pts_to_path(pts, closed=True)
    pill_clip = svg.add_clip_path(f'<path d="{pill_d}"/>')

    skin_g = svg.add_cylindrical_gradient(skin, 0.15, 0.22, "#F5BA84")
    suit_g = svg.add_cylindrical_gradient(suit, 0.24, 0.38, "#E8B86B")
    lapel_g = svg.add_linear_gradient([(0.0, lighten(suit, 0.24), 1.0), (1.0, darken(suit, 0.26), 1.0)], 0, 0, 1, 1)
    vest_g = svg.add_cylindrical_gradient(vest, 0.18, 0.30)
    tie_g = svg.add_linear_gradient([(0.0, "#F55B4A", 1.0), (0.55, tie, 1.0), (1.0, "#8C1911", 1.0)], 0.1, 0, 0.9, 1)
    hair_g = svg.add_linear_gradient([(0.0, "#5C657D", 1.0), (0.5, hair_col, 1.0), (1.0, "#1C202B", 1.0)], 0.1, 0, 0.9, 1)

    legs_svg = _draw_turned_legs(svg, angle_key, -104.0, 30.0, "#1E1D24", "#121116", "oxford", 1.02)

    parts = [f'<g transform="translate({fmt(cx)},{fmt(floor_y)}) scale({fmt(scale)})">']
    parts.append(legs_svg)

    # Back cowlicks visible from every angle!
    parts.append(
        f'<path d="M -10,{fmt(top_y + 4)} Q -24,{fmt(top_y - 36)} -2,{fmt(top_y - 46)} '
        f'Q -5,{fmt(top_y - 25)} 9,{fmt(top_y - 10)} Z" fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        f'<path d="M 6,{fmt(top_y + 4)} Q 18,{fmt(top_y - 36)} 36,{fmt(top_y - 32)} '
        f'Q 18,{fmt(top_y - 16)} 22,{fmt(top_y - 2)} Z" fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
    )

    # ---- BACK ARM ----
    if angle_key == "three_quarter":
        sh_far = (58.0, -220.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (112.0, -222.0), 46.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 13.0, 10.5, "#15131C", "#3A364D"))
        if with_props:
            parts.append(draw_red_pen(svg, (hand_far[0] + 6, hand_far[1] - 10), angle_deg=-35.0, scale=0.95))
        parts.append(draw_hand(svg, hand_far, angle_deg=-10.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "side":
        sh_far = (36.0, -220.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (108.0, -228.0), 46.0, 46.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 13.0, 10.5, "#15131C", "#3A364D"))
        if with_props:
            parts.append(draw_red_pen(svg, (hand_far[0] + 6, hand_far[1] - 10), angle_deg=-30.0, scale=0.92))
        parts.append(draw_hand(svg, hand_far, angle_deg=-10.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "back_three_quarter":
        sh_far = (58.0, -220.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (116.0, -214.0), 46.0, 46.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 13.0, 10.5, "#15131C", "#3A364D"))
        if with_props:
            parts.append(_draw_clipboard_back(svg, (hand_far[0] + 10, hand_far[1] - 16), angle_deg=12.0, scale=0.90))
        parts.append(draw_hand(svg, hand_far, angle_deg=14.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "back":
        sh_l = clavicle_follow((-72.0, -220.0), (-124.0, -224.0), 0.14)
        el_l, hand_l = solve_2bone_ik(sh_l, (-124.0, -224.0), 48.0, 46.0, bend_dir=-1.0)
        sh_r = clavicle_follow((72.0, -220.0), (128.0, -214.0), 0.14)
        el_r, hand_r = solve_2bone_ik(sh_r, (128.0, -214.0), 48.0, 46.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_l, el_l, hand_l, 14.0, 11.0))
        parts.append(draw_stick_limb(svg, sh_r, el_r, hand_r, 14.0, 11.0))
        if with_props:
            parts.append(draw_red_pen(svg, (hand_l[0] - 8, hand_l[1] - 8), angle_deg=210.0, scale=0.95))
            parts.append(_draw_clipboard_back(svg, (hand_r[0] + 12, hand_r[1] - 16), angle_deg=12.0, scale=0.94))
        parts.append(draw_hand(svg, hand_l, angle_deg=-15.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_hand(svg, hand_r, angle_deg=15.0, skin_color=skin, pose="grip"))

    parts.append(f'<path d="{pill_d}" fill="{skin_g}"/>')

    # ---- CLIPPED 3D ART DECO SUIT ----
    parts.append(f'<g clip-path="{pill_clip}">')
    parts.append(
        f'<path d="M -95,{fmt(neck_y)} Q 0,{fmt(neck_y + 18)} 95,{fmt(neck_y)} '
        f'L 95,-80 L -95,-80 Z" fill="{suit_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
    )
    for px in (-56, -42, -28, -14, 0, 14, 28, 42, 56):
        parts.append(f'<line x1="{px}" y1="{fmt(neck_y + 10)}" x2="{px}" y2="-92" stroke="#4D6896" stroke-width="1.3" opacity="0.28"/>')

    if angle_key == "three_quarter":
        parts.append(
            f'<path d="M -6,{fmt(neck_y + 2)} L 56,{fmt(neck_y + 2)} L 52,-124 Q 24,-112 -2,-124 Z" '
            f'fill="{vest_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            f'<path d="M -2,{fmt(neck_y - 2)} L 52,{fmt(neck_y - 2)} L 26,-186 Z" '
            f'fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
            f'<path d="M -6,{fmt(neck_y)} L -32,-212 L -14,-208 L -20,-192 L 2,-122 L -8,-122 L -14,{fmt(neck_y)} Z" '
            f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            f'<rect x="-38" y="-194" width="22" height="12" rx="3" fill="#F0C24B" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<path d="M 0,-156 Q 14,-142 26,-154 Q 38,-142 48,-156" fill="none" stroke="{INK_COLOR}" stroke-width="4.2" stroke-linecap="round"/>'
            f'<path d="M 0,-156 Q 14,-142 26,-154 Q 38,-142 48,-156" fill="none" stroke="#F5C954" stroke-width="2.0" stroke-linecap="round"/>'
            f'<polygon points="-6,{fmt(neck_y - 4)} 26,{fmt(neck_y + 8)} 10,{fmt(neck_y + 22)}" fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
            f'<polygon points="56,{fmt(neck_y - 4)} 26,{fmt(neck_y + 8)} 40,{fmt(neck_y + 22)}" fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        )
    elif angle_key == "side":
        parts.append(
            f'<path d="M 44,{fmt(neck_y + 2)} L 76,{fmt(neck_y + 2)} L 76,-124 L 46,-124 Z" '
            f'fill="{vest_g}" stroke="{INK_COLOR}" stroke-width="3.0"/>'
            f'<path d="M 38,{fmt(neck_y)} L 24,-210 L 38,-204 L 30,-190 L 48,-122 L 54,-122 L 46,{fmt(neck_y)} Z" '
            f'fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            f'<rect x="6" y="-194" width="20" height="11" rx="3" fill="#F0C24B" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<path d="M -28,-154 Q -6,-150 18,-154 L 16,-134 Q -6,-130 -26,-134 Z" fill="{darken(suit, 0.16)}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
            f'<polygon points="34,{fmt(neck_y - 4)} 64,{fmt(neck_y + 6)} 46,{fmt(neck_y + 20)}" fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        )
    elif angle_key == "back_three_quarter":
        # Crisp folded white shirt collar strip + tailored suit back seams & vent
        parts.append(
            f'<path d="M -72,{fmt(neck_y - 2)} Q 0,{fmt(neck_y + 12)} 72,{fmt(neck_y - 2)} '
            f'L 70,{fmt(neck_y + 10)} Q 0,{fmt(neck_y + 22)} -70,{fmt(neck_y + 10)} Z" fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="2.8"/>'
            f'<line x1="-22" y1="{fmt(neck_y + 18)}" x2="-22" y2="-122" stroke="{INK_COLOR}" stroke-width="2.8" opacity="0.65"/>'
            f'<path d="M -22,-154 L -13,-122 L -22,-122 Z" fill="{darken(suit, 0.36)}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        )
    else:
        # Full 180° Back Suit: folded collar, center back seam, twin Art Deco side vents!
        parts.append(
            f'<path d="M -76,{fmt(neck_y - 2)} Q 0,{fmt(neck_y + 14)} 76,{fmt(neck_y - 2)} '
            f'L 74,{fmt(neck_y + 12)} Q 0,{fmt(neck_y + 24)} -74,{fmt(neck_y + 12)} Z" fill="{lapel_g}" stroke="{INK_COLOR}" stroke-width="3.0"/>'
            f'<line x1="0" y1="{fmt(neck_y + 20)}" x2="0" y2="-120" stroke="{INK_COLOR}" stroke-width="3.0" opacity="0.7"/>'
            f'<path d="M -38,-154 L -38,-122 L -30,-122 Z" fill="{darken(suit, 0.38)}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<path d="M 38,-154 L 38,-122 L 30,-122 Z" fill="{darken(suit, 0.38)}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        )
    parts.append(f'<path d="M -88,-124 Q 0,-110 88,-124" fill="none" stroke="{INK_COLOR}" stroke-width="3.6"/>')
    parts.append("</g>")

    parts.append(_draw_capsule_volume_overlay(svg, pill_clip, 0.0, top_y, 170 * w_fac, pill_h))
    parts.append(variable_ink_closed(pts, min_w=3.2, max_w=7.8))

    # Dynamic crimson tie fluttering forward in 3/4 and side views!
    if angle_key == "three_quarter":
        parts.append(
            f'<path d="M 22,{fmt(neck_y + 16)} L 33,{fmt(neck_y + 16)} Q 46,-198 48,-168 L 35,-154 L 22,-170 Z" '
            f'fill="{tie_g}" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linejoin="round"/>'
            f'<path d="M 20,{fmt(neck_y + 6)} L 36,{fmt(neck_y + 6)} L 33,{fmt(neck_y + 19)} L 23,{fmt(neck_y + 19)} Z" '
            f'fill="{tie_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
        )
    elif angle_key == "side":
        # Fluttering stressed tie kicking right off his chest!
        parts.append(
            f'<path d="M 56,{fmt(neck_y + 14)} L 68,{fmt(neck_y + 16)} Q 82,-200 94,-176 L 80,-164 Q 68,-182 56,-218 Z" '
            f'fill="{tie_g}" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linejoin="round"/>'
            f'<circle cx="62" cy="{fmt(neck_y + 14)}" r="7.5" fill="{tie_g}" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        )

    # ---- HAIR & FACE PER ANGLE ----
    if angle_key == "three_quarter":
        parts.append(
            f'<path d="M -62,{fmt(top_y + 48)} C -66,{fmt(top_y + 4)} -48,{fmt(top_y - 24)} 4,{fmt(top_y - 24)} '
            f'C 48,{fmt(top_y - 24)} 64,{fmt(top_y + 2)} 58,{fmt(top_y + 38)} '
            f'C 44,{fmt(top_y + 18)} 26,{fmt(top_y + 18)} 8,{fmt(top_y + 24)} '
            f'C -14,{fmt(top_y + 16)} -36,{fmt(top_y + 22)} -46,{fmt(top_y + 48)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
            f'<path d="M -38,{fmt(top_y - 8)} Q -8,{fmt(top_y - 18)} 24,{fmt(top_y - 12)}" fill="none" stroke="#8C96B0" stroke-width="4.4" stroke-linecap="round" opacity="0.65"/>'
        )
        parts.append(
            f'<g transform="translate(24,0) scale(0.86,1.0)">'
            + draw_expression(svg, expression, 0.0, face_cy, skin_color=skin, brow_color=hair_col, scale=0.94, has_mustache=True, mustache_color=hair_col)
            + "</g>"
        )
    elif angle_key == "side":
        parts.append(_draw_side_profile_face(svg, "bima", expression, 16.0, face_cy, skin, hair_col, has_mustache=True, mustache_color=hair_col))
        parts.append(
            f'<path d="M -58,{fmt(top_y + 106)} C -66,{fmt(top_y + 52)} -62,{fmt(top_y - 24)} -4,{fmt(top_y - 24)} '
            f'C 44,{fmt(top_y - 24)} 62,{fmt(top_y + 2)} 54,{fmt(top_y + 28)} '
            f'C 32,{fmt(top_y + 18)} 8,{fmt(top_y + 18)} -10,{fmt(top_y + 30)} '
            f'C -26,{fmt(top_y + 42)} -24,{fmt(top_y + 70)} -32,{fmt(top_y + 92)} '
            f'Q -44,{fmt(top_y + 106)} -58,{fmt(top_y + 106)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
            f'<path d="M -42,{fmt(top_y + 62)} Q -34,{fmt(top_y + 46)} -24,{fmt(top_y + 48)}" fill="none" stroke="#B4BED6" stroke-width="3.6" stroke-linecap="round" opacity="0.72"/>'
        )
    elif angle_key == "back_three_quarter":
        parts.append(
            f'<ellipse cx="42" cy="{fmt(face_cy + 4)}" rx="7.5" ry="10.5" fill="{skin_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>'
            f'<path d="M -64,{fmt(top_y + 102)} C -72,{fmt(top_y + 38)} -62,{fmt(top_y - 24)} -4,{fmt(top_y - 24)} '
            f'C 48,{fmt(top_y - 24)} 66,{fmt(top_y + 8)} 58,{fmt(top_y + 52)} '
            f'C 44,{fmt(top_y + 56)} 40,{fmt(top_y + 86)} 28,{fmt(top_y + 102)} '
            f'Q -18,{fmt(top_y + 114)} -64,{fmt(top_y + 102)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
            f'<path d="M -46,{fmt(top_y + 86)} Q -10,{fmt(top_y + 94)} 22,{fmt(top_y + 86)}" fill="none" stroke="#B4BED6" stroke-width="3.4" stroke-linecap="round" opacity="0.6"/>'
        )
    else:
        parts.append(
            f'<path d="M -66,{fmt(top_y + 104)} C -74,{fmt(top_y + 38)} -64,{fmt(top_y - 24)} 0,{fmt(top_y - 24)} '
            f'C 64,{fmt(top_y - 24)} 74,{fmt(top_y + 38)} 66,{fmt(top_y + 104)} '
            f'Q 0,{fmt(top_y + 116)} -66,{fmt(top_y + 104)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.8" stroke-linejoin="round"/>'
            f'<path d="M -48,{fmt(top_y + 88)} Q 0,{fmt(top_y + 98)} 48,{fmt(top_y + 88)}" fill="none" stroke="#B4BED6" stroke-width="3.6" stroke-linecap="round" opacity="0.62"/>'
        )

    # ---- FOREGROUND NEAR ARM ----
    if angle_key == "three_quarter":
        sh_n = clavicle_follow((-62.0, -220.0), (-120.0, -210.0), 0.14)
        el_n, hand_n = solve_2bone_ik(sh_n, (-120.0, -210.0), 48.0, 46.0, bend_dir=-1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 14.0, 11.0))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, suit, 15.5))
        if with_props:
            parts.append(draw_complaint_clipboard(svg, (hand_n[0] - 12, hand_n[1] - 18), angle_deg=-12.0, scale=0.94))
        parts.append(draw_hand(svg, hand_n, angle_deg=-20.0, skin_color=skin, pose="grip", flip_y=True))
    elif angle_key == "side":
        sh_n = clavicle_follow((-22.0, -220.0), (24.0, -176.0), 0.14)
        el_n, hand_n = solve_2bone_ik(sh_n, (24.0, -176.0), 46.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 14.0, 11.0))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, suit, 15.5))
        if with_props:
            parts.append(draw_complaint_clipboard(svg, (hand_n[0] + 10, hand_n[1] - 18), angle_deg=12.0, scale=0.90))
        parts.append(draw_hand(svg, hand_n, angle_deg=12.0, skin_color=skin, pose="grip"))
    elif angle_key == "back_three_quarter":
        sh_n = clavicle_follow((-62.0, -220.0), (-118.0, -222.0), 0.14)
        el_n, hand_n = solve_2bone_ik(sh_n, (-118.0, -222.0), 48.0, 46.0, bend_dir=-1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 14.0, 11.0))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, suit, 15.5))
        if with_props:
            parts.append(draw_red_pen(svg, (hand_n[0] - 8, hand_n[1] - 8), angle_deg=210.0, scale=0.95))
        parts.append(draw_hand(svg, hand_n, angle_deg=-16.0, skin_color=skin, pose="grip", flip_y=True))
    elif angle_key == "back":
        parts.append(draw_sleeve_cap(svg, sh_l, el_l, suit, 15.5))
        parts.append(draw_sleeve_cap(svg, sh_r, el_r, suit, 15.5))

    parts.append("</g>")
    return "".join(parts)


# ==============================================================================
# 3. PAK DONI — MULTI-ANGLE TURNAROUND (WITH ICONIC SIDE-PROFILE POMPADOUR!)
# ==============================================================================

def draw_doni_angle(
    svg: SvgBuilder,
    angle_key: str,
    expression: str = "furious",
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    if angle_key == "front":
        return draw_character(svg, "doni", expression=expression, cx=cx, floor_y=floor_y, scale=scale, with_props=with_props)

    skin = "#F6C8A2"
    vest = "#8E2436"
    shirt = "#EAF2FA"
    slacks = "#2E3340"
    top_y = -336.0
    pill_h = 260.0
    face_cy = -264.0
    neck_y = -212.0

    w_fac = 0.88 if angle_key == "side" else (0.95 if "three_quarter" in angle_key else 1.0)
    pts = sample_rounded_capsule(0.0, top_y, 132 * w_fac, 162 * w_fac, 152 * w_fac, pill_h, 0.27, 0.22)
    pill_d = pts_to_path(pts, closed=True)
    pill_clip = svg.add_clip_path(f'<path d="{pill_d}"/>')

    skin_g = svg.add_cylindrical_gradient(skin, 0.16, 0.22, "#F5B582")
    vest_g = svg.add_cylindrical_gradient(vest, 0.22, 0.36, "#F2B872")
    shirt_g = svg.add_cylindrical_gradient(shirt, 0.10, 0.18)
    slacks_g = svg.add_cylindrical_gradient(slacks, 0.18, 0.34)
    hair_g = svg.add_linear_gradient([(0.0, "#3D4663", 1.0), (0.38, "#1E2230", 1.0), (1.0, "#0F111A", 1.0)], 0.1, 0, 0.85, 1)
    buckle_g = svg.add_linear_gradient([(0.0, "#FFF0A6", 1.0), (0.5, "#E3B034", 1.0), (1.0, "#996814", 1.0)], 0, 0, 1, 1)

    legs_svg = _draw_turned_legs(svg, angle_key, -88.0, 30.0, "#3B2014", "#1A0E08", "oxford", 0.98)

    parts = [f'<g transform="translate({fmt(cx)},{fmt(floor_y)}) scale({fmt(scale)})">']
    parts.append(legs_svg)

    # ---- BACK ARM ----
    if angle_key == "three_quarter":
        sh_far = (56.0, -184.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (104.0, -124.0), 42.0, 40.0, bend_dir=-1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 13.0, 10.5, "#15131C", "#3A364D"))
        if with_props:
            parts.append(draw_leather_briefcase(svg, (hand_far[0] + 4, hand_far[1] + 4), angle_deg=6.0, scale=0.88))
        parts.append(draw_hand(svg, hand_far, angle_deg=70.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "side":
        sh_far = (34.0, -184.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (96.0, -206.0), 44.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 13.0, 10.5, "#15131C", "#3A364D"))
        if with_props:
            wx = el_far[0] + (hand_far[0] - el_far[0]) * 0.62
            wy = el_far[1] + (hand_far[1] - el_far[1]) * 0.62
            parts.append(draw_gold_wristwatch(svg, (wx, wy), angle_deg=45.0, scale=1.0))
            parts.append(draw_pocket_comb(svg, (hand_far[0] + 12, hand_far[1] - 14), angle_deg=30.0, scale=0.90))
        parts.append(draw_hand(svg, hand_far, angle_deg=14.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "back_three_quarter":
        sh_far = (56.0, -184.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (112.0, -204.0), 44.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 13.0, 10.5, "#15131C", "#3A364D"))
        if with_props:
            parts.append(draw_pocket_comb(svg, (hand_far[0] + 10, hand_far[1] - 16), angle_deg=34.0, scale=0.90))
        parts.append(draw_hand(svg, hand_far, angle_deg=14.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "back":
        sh_l = clavicle_follow((-70.0, -184.0), (-112.0, -124.0), 0.12)
        el_l, hand_l = solve_2bone_ik(sh_l, (-112.0, -124.0), 44.0, 42.0, bend_dir=+1.0)
        sh_r = clavicle_follow((70.0, -184.0), (120.0, -204.0), 0.14)
        el_r, hand_r = solve_2bone_ik(sh_r, (120.0, -204.0), 46.0, 46.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_l, el_l, hand_l, 14.0, 11.0))
        parts.append(draw_stick_limb(svg, sh_r, el_r, hand_r, 14.0, 11.0))
        if with_props:
            parts.append(draw_leather_briefcase(svg, (hand_l[0] - 4, hand_l[1] + 4), angle_deg=-6.0, scale=0.92))
            parts.append(draw_pocket_comb(svg, (hand_r[0] + 12, hand_r[1] - 16), angle_deg=36.0, scale=0.92))
        parts.append(draw_hand(svg, hand_l, angle_deg=110.0, skin_color=skin, pose="grip"))
        parts.append(draw_hand(svg, hand_r, angle_deg=18.0, skin_color=skin, pose="grip"))

    parts.append(f'<path d="{pill_d}" fill="{skin_g}"/>')

    # ---- CLIPPED BURGUNDY VEST & BELT ----
    parts.append(f'<g clip-path="{pill_clip}">')
    parts.append(f'<path d="M -90,-114 Q 0,-100 90,-114 L 90,-65 L -90,-65 Z" fill="{slacks_g}"/>')
    parts.append(
        f'<path d="M -90,{fmt(neck_y)} Q 0,{fmt(neck_y + 14)} 90,{fmt(neck_y)} '
        f'L 90,-118 Q 0,-104 -90,-118 Z" fill="{vest_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
    )
    if angle_key == "three_quarter":
        for ax in (-22, 22, 62):
            parts.append(
                f'<polygon points="{ax},-174 {ax + 15},-152 {ax},-130 {ax - 15},-152" fill="#B5384B" opacity="0.34"/>'
                f'<polygon points="{ax},-174 {ax + 15},-152 {ax},-130 {ax - 15},-152" fill="none" stroke="#F0C674" stroke-width="1.3" opacity="0.45"/>'
            )
        parts.append(
            f'<path d="M -8,{fmt(neck_y - 2)} L 58,{fmt(neck_y - 2)} L 26,-156 Z" '
            f'fill="{shirt_g}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
            f'<polygon points="22,{fmt(neck_y + 12)} 31,{fmt(neck_y + 12)} 33,-168 26,-158 19,-168" fill="#2F3B4D" stroke="{INK_COLOR}" stroke-width="2.4"/>'
            f'<polygon points="-6,{fmt(neck_y - 4)} 26,{fmt(neck_y + 6)} 10,{fmt(neck_y + 20)}" fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.6" stroke-linejoin="round"/>'
            f'<polygon points="56,{fmt(neck_y - 4)} 26,{fmt(neck_y + 6)} 42,{fmt(neck_y + 20)}" fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.6" stroke-linejoin="round"/>'
        )
    elif angle_key == "side":
        for ax in (10, 48):
            parts.append(
                f'<polygon points="{ax},-174 {ax + 14},-152 {ax},-130 {ax - 14},-152" fill="#B5384B" opacity="0.32"/>'
                f'<polygon points="{ax},-174 {ax + 14},-152 {ax},-130 {ax - 14},-152" fill="none" stroke="#F0C674" stroke-width="1.3" opacity="0.42"/>'
            )
        parts.append(
            f'<polygon points="36,{fmt(neck_y - 4)} 68,{fmt(neck_y + 4)} 52,{fmt(neck_y + 20)}" fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        )
    else:
        # Back 3/4 & Full Back: clean crisp sky-white collar strip around nape + neat vest back + rear pocket lines
        parts.append(
            f'<path d="M -76,{fmt(neck_y - 2)} Q 0,{fmt(neck_y + 12)} 76,{fmt(neck_y - 2)} '
            f'L 72,{fmt(neck_y + 10)} Q 0,{fmt(neck_y + 22)} -72,{fmt(neck_y + 10)} Z" fill="{shirt}" stroke="{INK_COLOR}" stroke-width="2.8"/>'
            f'<line x1="-38" y1="-92" x2="-12" y2="-92" stroke="{INK_COLOR}" stroke-width="2.4" opacity="0.55" stroke-linecap="round"/>'
            f'<line x1="12" y1="-92" x2="38" y2="-92" stroke="{INK_COLOR}" stroke-width="2.4" opacity="0.55" stroke-linecap="round"/>'
        )

    # Ribbed vest hem + leather belt (brass buckle on front/3/4, clean leather loops on side/back)
    parts.append(
        f'<path d="M -88,-126 Q 0,-112 88,-126 L 88,-115 Q 0,-101 -88,-115 Z" fill="{darken(vest, 0.24)}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        f'<path d="M -86,-116 Q 0,-102 86,-116 L 86,-104 Q 0,-90 -86,-104 Z" fill="#3D2114" stroke="{INK_COLOR}" stroke-width="2.8"/>'
    )
    if angle_key == "three_quarter":
        parts.append(
            f'<rect x="14" y="-110" width="22" height="14" rx="3" fill="{buckle_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
            f'<rect x="20" y="-106" width="10" height="6" rx="1.5" fill="#3D2114"/>'
        )
    else:
        for lx in (-42, 0, 42):
            parts.append(f'<rect x="{lx - 4}" y="-113" width="8" height="16" rx="2" fill="#232833" stroke="{INK_COLOR}" stroke-width="1.8"/>')
    parts.append("</g>")

    parts.append(_draw_capsule_volume_overlay(svg, pill_clip, 0.0, top_y, 166 * w_fac, pill_h))
    parts.append(variable_ink_closed(pts, min_w=3.2, max_w=7.8))

    # ---- ICONIC 3D POMPADOUR + FACE PER ANGLE ----
    if angle_key == "three_quarter":
        parts.append(
            f'<path d="M -62,{fmt(top_y + 48)} C -74,{fmt(top_y - 6)} -48,{fmt(top_y - 62)} 14,{fmt(top_y - 64)} '
            f'C 70,{fmt(top_y - 66)} 104,{fmt(top_y - 36)} 94,{fmt(top_y - 4)} '
            f'C 86,{fmt(top_y + 18)} 66,{fmt(top_y + 22)} 58,{fmt(top_y + 34)} '
            f'C 42,{fmt(top_y + 16)} 12,{fmt(top_y + 26)} -26,{fmt(top_y + 24)} '
            f'C -44,{fmt(top_y + 24)} -48,{fmt(top_y + 44)} -62,{fmt(top_y + 48)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
            f'<path d="M -32,{fmt(top_y - 24)} C 0,{fmt(top_y - 52)} 48,{fmt(top_y - 52)} 76,{fmt(top_y - 32)}" '
            f'fill="none" stroke="#7A8BB8" stroke-width="6.2" stroke-linecap="round" opacity="0.72"/>'
            f'<path d="M -18,{fmt(top_y - 22)} C 8,{fmt(top_y - 44)} 38,{fmt(top_y - 44)} 58,{fmt(top_y - 32)}" '
            f'fill="none" stroke="#E4EEFF" stroke-width="2.6" stroke-linecap="round" opacity="0.78"/>'
            f'<path d="M -54,{fmt(top_y + 38)} L -50,{fmt(top_y + 68)} L -40,{fmt(top_y + 56)} Z" fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        )
        parts.append(
            f'<g transform="translate(24,0) scale(0.86,1.0)">'
            + draw_expression(svg, expression, 0.0, face_cy, skin_color=skin, brow_color="#1E2230", scale=0.94)
            + "</g>"
        )
    elif angle_key == "side":
        # SIDE-PROFILE FACE + LEGENDARY JUTTING ROCKABILLY POMPADOUR!!
        parts.append(_draw_side_profile_face(svg, "doni", expression, 16.0, face_cy, skin, "#1E2230"))
        parts.append(
            # Sweeping rockabilly pompadour crest jutting dramatically out past forehead (+102!) + sleek ducktail nape!
            f'<path d="M -56,{fmt(top_y + 104)} C -72,{fmt(top_y + 54)} -70,{fmt(top_y - 18)} -24,{fmt(top_y - 56)} '
            f'C 22,{fmt(top_y - 76)} 98,{fmt(top_y - 62)} 104,{fmt(top_y - 22)} '
            f'C 108,{fmt(top_y + 4)} 82,{fmt(top_y + 20)} 56,{fmt(top_y + 18)} '
            f'C 32,{fmt(top_y + 18)} 8,{fmt(top_y + 14)} -8,{fmt(top_y + 28)} '
            f'C -18,{fmt(top_y + 38)} -22,{fmt(top_y + 68)} -34,{fmt(top_y + 66)} '
            f'L -36,{fmt(top_y + 90)} Q -48,{fmt(top_y + 104)} -56,{fmt(top_y + 104)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
            # Pompadour side-view spiral curl & pomade gloss!
            f'<path d="M 68,{fmt(top_y - 22)} C 86,{fmt(top_y - 22)} 88,{fmt(top_y - 2)} 68,{fmt(top_y + 4)}" '
            f'fill="none" stroke="#0B0C12" stroke-width="3.6" stroke-linecap="round"/>'
            f'<path d="M -28,{fmt(top_y - 26)} C 6,{fmt(top_y - 58)} 56,{fmt(top_y - 58)} 86,{fmt(top_y - 34)}" '
            f'fill="none" stroke="#7A8BB8" stroke-width="6.4" stroke-linecap="round" opacity="0.72"/>'
            f'<path d="M -14,{fmt(top_y - 24)} C 14,{fmt(top_y - 48)} 48,{fmt(top_y - 48)} 68,{fmt(top_y - 34)}" '
            f'fill="none" stroke="#E4EEFF" stroke-width="2.6" stroke-linecap="round" opacity="0.80"/>'
            # Crisp sideburn right in front of ear
            f'<path d="M -18,{fmt(top_y + 42)} L -16,{fmt(top_y + 72)} L -8,{fmt(top_y + 64)} L -10,{fmt(top_y + 42)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        )
    elif angle_key == "back_three_quarter":
        # Over-the-shoulder view (perfect for mirror shots!): sweeping pompadour jutting to far-right!
        parts.append(
            f'<ellipse cx="42" cy="{fmt(face_cy + 4)}" rx="7.5" ry="10.5" fill="{skin_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>'
            f'<path d="M -62,{fmt(top_y + 100)} C -74,{fmt(top_y + 38)} -64,{fmt(top_y - 34)} -8,{fmt(top_y - 58)} '
            f'C 42,{fmt(top_y - 72)} 88,{fmt(top_y - 44)} 82,{fmt(top_y - 4)} '
            f'C 78,{fmt(top_y + 16)} 64,{fmt(top_y + 24)} 54,{fmt(top_y + 44)} '
            f'C 46,{fmt(top_y + 68)} 36,{fmt(top_y + 92)} 24,{fmt(top_y + 102)} '
            f'Q -20,{fmt(top_y + 114)} -62,{fmt(top_y + 100)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
            f'<path d="M -32,{fmt(top_y - 24)} C 0,{fmt(top_y - 52)} 38,{fmt(top_y - 52)} 64,{fmt(top_y - 32)}" '
            f'fill="none" stroke="#7A8BB8" stroke-width="5.6" stroke-linecap="round" opacity="0.7"/>'
        )
    else:
        # Full 180° Back Pompadour Crown (sleek sculpted jet-black back with combed taper lines!)
        parts.append(
            f'<path d="M -64,{fmt(top_y + 100)} C -76,{fmt(top_y + 34)} -68,{fmt(top_y - 44)} 0,{fmt(top_y - 62)} '
            f'C 68,{fmt(top_y - 44)} 76,{fmt(top_y + 34)} 64,{fmt(top_y + 100)} '
            f'Q 0,{fmt(top_y + 112)} -64,{fmt(top_y + 100)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.8" stroke-linejoin="round"/>'
            f'<path d="M -36,{fmt(top_y - 26)} Q 0,{fmt(top_y - 48)} 36,{fmt(top_y - 26)}" '
            f'fill="none" stroke="#7A8BB8" stroke-width="5.6" stroke-linecap="round" opacity="0.72"/>'
            # Ducktail combed back crease!
            f'<path d="M -32,{fmt(top_y + 44)} Q -8,{fmt(top_y + 64)} 0,{fmt(top_y + 94)} Q 8,{fmt(top_y + 64)} 32,{fmt(top_y + 44)}" '
            f'fill="none" stroke="#3B4563" stroke-width="2.6" stroke-linecap="round" opacity="0.65"/>'
        )

    # ---- FOREGROUND NEAR ARM ----
    if angle_key == "three_quarter":
        sh_n = clavicle_follow((-58.0, -184.0), (-114.0, -206.0), 0.14)
        el_n, hand_n = solve_2bone_ik(sh_n, (-114.0, -206.0), 46.0, 46.0, bend_dir=-1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 14.0, 11.0))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, shirt, 15.0))
        if with_props:
            wx = el_n[0] + (hand_n[0] - el_n[0]) * 0.66
            wy = el_n[1] + (hand_n[1] - el_n[1]) * 0.66
            ang = math.degrees(math.atan2(hand_n[1] - el_n[1], hand_n[0] - el_n[0]))
            parts.append(draw_gold_wristwatch(svg, (wx, wy), angle_deg=ang + 90.0, scale=1.05))
            parts.append(draw_pocket_comb(svg, (hand_n[0] - 14, hand_n[1] - 18), angle_deg=-38.0, scale=0.92))
        parts.append(draw_hand(svg, hand_n, angle_deg=-25.0, skin_color=skin, pose="grip", flip_y=True))
    elif angle_key == "side":
        sh_n = clavicle_follow((-18.0, -184.0), (-14.0, -118.0), 0.10)
        el_n, hand_n = solve_2bone_ik(sh_n, (-14.0, -118.0), 36.0, 34.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 14.0, 11.0))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, shirt, 15.0))
        if with_props:
            parts.append(draw_leather_briefcase(svg, (hand_n[0] + 2, hand_n[1] + 4), angle_deg=4.0, scale=0.92))
        parts.append(draw_hand(svg, hand_n, angle_deg=85.0, skin_color=skin, pose="grip"))
    elif angle_key == "back_three_quarter":
        sh_n = clavicle_follow((-58.0, -184.0), (-106.0, -124.0), 0.12)
        el_n, hand_n = solve_2bone_ik(sh_n, (-106.0, -124.0), 44.0, 42.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 14.0, 11.0))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, shirt, 15.0))
        if with_props:
            parts.append(draw_leather_briefcase(svg, (hand_n[0] - 4, hand_n[1] + 4), angle_deg=-6.0, scale=0.92))
        parts.append(draw_hand(svg, hand_n, angle_deg=110.0, skin_color=skin, pose="grip"))
    elif angle_key == "back":
        parts.append(draw_sleeve_cap(svg, sh_l, el_l, shirt, 15.0))
        parts.append(draw_sleeve_cap(svg, sh_r, el_r, shirt, 15.0))

    parts.append("</g>")
    return "".join(parts)


# ==============================================================================
# 4. CLARA — MULTI-ANGLE TURNAROUND (HARD HAT + GOGGLES + PONYTAIL + X-OVERALLS)
# ==============================================================================

def draw_clara_angle(
    svg: SvgBuilder,
    angle_key: str,
    expression: str = "excited",
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    if angle_key == "front":
        return draw_character(svg, "clara", expression=expression, cx=cx, floor_y=floor_y, scale=scale, with_props=with_props)

    skin = "#F9D5B5"
    shirt = "#DE642B"
    denim = "#2D4F7E"
    hair_col = "#6E3A24"
    top_y = -356.0
    pill_h = 272.0
    face_cy = -280.0
    neck_y = -226.0

    w_fac = 0.88 if angle_key == "side" else (0.95 if "three_quarter" in angle_key else 1.0)
    pts = sample_rounded_capsule(0.0, top_y, 124 * w_fac, 146 * w_fac, 142 * w_fac, pill_h, 0.26, 0.22)
    pill_d = pts_to_path(pts, closed=True)
    pill_clip = svg.add_clip_path(f'<path d="{pill_d}"/>')

    skin_g = svg.add_cylindrical_gradient(skin, 0.16, 0.20, "#F7BC88")
    shirt_g = svg.add_cylindrical_gradient(shirt, 0.22, 0.34, "#FFC57A")
    denim_g = svg.add_cylindrical_gradient(denim, 0.22, 0.36, "#E8B874")
    hair_g = svg.add_linear_gradient([(0.0, "#9E5A3C", 1.0), (0.55, hair_col, 1.0), (1.0, "#3D1E11", 1.0)], 0.1, 0, 0.9, 1)
    hat_g = svg.add_radial_gradient([(0.0, "#FFE484", 1.0), (0.45, "#F2B724", 1.0), (0.85, "#C78710", 1.0), (1.0, "#E3A729", 1.0)], 0.32, 0.28, 0.72)
    brim_g = svg.add_linear_gradient([(0.0, "#FFD86B", 1.0), (0.6, "#E3A419", 1.0), (1.0, "#A6700B", 1.0)], 0, 0, 1, 1)
    lens_g = svg.add_linear_gradient([(0.0, "#C7FAFF", 1.0), (0.5, "#44C4D8", 1.0), (1.0, "#1D7891", 1.0)], 0.1, 0, 0.9, 1)
    brass_g = svg.add_linear_gradient([(0.0, "#FFF2AD", 1.0), (0.5, "#E3B234", 1.0), (1.0, "#996A14", 1.0)], 0, 0, 1, 1)

    legs_svg = _draw_turned_legs(svg, angle_key, -96.0, 27.0, "#73411F", "#1C1410", "boot", 1.02)

    parts = [f'<g transform="translate({fmt(cx)},{fmt(floor_y)}) scale({fmt(scale)})">']
    parts.append(legs_svg)

    # Trailing bouncy ponytail behind head on 3/4 & Side views!
    if angle_key == "three_quarter":
        parts.append(
            f'<path d="M -52,{fmt(top_y + 42)} C -84,{fmt(top_y + 28)} -102,{fmt(top_y + 62)} -84,{fmt(top_y + 96)} '
            f'C -74,{fmt(top_y + 106)} -64,{fmt(top_y + 94)} -66,{fmt(top_y + 80)} '
            f'C -68,{fmt(top_y + 68)} -58,{fmt(top_y + 62)} -46,{fmt(top_y + 56)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
            f'<ellipse cx="-56" cy="{fmt(top_y + 50)}" rx="7" ry="11" transform="rotate(18 -56 {fmt(top_y + 50)})" '
            f'fill="#F2B724" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        )
    elif angle_key == "side":
        parts.append(
            f'<path d="M -54,{fmt(top_y + 38)} C -92,{fmt(top_y + 22)} -114,{fmt(top_y + 60)} -92,{fmt(top_y + 98)} '
            f'C -80,{fmt(top_y + 108)} -68,{fmt(top_y + 96)} -72,{fmt(top_y + 80)} '
            f'C -74,{fmt(top_y + 66)} -64,{fmt(top_y + 58)} -48,{fmt(top_y + 54)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
            f'<path d="M -72,{fmt(top_y + 42)} Q -90,{fmt(top_y + 54)} -88,{fmt(top_y + 78)}" fill="none" stroke="#B87352" stroke-width="3.6" stroke-linecap="round" opacity="0.65"/>'
            f'<ellipse cx="-56" cy="{fmt(top_y + 46)}" rx="7.5" ry="11.5" transform="rotate(20 -56 {fmt(top_y + 46)})" '
            f'fill="#F2B724" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        )

    # ---- BACK ARM ----
    if angle_key == "three_quarter":
        sh_far = (52.0, -198.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (108.0, -206.0), 44.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 12.5, 10.0, "#15131C", "#3A364D"))
        if with_props:
            parts.append(draw_steel_wrench(svg, (hand_far[0] + 6, hand_far[1] - 14), angle_deg=26.0, scale=0.90))
        parts.append(draw_hand(svg, hand_far, angle_deg=18.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "side":
        sh_far = (34.0, -198.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (100.0, -208.0), 44.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 12.5, 10.0, "#15131C", "#3A364D"))
        if with_props:
            parts.append(draw_steel_wrench(svg, (hand_far[0] + 6, hand_far[1] - 14), angle_deg=22.0, scale=0.88))
        parts.append(draw_hand(svg, hand_far, angle_deg=16.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "back_three_quarter":
        sh_far = (52.0, -198.0)
        el_far, hand_far = solve_2bone_ik(sh_far, (108.0, -214.0), 44.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_far, el_far, hand_far, 12.5, 10.0, "#15131C", "#3A364D"))
        if with_props:
            parts.append(draw_rocket_blueprint(svg, (hand_far[0] + 8, hand_far[1] - 12), angle_deg=20.0, scale=0.88))
        parts.append(draw_hand(svg, hand_far, angle_deg=16.0, skin_color=darken(skin, 0.08), pose="grip"))
    elif angle_key == "back":
        sh_l = clavicle_follow((-64.0, -198.0), (-118.0, -206.0), 0.14)
        el_l, hand_l = solve_2bone_ik(sh_l, (-118.0, -206.0), 46.0, 44.0, bend_dir=-1.0)
        sh_r = clavicle_follow((64.0, -198.0), (118.0, -214.0), 0.14)
        el_r, hand_r = solve_2bone_ik(sh_r, (118.0, -214.0), 46.0, 44.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_l, el_l, hand_l, 13.5, 10.5))
        parts.append(draw_stick_limb(svg, sh_r, el_r, hand_r, 13.5, 10.5))
        if with_props:
            parts.append(draw_steel_wrench(svg, (hand_l[0] - 6, hand_l[1] - 14), angle_deg=-26.0, scale=0.92))
            parts.append(draw_rocket_blueprint(svg, (hand_r[0] + 8, hand_r[1] - 12), angle_deg=22.0, scale=0.92))
        parts.append(draw_hand(svg, hand_l, angle_deg=-18.0, skin_color=skin, pose="grip", flip_y=True))
        parts.append(draw_hand(svg, hand_r, angle_deg=18.0, skin_color=skin, pose="grip"))

    parts.append(f'<path d="{pill_d}" fill="{skin_g}"/>')

    # ---- CLIPPED INDUSTRIAL SHIRT + OVERALLS (FRONT/SIDE/BACK X-STRAPS!) ----
    parts.append(f'<g clip-path="{pill_clip}">')
    parts.append(
        f'<path d="M -86,{fmt(neck_y)} Q 0,{fmt(neck_y + 14)} 86,{fmt(neck_y)} '
        f'L 86,-120 L -86,-120 Z" fill="{shirt_g}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
    )
    parts.append(f'<path d="M -84,-154 Q 0,-142 84,-154 L 84,-72 L -84,-72 Z" fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>')

    if angle_key == "three_quarter":
        parts.append(
            f'<path d="M -16,-206 Q 22,-198 58,-206 L 60,-146 Q 22,-138 -18,-146 Z" fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            f'<path d="M -18,{fmt(neck_y + 2)} L -6,{fmt(neck_y + 4)} L -4,-196 L -16,-196 Z" fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
            f'<path d="M 44,{fmt(neck_y + 4)} L 56,{fmt(neck_y + 2)} L 52,-196 L 40,-196 Z" fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
            f'<circle cx="-10" cy="-195" r="5.2" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
            f'<circle cx="46" cy="-195" r="5.2" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
            f'<rect x="26" y="-203" width="6" height="20" rx="1.5" transform="rotate(14 29 -193)" fill="#F7D046" stroke="{INK_COLOR}" stroke-width="1.8"/>'
            f'<path d="M 0,-184 Q 22,-180 42,-184 L 40,-158 Q 22,-152 2,-158 Z" fill="{lighten(denim, 0.10)}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
            # Leather tool belt + side pouch
            f'<path d="M -82,-134 Q 0,-120 82,-134 L 82,-120 Q 0,-106 -82,-120 Z" fill="#69391B" stroke="{INK_COLOR}" stroke-width="3.0"/>'
            f'<path d="M -52,-129 L -24,-125 L -26,-102 Q -38,-98 -50,-104 Z" fill="#8A4E27" stroke="{INK_COLOR}" stroke-width="2.6"/>'
            f'<rect x="12" y="-128" width="20" height="14" rx="3" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        )
    elif angle_key == "side":
        # Side view: overall strap over shoulder, side denim bib profile, prominent hip tool pouch & brass side button!
        parts.append(
            f'<path d="M 18,-204 L 68,-204 L 68,-148 L 16,-148 Z" fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
            f'<path d="M -8,{fmt(neck_y + 2)} L 12,{fmt(neck_y + 2)} L 32,-198 L 16,-198 Z" fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
            f'<circle cx="14" cy="-152" r="5.0" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
            f'<path d="M -82,-134 Q 0,-120 82,-134 L 82,-120 Q 0,-106 -82,-120 Z" fill="#69391B" stroke="{INK_COLOR}" stroke-width="3.0"/>'
            f'<path d="M -22,-130 L 14,-126 L 12,-100 Q -4,-96 -20,-102 Z" fill="#8A4E27" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
            f'<line x1="-18" y1="-119" x2="10" y2="-117" stroke="#F5D99B" stroke-width="2.0" stroke-dasharray="4 3"/>'
        )
    else:
        # Back 3/4 & Full 180° Back: ICONIC CROSSED DENIM OVERALL X-STRAPS + TWIN REAR POCKETS + TOOL BELT!!
        ox = -14.0 if angle_key == "back_three_quarter" else 0.0
        parts.append(
            # Shirt collar back fold
            f'<path d="M -52,{fmt(neck_y - 2)} Q 0,{fmt(neck_y + 12)} 52,{fmt(neck_y - 2)} '
            f'L 46,{fmt(neck_y + 12)} Q 0,{fmt(neck_y + 22)} -46,{fmt(neck_y + 12)} Z" fill="{lighten(shirt, 0.14)}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
            # Denim X-straps crossing crisply across her back!
            f'<path d="M {fmt(ox - 46)},{fmt(neck_y + 2)} L {fmt(ox - 30)},{fmt(neck_y + 4)} L {fmt(ox + 38)},-148 L {fmt(ox + 20)},-148 Z" '
            f'fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
            f'<path d="M {fmt(ox + 30)},{fmt(neck_y + 4)} L {fmt(ox + 46)},{fmt(neck_y + 2)} L {fmt(ox - 20)},-148 L {fmt(ox - 38)},-148 Z" '
            f'fill="{denim_g}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
            # Center X stitch square + leather belt + rear denim patch pockets!
            f'<rect x="{fmt(ox - 8)}" y="-188" width="16" height="14" rx="2" fill="none" stroke="#F5D99B" stroke-width="1.8" stroke-dasharray="3 2"/>'
            f'<path d="M -82,-134 Q 0,-120 82,-134 L 82,-120 Q 0,-106 -82,-120 Z" fill="#69391B" stroke="{INK_COLOR}" stroke-width="3.0"/>'
            f'<rect x="{fmt(ox - 42)}" y="-114" width="32" height="24" rx="4" fill="{lighten(denim, 0.08)}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
            f'<rect x="{fmt(ox + 10)}" y="-114" width="32" height="24" rx="4" fill="{lighten(denim, 0.08)}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
            # Brass belt loops
            f'<rect x="{fmt(ox - 32)}" y="-131" width="8" height="18" rx="2" fill="#472611" stroke="{INK_COLOR}" stroke-width="1.8"/>'
            f'<rect x="{fmt(ox + 24)}" y="-131" width="8" height="18" rx="2" fill="#472611" stroke="{INK_COLOR}" stroke-width="1.8"/>'
        )
    parts.append("</g>")

    parts.append(_draw_capsule_volume_overlay(svg, pill_clip, 0.0, top_y, 150 * w_fac, pill_h))
    parts.append(variable_ink_closed(pts, min_w=3.2, max_w=7.6))

    # ---- HAIR + DOMED 3D HARD HAT + GOGGLES + FACE PER ANGLE ----
    if angle_key == "three_quarter":
        parts.append(
            f'<path d="M -60,{fmt(top_y + 52)} C -62,{fmt(top_y + 18)} -44,{fmt(top_y - 4)} 4,{fmt(top_y - 4)} '
            f'C 46,{fmt(top_y - 4)} 60,{fmt(top_y + 16)} 56,{fmt(top_y + 42)} '
            f'C 44,{fmt(top_y + 26)} 28,{fmt(top_y + 26)} 14,{fmt(top_y + 38)} '
            f'C -4,{fmt(top_y + 24)} -24,{fmt(top_y + 34)} -38,{fmt(top_y + 52)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linejoin="round"/>'
        )
        parts.append(
            f'<g transform="translate(22,0) scale(0.86,1.0)">'
            + draw_expression(svg, expression, 0.0, face_cy, skin_color=skin, brow_color="#592C19", scale=0.92)
            + "</g>"
        )
        # 3/4 Domed Hard Hat with projecting front-right brim + angled goggles!
        parts.append(
            f'<path d="M -66,{fmt(top_y + 20)} C -68,{fmt(top_y - 36)} -34,{fmt(top_y - 56)} 2,{fmt(top_y - 56)} '
            f'C 38,{fmt(top_y - 56)} 68,{fmt(top_y - 34)} 66,{fmt(top_y + 20)} Z" fill="{hat_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
            f'<path d="M 0,{fmt(top_y - 55)} L 20,{fmt(top_y - 53)} L 28,{fmt(top_y + 12)} L 4,{fmt(top_y + 14)} Z" fill="{lighten("#F2B724", 0.16)}" stroke="{INK_COLOR}" stroke-width="3.0"/>'
            f'<path d="M -66,{fmt(top_y + 6)} Q 8,{fmt(top_y + 16)} 66,{fmt(top_y + 4)} L 66,{fmt(top_y - 7)} Q 8,{fmt(top_y + 5)} -66,{fmt(top_y - 5)} Z" fill="#2F3847" stroke="{INK_COLOR}" stroke-width="2.8"/>'
            f'<path d="M -72,{fmt(top_y + 20)} Q 16,{fmt(top_y + 38)} 88,{fmt(top_y + 20)} Q 80,{fmt(top_y + 8)} 64,{fmt(top_y + 12)} Q 8,{fmt(top_y + 25)} -62,{fmt(top_y + 12)} Z" fill="{brim_g}" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linejoin="round"/>'
            # 3/4 Cyan goggles
            f'<rect x="-12" y="{fmt(top_y - 18)}" width="34" height="27" rx="12" fill="#525D6E" stroke="{INK_COLOR}" stroke-width="3.2"/>'
            f'<rect x="30" y="{fmt(top_y - 18)}" width="28" height="26" rx="11" fill="#525D6E" stroke="{INK_COLOR}" stroke-width="3.2"/>'
            f'<rect x="-7" y="{fmt(top_y - 13)}" width="24" height="17" rx="8" fill="{lens_g}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<rect x="34" y="{fmt(top_y - 13)}" width="20" height="16" rx="7" fill="{lens_g}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<line x1="-1" y1="{fmt(top_y - 4)}" x2="8" y2="{fmt(top_y - 10)}" stroke="#FFFFFF" stroke-width="2.8" stroke-linecap="round" opacity="0.85"/>'
            f'<line x1="39" y1="{fmt(top_y - 4)}" x2="47" y2="{fmt(top_y - 10)}" stroke="#FFFFFF" stroke-width="2.8" stroke-linecap="round" opacity="0.85"/>'
        )
    elif angle_key == "side":
        parts.append(_draw_side_profile_face(svg, "clara", expression, 16.0, face_cy, skin, "#592C19"))
        # Underlying bangs & side hair nape securely tucked under helmet crown!
        parts.append(
            f'<path d="M -54,{fmt(top_y + 86)} C -62,{fmt(top_y + 42)} -56,{fmt(top_y - 6)} -2,{fmt(top_y - 6)} '
            f'C 38,{fmt(top_y - 6)} 56,{fmt(top_y + 10)} 52,{fmt(top_y + 34)} '
            f'C 34,{fmt(top_y + 24)} 14,{fmt(top_y + 34)} -4,{fmt(top_y + 28)} '
            f'C -24,{fmt(top_y + 40)} -24,{fmt(top_y + 70)} -54,{fmt(top_y + 86)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linejoin="round"/>'
        )
        # Side-profile domed hard hat with crisp projecting visor brim + perched side goggles!
        parts.append(
            f'<path d="M -64,{fmt(top_y + 20)} C -66,{fmt(top_y - 36)} -32,{fmt(top_y - 56)} 4,{fmt(top_y - 56)} '
            f'C 42,{fmt(top_y - 56)} 66,{fmt(top_y - 30)} 62,{fmt(top_y + 20)} Z" fill="{hat_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
            # Curved goggle strap wrapping around full side dome!
            f'<path d="M -64,{fmt(top_y + 5)} Q 0,{fmt(top_y + 12)} 62,{fmt(top_y + 2)} L 62,{fmt(top_y - 9)} Q 0,{fmt(top_y + 1)} -64,{fmt(top_y - 6)} Z" fill="#2F3847" stroke="{INK_COLOR}" stroke-width="2.8"/>'
            # Projecting front visor brim!
            f'<path d="M -68,{fmt(top_y + 18)} Q 10,{fmt(top_y + 24)} 88,{fmt(top_y + 24)} '
            f'Q 92,{fmt(top_y + 14)} 64,{fmt(top_y + 10)} Q 0,{fmt(top_y + 14)} -66,{fmt(top_y + 10)} Z" '
            f'fill="{brim_g}" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linejoin="round"/>'
            # Side-view perched cyan goggle cup!
            f'<rect x="34" y="{fmt(top_y - 18)}" width="28" height="27" rx="10" fill="#525D6E" stroke="{INK_COLOR}" stroke-width="3.2"/>'
            f'<rect x="44" y="{fmt(top_y - 13)}" width="15" height="17" rx="6" fill="{lens_g}" stroke="{INK_COLOR}" stroke-width="2.2"/>'
            f'<line x1="48" y1="{fmt(top_y - 4)}" x2="55" y2="{fmt(top_y - 10)}" stroke="#FFFFFF" stroke-width="2.8" stroke-linecap="round" opacity="0.88"/>'
            f'<path d="M -38,{fmt(top_y - 18)} Q -18,{fmt(top_y - 44)} 14,{fmt(top_y - 44)}" fill="none" stroke="#FFF9D6" stroke-width="5.5" stroke-linecap="round" opacity="0.8"/>'
        )
    else:
        # Back 3/4 & Full 180° Back: Full underlying chestnut hair nape + hard hat rear dome + goggle strap buckle + bouncy ponytail on top!
        px_off = -16.0 if angle_key == "back_three_quarter" else -6.0
        parts.append(
            f'<path d="M -60,{fmt(top_y + 94)} C -68,{fmt(top_y + 42)} -60,{fmt(top_y + 6)} 0,{fmt(top_y + 6)} '
            f'C 60,{fmt(top_y + 6)} 68,{fmt(top_y + 42)} 60,{fmt(top_y + 94)} Q 0,{fmt(top_y + 106)} -60,{fmt(top_y + 94)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linejoin="round"/>'
            # Hard hat rear dome + crest rib + goggle strap buckle
            f'<path d="M -66,{fmt(top_y + 20)} C -68,{fmt(top_y - 36)} -36,{fmt(top_y - 56)} 0,{fmt(top_y - 56)} '
            f'C 36,{fmt(top_y - 56)} 68,{fmt(top_y - 36)} 66,{fmt(top_y + 20)} Z" fill="{hat_g}" stroke="{INK_COLOR}" stroke-width="4.6" stroke-linejoin="round"/>'
            f'<path d="M {fmt(px_off - 12)},{fmt(top_y - 55)} L {fmt(px_off + 12)},{fmt(top_y - 55)} L {fmt(px_off + 15)},{fmt(top_y + 14)} L {fmt(px_off - 15)},{fmt(top_y + 14)} Z" '
            f'fill="{lighten("#F2B724", 0.16)}" stroke="{INK_COLOR}" stroke-width="3.0"/>'
            f'<path d="M -66,{fmt(top_y + 6)} Q 0,{fmt(top_y + 14)} 66,{fmt(top_y + 6)} L 66,{fmt(top_y - 5)} Q 0,{fmt(top_y + 3)} -66,{fmt(top_y - 5)} Z" fill="#2F3847" stroke="{INK_COLOR}" stroke-width="2.8"/>'
            # Rear goggle strap adjuster clip
            f'<rect x="{fmt(px_off - 12)}" y="{fmt(top_y - 7)}" width="24" height="16" rx="3" fill="#525D6E" stroke="{INK_COLOR}" stroke-width="2.6"/>'
            f'<path d="M -72,{fmt(top_y + 20)} Q 0,{fmt(top_y + 32)} 72,{fmt(top_y + 20)} Q 68,{fmt(top_y + 10)} 60,{fmt(top_y + 13)} Q 0,{fmt(top_y + 22)} -60,{fmt(top_y + 13)} Z" '
            f'fill="{brim_g}" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linejoin="round"/>'
            # Lively rear ponytail anchored cleanly below rear helmet brim!
            f'<ellipse cx="{fmt(px_off - 12)}" cy="{fmt(top_y + 44)}" rx="12" ry="8" fill="#F2B724" stroke="{INK_COLOR}" stroke-width="2.8"/>'
            f'<path d="M {fmt(px_off - 18)},{fmt(top_y + 44)} C {fmt(px_off - 48)},{fmt(top_y + 46)} {fmt(px_off - 54)},{fmt(top_y + 92)} {fmt(px_off - 30)},{fmt(top_y + 114)} '
            f'C {fmt(px_off - 12)},{fmt(top_y + 108)} {fmt(px_off - 4)},{fmt(top_y + 82)} {fmt(px_off - 4)},{fmt(top_y + 46)} Z" '
            f'fill="{hair_g}" stroke="{INK_COLOR}" stroke-width="4.2" stroke-linejoin="round"/>'
            f'<path d="M {fmt(px_off - 28)},{fmt(top_y + 56)} Q {fmt(px_off - 40)},{fmt(top_y + 78)} {fmt(px_off - 28)},{fmt(top_y + 98)}" fill="none" stroke="#B87352" stroke-width="3.4" stroke-linecap="round" opacity="0.65"/>'
        )

    # ---- FOREGROUND NEAR ARM ----
    if angle_key == "three_quarter":
        sh_n = clavicle_follow((-54.0, -198.0), (-110.0, -212.0), 0.14)
        el_n, hand_n = solve_2bone_ik(sh_n, (-110.0, -212.0), 46.0, 44.0, bend_dir=-1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 13.5, 10.5))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, shirt, 14.0))
        if with_props:
            parts.append(draw_rocket_blueprint(svg, (hand_n[0] - 8, hand_n[1] - 12), angle_deg=-22.0, scale=0.92))
        parts.append(draw_hand(svg, hand_n, angle_deg=-18.0, skin_color=skin, pose="grip", flip_y=True))
    elif angle_key == "side":
        sh_n = clavicle_follow((-18.0, -198.0), (26.0, -162.0), 0.14)
        el_n, hand_n = solve_2bone_ik(sh_n, (26.0, -162.0), 44.0, 42.0, bend_dir=+1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 13.5, 10.5))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, shirt, 14.0))
        if with_props:
            parts.append(draw_rocket_blueprint(svg, (hand_n[0] + 10, hand_n[1] - 10), angle_deg=18.0, scale=0.90))
        parts.append(draw_hand(svg, hand_n, angle_deg=14.0, skin_color=skin, pose="grip"))
    elif angle_key == "back_three_quarter":
        sh_n = clavicle_follow((-54.0, -198.0), (-110.0, -206.0), 0.14)
        el_n, hand_n = solve_2bone_ik(sh_n, (-110.0, -206.0), 46.0, 44.0, bend_dir=-1.0)
        parts.append(draw_stick_limb(svg, sh_n, el_n, hand_n, 13.5, 10.5))
        parts.append(draw_sleeve_cap(svg, sh_n, el_n, shirt, 14.0))
        if with_props:
            parts.append(draw_steel_wrench(svg, (hand_n[0] - 6, hand_n[1] - 14), angle_deg=-26.0, scale=0.92))
        parts.append(draw_hand(svg, hand_n, angle_deg=-18.0, skin_color=skin, pose="grip", flip_y=True))
    elif angle_key == "back":
        parts.append(draw_sleeve_cap(svg, sh_l, el_l, shirt, 14.0))
        parts.append(draw_sleeve_cap(svg, sh_r, el_r, shirt, 14.0))

    parts.append("</g>")
    return "".join(parts)


ANGLE_DRAWERS = {
    "raka": draw_raka_angle,
    "bima": draw_bima_angle,
    "doni": draw_doni_angle,
    "clara": draw_clara_angle,
}


def draw_character_angle(
    svg: SvgBuilder,
    char_id: str,
    angle_key: str,
    expression: str,
    cx: float = 0.0,
    floor_y: float = 0.0,
    scale: float = 1.0,
    with_props: bool = True,
) -> str:
    return ANGLE_DRAWERS[char_id](
        svg,
        angle_key=angle_key,
        expression=expression,
        cx=cx,
        floor_y=floor_y,
        scale=scale,
        with_props=with_props,
    )
