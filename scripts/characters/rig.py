"""Biomechanical 2-Bone IK solver & stylized 2.5D flexible stick-limb, hand, and 3D shoe renderers."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from .svg_core import (
    INK_COLOR,
    Point,
    SvgBuilder,
    clamp,
    darken,
    fmt,
    lighten,
    pts_to_path,
    sample_quad,
    variable_ink_closed,
)


def clavicle_follow(shoulder: Point, target: Point, factor: float = 0.12, max_shift: float = 11.0) -> Point:
    """Subtle clavicle follow toward reach target so arm posing feels organic and weighted."""
    dx = (target[0] - shoulder[0]) * factor
    dy = (target[1] - shoulder[1]) * factor
    mag = math.hypot(dx, dy)
    if mag > max_shift and mag > 1e-6:
        scale = max_shift / mag
        dx *= scale
        dy *= scale
    return (shoulder[0] + dx, shoulder[1] + dy)


def solve_2bone_ik(
    root: Point,
    target: Point,
    l1: float,
    l2: float,
    bend_dir: float = 1.0,
) -> Tuple[Point, Point]:
    """Exact 2-bone planar IK solver in SVG (+Y down) coordinates.

    Returns (joint_pos, clamped_end_pos).
    bend_dir = +1 bends toward positive perpendicular (-dy, dx); -1 bends opposite.
    """
    rx, ry = root
    tx, ty = target
    dx = tx - rx
    dy = ty - ry
    dist = math.hypot(dx, dy)

    min_d = abs(l1 - l2) + 1.5
    max_d = (l1 + l2) - 0.8
    if dist < 1e-6:
        dx, dy, dist = 0.0, 1.0, 1.0

    clamped_d = clamp(dist, min_d, max_d)
    ux, uy = dx / dist, dy / dist
    end_pos = (rx + ux * clamped_d, ry + uy * clamped_d)

    cos_a = clamp((l1 * l1 + clamped_d * clamped_d - l2 * l2) / (2.0 * l1 * clamped_d), -1.0, 1.0)
    angle = math.acos(cos_a)
    base_angle = math.atan2(uy, ux)
    joint_angle = base_angle + (angle * (1.0 if bend_dir >= 0 else -1.0))

    jx = rx + math.cos(joint_angle) * l1
    jy = ry + math.sin(joint_angle) * l1
    return (jx, jy), end_pos


def _build_tapered_limb_poly(pts: List[Point], w_start: float, w_end: float) -> Tuple[List[Point], List[Point], List[Point]]:
    """Offset a curve centerline into a tapered ribbon plus a sunlit cylindrical highlight ribbon."""
    n = len(pts)
    left: List[Point] = []
    right: List[Point] = []
    hi_pts: List[Point] = []

    for i in range(n):
        if i == 0:
            dx = pts[1][0] - pts[0][0]
            dy = pts[1][1] - pts[0][1]
        elif i == n - 1:
            dx = pts[-1][0] - pts[-2][0]
            dy = pts[-1][1] - pts[-2][1]
        else:
            dx = pts[i + 1][0] - pts[i - 1][0]
            dy = pts[i + 1][1] - pts[i - 1][1]
        mag = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / mag, dx / mag  # perpendicular
        t = i / (n - 1)
        half_w = 0.5 * (w_start + (w_end - w_start) * t)
        cx, cy = pts[i]
        left.append((cx + nx * half_w, cy + ny * half_w))
        right.append((cx - nx * half_w, cy - ny * half_w))

        # Subtle highlight shifted toward upper-left key light
        hi_pts.append((cx - 0.34 * half_w, cy - 0.34 * half_w))

    return left, right, hi_pts


def draw_stick_limb(
    svg: SvgBuilder,
    root: Point,
    joint: Point,
    end: Point,
    w_start: float = 14.0,
    w_end: float = 10.5,
    limb_color: str = "#1C1A24",
    highlight_color: str = "#4E4A63",
    bend_softness: float = 0.72,
) -> str:
    """Render a flexible 2-segment biomechanical stylized stick limb with subtle 3D cylindrical highlight.

    Smoothly blends the 2-bone IK elbow/knee bend into a supple cartoon rubber-hose curve while
    preserving exact anatomical joint direction and crisp silhouette volume.
    """
    # Pull control point slightly toward the solved IK joint for supple yet anatomically faithful flex
    mid_direct = ((root[0] + end[0]) * 0.5, (root[1] + end[1]) * 0.5)
    ctrl = (
        mid_direct[0] + (joint[0] - mid_direct[0]) * (1.0 + bend_softness * 0.55),
        mid_direct[1] + (joint[1] - mid_direct[1]) * (1.0 + bend_softness * 0.55),
    )
    centerline = sample_quad(root, ctrl, end, steps=24)
    left, right, hi_pts = _build_tapered_limb_poly(centerline, w_start, w_end)

    poly = left + list(reversed(right))
    hi_d = pts_to_path(hi_pts[2:-2], closed=False)

    parts = [
        f'<path d="{pts_to_path(poly, closed=True)}" fill="{limb_color}" stroke="{limb_color}" '
        f'stroke-width="1.2" stroke-linejoin="round"/>',
        # Rounded caps at root and end
        f'<circle cx="{fmt(root[0])}" cy="{fmt(root[1])}" r="{fmt(w_start * 0.5)}" fill="{limb_color}"/>',
        f'<circle cx="{fmt(end[0])}" cy="{fmt(end[1])}" r="{fmt(w_end * 0.5)}" fill="{limb_color}"/>',
        # Cylindrical top-left specular sheen along the dark stick limb
        f'<path d="{hi_d}" fill="none" stroke="{highlight_color}" stroke-width="{fmt(w_end * 0.24)}" '
        f'stroke-linecap="round" opacity="0.62"/>',
    ]
    return "<g>" + "".join(parts) + "</g>"


def draw_sleeve_cap(
    svg: SvgBuilder,
    shoulder: Point,
    elbow: Point,
    garment_color: str,
    radius: float = 15.0,
) -> str:
    """Draw a tailored 3D shoulder sleeve cap sealing the arm socket so zero gaps leak."""
    ang = math.degrees(math.atan2(elbow[1] - shoulder[1], elbow[0] - shoulder[0]))
    grad = svg.add_cylindrical_gradient(garment_color, lit_shift=0.22, shadow_shift=0.35)
    cuff_hi = lighten(garment_color, 0.28)
    return (
        f'<g transform="translate({fmt(shoulder[0])},{fmt(shoulder[1])}) rotate({fmt(ang)})">'
        f'<path d="M -8,{fmt(-radius)} Q 16,{fmt(-radius * 0.92)} 20,{fmt(-radius * 0.62)} '
        f'L 20,{fmt(radius * 0.62)} Q 16,{fmt(radius * 0.92)} -8,{fmt(radius)} '
        f'Q -14,0 -8,{fmt(-radius)} Z" fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.4" stroke-linejoin="round"/>'
        f'<path d="M -4,{fmt(-radius * 0.62)} Q 8,{fmt(-radius * 0.6)} 15,{fmt(-radius * 0.42)}" '
        f'fill="none" stroke="{cuff_hi}" stroke-width="2.4" stroke-linecap="round" opacity="0.65"/>'
        f"</g>"
    )


def draw_hand(
    svg: SvgBuilder,
    pos: Point,
    angle_deg: float = 0.0,
    skin_color: str = "#FAD7B8",
    scale: float = 1.0,
    pose: str = "relaxed",
    flip_y: bool = False,
) -> str:
    """Draw a stylized expressive 2.5D rounded cartoon mitten hand with thumb & 3D shading."""
    grad = svg.add_radial_gradient(
        [
            (0.0, lighten(skin_color, 0.20), 1.0),
            (0.60, skin_color, 1.0),
            (1.0, darken(skin_color, 0.24), 1.0),
        ],
        cx=0.32,
        cy=0.28,
        r=0.78,
    )
    sy = -scale if flip_y else scale
    x, y = pos

    if pose == "grip":
        body = (
            f'<ellipse cx="3" cy="0" rx="13.5" ry="11.5" fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.6"/>'
            f'<path d="M -3,-8 Q 4,-16 11,-9 Q 13,-3 7,-1" fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.3" stroke-linecap="round"/>'
            f'<path d="M 5,-4 Q 11,-3 12,3" fill="none" stroke="{darken(skin_color, 0.32)}" stroke-width="2.2" stroke-linecap="round"/>'
            f'<ellipse cx="-1" cy="-4.5" rx="3.5" ry="2.0" fill="#FFFFFF" opacity="0.55"/>'
        )
    elif pose == "point":
        body = (
            f'<path d="M -9,-7 Q -2,-13 10,-9 L 22,-8 Q 26,-7 26,-3 Q 26,1 21,2 L 10,3 '
            f'Q 12,11 3,12 Q -9,12 -11,3 Q -12,-3 -9,-7 Z" fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
            f'<path d="M -2,-9 Q 3,-17 9,-11" fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linecap="round"/>'
            f'<ellipse cx="0" cy="-4" rx="4.2" ry="2.0" fill="#FFFFFF" opacity="0.52"/>'
        )
    elif pose == "palm_up":
        body = (
            f'<path d="M -10,-4 Q 0,-11 15,-8 Q 21,-6 20,-1 Q 19,5 12,7 L -2,9 Q -11,8 -12,1 Z" '
            f'fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
            f'<path d="M -2,-8 Q 3,-16 9,-11" fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.2" stroke-linecap="round"/>'
            f'<ellipse cx="3" cy="-3.5" rx="5.0" ry="2.1" fill="#FFFFFF" opacity="0.5"/>'
        )
    else:  # relaxed open hand
        body = (
            f'<path d="M -10,-6 Q -1,-13 12,-9 Q 18,-6 17,2 Q 16,10 6,11 Q -8,12 -11,4 Z" '
            f'fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
            f'<path d="M -3,-9 Q 2,-16 8,-10" fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.1" stroke-linecap="round"/>'
            f'<ellipse cx="1" cy="-4.5" rx="4.0" ry="2.1" fill="#FFFFFF" opacity="0.55"/>'
        )

    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)},{fmt(sy)})">'
        f"{body}</g>"
    )


def draw_shoe(
    svg: SvgBuilder,
    ankle: Point,
    facing: float = 1.0,
    color: str = "#2A2428",
    sole_color: str = "#161318",
    style: str = "oxford",
    scale: float = 1.0,
) -> str:
    """Draw a 3D-shaded stylized cartoon shoe grounded on the floor plane (ankle_y + 18*scale)."""
    x, y = ankle
    sx = scale * (1.0 if facing >= 0 else -1.0)

    grad = svg.add_linear_gradient(
        [
            (0.0, lighten(color, 0.28), 1.0),
            (0.45, color, 1.0),
            (1.0, darken(color, 0.36), 1.0),
        ],
        x1=0.1,
        y1=0.0,
        x2=0.85,
        y2=1.0,
    )

    if style == "boot":
        # Chunky industrial steel-toe work boot for Clara
        upper_d = (
            "M -15,-7 L 10,-7 Q 18,-6 24,1 Q 34,3 37,11 Q 38,16 32,17 "
            "L -16,17 Q -20,16 -19,9 L -18,-3 Q -18,-7 -15,-7 Z"
        )
        sole = (
            f'<path d="M -18,14 L 35,14 Q 37,19 32,20 L -15,20 Q -20,19 -18,14 Z" '
            f'fill="{sole_color}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
        )
        details = (
            # Steel toe cap crease & specular
            f'<path d="M 19,2 Q 24,8 23,14" fill="none" stroke="{darken(color, 0.4)}" stroke-width="2.2"/>'
            f'<ellipse cx="26" cy="7" rx="6.0" ry="2.8" transform="rotate(14 26 7)" fill="#FFFFFF" opacity="0.45"/>'
            # Laces
            f'<line x1="6" y1="-2" x2="13" y2="-1" stroke="#F0D28C" stroke-width="2.6" stroke-linecap="round"/>'
            f'<line x1="8" y1="3" x2="15" y2="4" stroke="#F0D28C" stroke-width="2.6" stroke-linecap="round"/>'
        )
    elif style == "loafer":
        # Sleek warm suede casual loafer for Raka
        upper_d = (
            "M -15,-2 L 8,-2 Q 16,-1 22,4 Q 35,6 37,13 Q 37,17 31,17 "
            "L -15,17 Q -19,16 -18,9 L -17,1 Q -17,-2 -15,-2 Z"
        )
        sole = (
            f'<path d="M -17,15 L 35,15 Q 36,19 31,19.5 L -14,19.5 Q -19,19 -17,15 Z" '
            f'fill="{sole_color}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        )
        details = (
            f'<path d="M 8,3 Q 15,7 22,5" fill="none" stroke="{lighten(color, 0.35)}" stroke-width="2.5" stroke-linecap="round"/>'
            f'<ellipse cx="25" cy="9.5" rx="6.5" ry="2.2" transform="rotate(10 25 9.5)" fill="#FFFFFF" opacity="0.32"/>'
        )
    else:
        # Classic Art Deco glossy oxford dress shoe for Pak Bima & Pak Doni
        upper_d = (
            "M -15,-3 L 8,-3 Q 15,-2 21,4 Q 35,5 38,12 Q 39,17 32,17 "
            "L -15,17 Q -19,16 -18,9 L -17,0 Q -17,-3 -15,-3 Z"
        )
        sole = (
            f'<path d="M -17,15 L 36,15 Q 37,19 32,19.5 L -1,19.5 L -3,17.5 L -7,19.5 L -15,19.5 Q -19,19 -17,15 Z" '
            f'fill="{sole_color}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        )
        details = (
            f'<path d="M 20,5 Q 24,10 23,15" fill="none" stroke="{darken(color, 0.45)}" stroke-width="2.0"/>'
            f'<ellipse cx="26.5" cy="9.2" rx="7.0" ry="2.5" transform="rotate(14 26.5 9.2)" fill="#FFFFFF" opacity="0.52"/>'
            f'<ellipse cx="2" cy="4.5" rx="5.0" ry="1.8" fill="#FFFFFF" opacity="0.22"/>'
        )

    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) scale({fmt(sx)},{fmt(scale)})">'
        f'<path d="{upper_d}" fill="{grad}" stroke="{INK_COLOR}" stroke-width="3.8" stroke-linejoin="round"/>'
        f"{details}{sole}</g>"
    )
