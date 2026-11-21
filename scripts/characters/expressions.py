"""Swappable 2.5D Cartoon Facial Expression Engine with gaze tracking, asymmetric brows & comic FX."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .svg_core import INK_COLOR, SvgBuilder, darken, fmt, lighten, mix_color


def _eye_open(
    svg: SvgBuilder,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    gx: float,
    gy: float,
    pupil_r: float,
    skin_color: str,
    top_lid: float = 0.0,
    bot_lid: float = 0.0,
    lid_tilt_deg: float = 0.0,
    sparkle: bool = False,
) -> str:
    """Render a crisp 2.5D expressive cartoon eye with upper/lower eyelids, gaze offset, and specular glint."""
    clip_id = svg.add_clip_path(f'<ellipse cx="{fmt(cx)}" cy="{fmt(cy)}" rx="{fmt(rx)}" ry="{fmt(ry)}"/>')
    px = cx + gx * (rx * 0.42)
    py = cy + gy * (ry * 0.36)

    sclera_grad = svg.add_linear_gradient(
        [(0.0, "#E4E8F2", 1.0), (0.28, "#FFFFFF", 1.0), (1.0, "#F7F8FC", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=0.0,
        y2=1.0,
    )
    lid_col = mix_color(skin_color, "#D49B7A", 0.25)

    parts = [
        f'<ellipse cx="{fmt(cx)}" cy="{fmt(cy)}" rx="{fmt(rx)}" ry="{fmt(ry)}" fill="{sclera_grad}"/>',
        f'<g clip-path="{clip_id}">',
        # Pupil
        f'<circle cx="{fmt(px)}" cy="{fmt(py)}" r="{fmt(pupil_r)}" fill="{INK_COLOR}"/>',
        # Primary bright catchlight
        f'<circle cx="{fmt(px - pupil_r * 0.34)}" cy="{fmt(py - pupil_r * 0.34)}" '
        f'r="{fmt(max(1.8, pupil_r * 0.34))}" fill="#FFFFFF"/>',
    ]
    if sparkle:
        parts.append(
            f'<circle cx="{fmt(px + pupil_r * 0.36)}" cy="{fmt(py + pupil_r * 0.32)}" '
            f'r="{fmt(max(1.2, pupil_r * 0.2))}" fill="#FFFFFF" opacity="0.9"/>'
        )
    # Upper eyelid
    if top_lid > 0.01:
        lid_h = ry * 2.0 * top_lid
        lid_y = cy - ry - 4.0
        parts.append(
            f'<g transform="rotate({fmt(lid_tilt_deg)} {fmt(cx)} {fmt(cy)})">'
            f'<rect x="{fmt(cx - rx - 8)}" y="{fmt(lid_y)}" width="{fmt(rx * 2 + 16)}" '
            f'height="{fmt(lid_h + 4)}" fill="{lid_col}"/>'
            f'<line x1="{fmt(cx - rx - 8)}" y1="{fmt(lid_y + lid_h + 4)}" '
            f'x2="{fmt(cx + rx + 8)}" y2="{fmt(lid_y + lid_h + 4)}" '
            f'stroke="{INK_COLOR}" stroke-width="3.2"/>'
            f"</g>"
        )
    # Lower eyelid (cheek push for smirks/anger/impatience)
    if bot_lid > 0.01:
        blid_h = ry * 2.0 * bot_lid
        blid_y = cy + ry - blid_h
        parts.append(
            f'<rect x="{fmt(cx - rx - 8)}" y="{fmt(blid_y)}" width="{fmt(rx * 2 + 16)}" '
            f'height="{fmt(blid_h + 6)}" fill="{lid_col}"/>'
            f'<line x1="{fmt(cx - rx - 8)}" y1="{fmt(blid_y)}" '
            f'x2="{fmt(cx + rx + 8)}" y2="{fmt(blid_y)}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        )
    parts.append("</g>")
    # Crisp outer ink rim
    parts.append(
        f'<ellipse cx="{fmt(cx)}" cy="{fmt(cy)}" rx="{fmt(rx)}" ry="{fmt(ry)}" '
        f'fill="none" stroke="{INK_COLOR}" stroke-width="3.3"/>'
    )
    return "".join(parts)


def _eye_closed_arc(cx: float, cy: float, rx: float, arch: float = -10.0) -> str:
    """Happy ^ ^ (arch < 0) or relieved u u (arch > 0) curved closed eye."""
    return (
        f'<path d="M {fmt(cx - rx)},{fmt(cy)} Q {fmt(cx)},{fmt(cy + arch)} {fmt(cx + rx)},{fmt(cy)}" '
        f'fill="none" stroke="{INK_COLOR}" stroke-width="4.4" stroke-linecap="round"/>'
    )


def _eye_squeeze(cx: float, cy: float, rx: float, is_left: bool) -> str:
    """Tight stressed > < eye."""
    if is_left:
        d = f"M {fmt(cx - rx)},{fmt(cy - 8)} L {fmt(cx + rx * 0.7)},{fmt(cy)} L {fmt(cx - rx)},{fmt(cy + 8)}"
    else:
        d = f"M {fmt(cx + rx)},{fmt(cy - 8)} L {fmt(cx - rx * 0.7)},{fmt(cy)} L {fmt(cx + rx)},{fmt(cy + 8)}"
    return (
        f'<path d="{d}" fill="none" stroke="{INK_COLOR}" stroke-width="4.4" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )


def _brow(x1: float, y1: float, x2: float, y2: float, bend: float, color: str, thickness: float = 5.4) -> str:
    mx = (x1 + x2) * 0.5
    my = (y1 + y2) * 0.5 + bend
    return (
        f'<path d="M {fmt(x1)},{fmt(y1)} Q {fmt(mx)},{fmt(my)} {fmt(x2)},{fmt(y2)}" '
        f'fill="none" stroke="{color}" stroke-width="{fmt(thickness)}" stroke-linecap="round"/>'
    )


def _cheek_blush(svg: SvgBuilder, cx: float, cy: float, spread: float, color: str = "#F27A6E", opacity: float = 0.42) -> str:
    # Clean radial gradient fading to alpha=0 of the SAME blush color (never black!)
    g = svg.add_radial_gradient([(0.0, color, opacity), (1.0, color, 0.0)], cx=0.5, cy=0.5, r=0.5)
    return (
        f'<ellipse cx="{fmt(cx - spread)}" cy="{fmt(cy)}" rx="15" ry="8.5" fill="{g}"/>'
        f'<ellipse cx="{fmt(cx + spread)}" cy="{fmt(cy)}" rx="15" ry="8.5" fill="{g}"/>'
    )


def _sweat_drop(svg: SvgBuilder, x: float, y: float, scale: float = 1.0) -> str:
    grad = svg.add_linear_gradient(
        [(0.0, "#D8F6FF", 1.0), (0.55, "#6AD5F5", 1.0), (1.0, "#2B94C7", 1.0)],
        x1=0.2,
        y1=0.0,
        x2=0.8,
        y2=1.0,
    )
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) scale({fmt(scale)})">'
        f'<path d="M 0,-13 C 6,-3 10,3 9,9 C 8,14 4,16 0,16 C -4,16 -8,14 -9,9 C -10,3 -6,-3 0,-13 Z" '
        f'fill="{grad}" stroke="{INK_COLOR}" stroke-width="2.6" stroke-linejoin="round"/>'
        f'<path d="M -3.5,2 C -4.5,6 -3.5,10 -1.5,11" fill="none" stroke="#FFFFFF" '
        f'stroke-width="2.3" stroke-linecap="round" opacity="0.88"/>'
        f"</g>"
    )


def _anger_vein(x: float, y: float, scale: float = 1.0) -> str:
    c = "#D92B2B"
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) scale({fmt(scale)})" '
        f'fill="none" stroke="{c}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M -9,-2 Q -3,-2 -2,-9"/>'
        f'<path d="M 9,-2 Q 3,-2 2,-9"/>'
        f'<path d="M -9,3 Q -3,3 -2,10"/>'
        f'<path d="M 9,3 Q 3,3 2,10"/>'
        f"</g>"
    )


def _sparkle_star(x: float, y: float, size: float = 12.0, color: str = "#FFD54A") -> str:
    s = size
    m = size * 0.26
    d = (
        f"M 0,{fmt(-s)} Q {fmt(m)},{fmt(-m)} {fmt(s)},0 "
        f"Q {fmt(m)},{fmt(m)} 0,{fmt(s)} "
        f"Q {fmt(-m)},{fmt(m)} {fmt(-s)},0 "
        f"Q {fmt(-m)},{fmt(-m)} 0,{fmt(-s)} Z"
    )
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)})">'
        f'<path d="{d}" fill="{color}" stroke="{INK_COLOR}" stroke-width="2.0" stroke-linejoin="round"/>'
        f'<circle cx="0" cy="0" r="{fmt(s * 0.16)}" fill="#FFFFFF"/>'
        f"</g>"
    )


def draw_expression(
    svg: SvgBuilder,
    expression: str,
    cx: float,
    cy: float,
    skin_color: str = "#FAD7B8",
    brow_color: str = "#261E1C",
    scale: float = 1.0,
    gaze: Optional[Tuple[float, float]] = None,
    has_mustache: bool = False,
    mustache_color: str = "#363B48",
) -> str:
    """Render a complete swappable facial expression centered at (cx, cy).

    Supported expressions:
    chill, aha, smug, thinking, deadpan, laugh, panic, stressed, shocked,
    skeptical, relieved, proud, furious, impatient, stunned, narcissistic,
    happy, excited, determined, confused.
    """
    e = expression.lower().strip()
    gx, gy = gaze if gaze is not None else (0.0, 0.0)

    # Default gaze overrides per emotional beat if caller didn't override
    if gaze is None:
        default_gazes: Dict[str, Tuple[float, float]] = {
            "chill": (0.18, 0.05),
            "smug": (0.38, -0.05),
            "thinking": (-0.36, -0.45),
            "skeptical": (0.30, 0.0),
            "impatient": (0.42, 0.15),
            "narcissistic": (0.25, 0.08),
            "furious": (0.20, 0.12),
            "confused": (-0.25, -0.15),
            "deadpan": (0.0, 0.05),
        }
        gx, gy = default_gazes.get(e, (0.08, 0.0))

    lx, rx = -21.0, 21.0
    ey = -4.0
    my = 22.0
    parts = [f'<g transform="translate({fmt(cx)},{fmt(cy)}) scale({fmt(scale)})">']

    # --- 1. BLUSH LAYER (behind mouth/eyes) ---
    if e in ("laugh", "happy", "relieved", "proud", "excited"):
        parts.append(_cheek_blush(svg, 0.0, 12.0, 31.0, "#F57E72", 0.42))
    elif e == "narcissistic":
        parts.append(_cheek_blush(svg, 0.0, 12.0, 31.0, "#F77B8B", 0.48))
    elif e == "furious":
        parts.append(_cheek_blush(svg, 0.0, 10.0, 30.0, "#E04438", 0.34))

    # --- 2. EYES ---
    if e == "chill":
        parts.append(_eye_open(svg, lx, ey, 11.5, 12.5, gx, gy, 5.2, skin_color, top_lid=0.36))
        parts.append(_eye_open(svg, rx, ey, 11.5, 12.5, gx, gy, 5.2, skin_color, top_lid=0.36))
    elif e == "aha":
        parts.append(_eye_open(svg, lx, ey - 1, 13.0, 15.0, gx, gy, 6.2, skin_color, sparkle=True))
        parts.append(_eye_open(svg, rx, ey - 1, 13.0, 15.0, gx, gy, 6.2, skin_color, sparkle=True))
    elif e == "smug":
        parts.append(_eye_open(svg, lx, ey, 11.8, 12.2, gx, gy, 5.2, skin_color, top_lid=0.40, bot_lid=0.14, lid_tilt_deg=5))
        parts.append(_eye_open(svg, rx, ey, 11.8, 12.2, gx, gy, 5.2, skin_color, top_lid=0.34, bot_lid=0.14, lid_tilt_deg=-6))
    elif e == "thinking":
        parts.append(_eye_open(svg, lx, ey, 11.5, 12.5, gx, gy, 5.0, skin_color, top_lid=0.22))
        parts.append(_eye_open(svg, rx, ey, 12.0, 13.5, gx, gy, 5.0, skin_color, top_lid=0.05))
    elif e == "deadpan":
        parts.append(_eye_open(svg, lx, ey, 11.5, 11.5, gx, gy, 4.6, skin_color, top_lid=0.48))
        parts.append(_eye_open(svg, rx, ey, 11.5, 11.5, gx, gy, 4.6, skin_color, top_lid=0.48))
    elif e == "laugh":
        parts.append(_eye_closed_arc(lx, ey + 2, 11.5, arch=-13.0))
        parts.append(_eye_closed_arc(rx, ey + 2, 11.5, arch=-13.0))
    elif e == "relieved":
        parts.append(_eye_closed_arc(lx, ey + 1, 11.0, arch=10.0))
        parts.append(_eye_closed_arc(rx, ey + 1, 11.0, arch=10.0))
    elif e == "panic":
        # Asymmetric O_o wide eyes with tiny stressed pupils!
        parts.append(_eye_open(svg, lx, ey - 1, 14.5, 16.0, -0.1, 0.05, 3.6, skin_color))
        parts.append(_eye_open(svg, rx, ey + 1, 11.5, 12.8, 0.12, -0.05, 3.2, skin_color))
    elif e == "stressed":
        parts.append(_eye_squeeze(lx, ey, 10.5, is_left=True))
        parts.append(_eye_squeeze(rx, ey, 10.5, is_left=False))
    elif e == "shocked":
        parts.append(_eye_open(svg, lx, ey - 2, 15.0, 17.0, 0.0, 0.0, 3.8, skin_color))
        parts.append(_eye_open(svg, rx, ey - 2, 15.0, 17.0, 0.0, 0.0, 3.8, skin_color))
    elif e == "skeptical":
        parts.append(_eye_open(svg, lx, ey, 11.5, 11.8, gx, gy, 4.8, skin_color, top_lid=0.44, bot_lid=0.14))
        parts.append(_eye_open(svg, rx, ey - 1, 12.5, 13.5, gx, gy, 5.0, skin_color, top_lid=0.16, bot_lid=0.10))
    elif e == "proud":
        parts.append(_eye_open(svg, lx, ey, 12.2, 13.5, gx, gy, 6.0, skin_color, bot_lid=0.16, sparkle=True))
        parts.append(_eye_open(svg, rx, ey, 12.2, 13.5, gx, gy, 6.0, skin_color, bot_lid=0.16, sparkle=True))
    elif e == "furious":
        parts.append(_eye_open(svg, lx, ey, 12.2, 13.0, gx, gy, 4.6, skin_color, top_lid=0.30, lid_tilt_deg=18))
        parts.append(_eye_open(svg, rx, ey, 12.2, 13.0, gx, gy, 4.6, skin_color, top_lid=0.30, lid_tilt_deg=-18))
    elif e == "impatient":
        parts.append(_eye_open(svg, lx, ey, 12.0, 12.0, gx, gy, 4.8, skin_color, top_lid=0.45, bot_lid=0.12))
        parts.append(_eye_open(svg, rx, ey, 12.0, 12.0, gx, gy, 4.8, skin_color, top_lid=0.45, bot_lid=0.12))
    elif e == "stunned":
        # O_o double-take moment when catching reflection in the mirror!
        parts.append(_eye_open(svg, lx, ey - 1, 14.2, 15.5, 0.15, 0.0, 5.2, skin_color, sparkle=True))
        parts.append(_eye_open(svg, rx, ey, 11.2, 12.2, 0.15, 0.0, 4.4, skin_color, top_lid=0.18))
    elif e == "narcissistic":
        # Dreamy half-lidded "Blue Steel" smolder + sparkles!
        parts.append(_eye_open(svg, lx, ey, 12.0, 12.5, gx, gy, 5.6, skin_color, top_lid=0.38, bot_lid=0.16, lid_tilt_deg=6, sparkle=True))
        parts.append(_eye_open(svg, rx, ey, 12.0, 12.5, gx, gy, 5.6, skin_color, top_lid=0.38, bot_lid=0.16, lid_tilt_deg=-6, sparkle=True))
    elif e in ("happy", "excited"):
        parts.append(_eye_open(svg, lx, ey - 1, 12.8, 14.8, gx, gy, 6.2, skin_color, sparkle=True))
        parts.append(_eye_open(svg, rx, ey - 1, 12.8, 14.8, gx, gy, 6.2, skin_color, sparkle=True))
    elif e == "determined":
        parts.append(_eye_open(svg, lx, ey, 12.0, 13.0, gx, gy, 5.6, skin_color, top_lid=0.26, lid_tilt_deg=12, sparkle=True))
        parts.append(_eye_open(svg, rx, ey, 12.0, 13.0, gx, gy, 5.6, skin_color, top_lid=0.26, lid_tilt_deg=-12, sparkle=True))
    elif e == "confused":
        parts.append(_eye_open(svg, lx, ey + 1, 10.6, 11.5, gx, gy, 4.2, skin_color, top_lid=0.22))
        parts.append(_eye_open(svg, rx, ey - 1, 14.0, 15.5, gx, gy, 4.6, skin_color))
    else:
        parts.append(_eye_open(svg, lx, ey, 12.0, 13.2, gx, gy, 5.5, skin_color))
        parts.append(_eye_open(svg, rx, ey, 12.0, 13.2, gx, gy, 5.5, skin_color))

    # --- 3. EYEBROWS (dramatic, asymmetric, narrative-driven) ---
    if e == "chill":
        parts.append(_brow(lx - 11, -21, lx + 10, -23, -3.5, brow_color, 4.8))
        parts.append(_brow(rx - 10, -24, rx + 11, -21, -4.0, brow_color, 4.8))
    elif e in ("aha", "excited"):
        parts.append(_brow(lx - 12, -26, lx + 10, -30, -6.5, brow_color, 5.2))
        parts.append(_brow(rx - 10, -30, rx + 12, -26, -6.5, brow_color, 5.2))
    elif e == "smug":
        parts.append(_brow(lx - 11, -20, lx + 11, -22, -2.5, brow_color, 5.0))
        parts.append(_brow(rx - 10, -26, rx + 12, -28, -6.5, brow_color, 5.0))
    elif e == "thinking":
        parts.append(_brow(lx - 12, -21, lx + 10, -18, 2.0, brow_color, 5.0))
        parts.append(_brow(rx - 10, -27, rx + 12, -29, -6.0, brow_color, 5.0))
    elif e == "deadpan":
        parts.append(_brow(lx - 12, -19, lx + 11, -19, 0.0, brow_color, 5.0))
        parts.append(_brow(rx - 11, -19, rx + 12, -19, 0.0, brow_color, 5.0))
    elif e in ("laugh", "happy", "proud"):
        parts.append(_brow(lx - 11, -23, lx + 10, -27, -5.0, brow_color, 5.0))
        parts.append(_brow(rx - 10, -27, rx + 11, -23, -5.0, brow_color, 5.0))
    elif e == "relieved":
        parts.append(_brow(lx - 12, -18, lx + 10, -23, -4.0, brow_color, 4.6))
        parts.append(_brow(rx - 10, -23, rx + 12, -18, -4.0, brow_color, 4.6))
    elif e == "panic":
        parts.append(_brow(lx - 13, -24, lx + 10, -33, -5.0, brow_color, 5.4))
        parts.append(_brow(rx - 10, -31, rx + 13, -22, -4.0, brow_color, 5.4))
    elif e == "stressed":
        parts.append(_brow(lx - 12, -23, lx + 10, -14, -2.0, brow_color, 5.6))
        parts.append(_brow(rx - 10, -14, rx + 12, -23, -2.0, brow_color, 5.6))
    elif e == "shocked":
        parts.append(_brow(lx - 12, -31, lx + 10, -34, -7.0, brow_color, 5.2))
        parts.append(_brow(rx - 10, -34, rx + 12, -31, -7.0, brow_color, 5.2))
    elif e == "skeptical":
        parts.append(_brow(lx - 12, -19, lx + 10, -17, 1.5, brow_color, 5.4))
        parts.append(_brow(rx - 10, -26, rx + 12, -28, -6.5, brow_color, 5.4))
    elif e == "furious":
        parts.append(_brow(lx - 13, -24, lx + 11, -13, -1.0, brow_color, 6.2))
        parts.append(_brow(rx - 11, -13, rx + 13, -24, -1.0, brow_color, 6.2))
    elif e == "impatient":
        parts.append(_brow(lx - 12, -19, lx + 11, -16, 1.0, brow_color, 5.4))
        parts.append(_brow(rx - 11, -16, rx + 12, -19, 1.0, brow_color, 5.4))
    elif e == "stunned":
        parts.append(_brow(lx - 12, -28, lx + 10, -31, -6.5, brow_color, 5.2))
        parts.append(_brow(rx - 10, -21, rx + 12, -23, -2.5, brow_color, 5.2))
    elif e == "narcissistic":
        parts.append(_brow(lx - 12, -22, lx + 10, -25, -5.5, brow_color, 5.4))
        parts.append(_brow(rx - 10, -24, rx + 12, -20, -4.5, brow_color, 5.4))
    elif e == "determined":
        parts.append(_brow(lx - 12, -23, lx + 10, -16, -2.0, brow_color, 5.6))
        parts.append(_brow(rx - 10, -16, rx + 12, -23, -2.0, brow_color, 5.6))
    elif e == "confused":
        parts.append(_brow(lx - 12, -19, lx + 10, -21, 2.0, brow_color, 5.2))
        parts.append(_brow(rx - 10, -29, rx + 12, -26, -7.0, brow_color, 5.2))

    # --- 4. MOUTH (optional mustache sits cleanly above mouth for Pak Bima) ---
    mouth_y = my + (6.5 if has_mustache else 0.0)
    if e == "chill":
        parts.append(
            f'<path d="M -11,{fmt(mouth_y)} Q 2,{fmt(mouth_y + 8)} 14,{fmt(mouth_y - 2)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linecap="round"/>'
        )
    elif e in ("aha", "laugh", "excited"):
        m_clip = svg.add_clip_path(
            f'<path d="M -18,{fmt(mouth_y - 4)} Q 0,{fmt(mouth_y - 7)} 18,{fmt(mouth_y - 4)} '
            f'Q 16,{fmt(mouth_y + 18)} 0,{fmt(mouth_y + 18)} Q -16,{fmt(mouth_y + 18)} -18,{fmt(mouth_y - 4)} Z"/>'
        )
        parts.append(
            f'<path d="M -18,{fmt(mouth_y - 4)} Q 0,{fmt(mouth_y - 7)} 18,{fmt(mouth_y - 4)} '
            f'Q 16,{fmt(mouth_y + 18)} 0,{fmt(mouth_y + 18)} Q -16,{fmt(mouth_y + 18)} -18,{fmt(mouth_y - 4)} Z" '
            f'fill="#6B1D29"/>'
            f'<g clip-path="{m_clip}">'
            f'<rect x="-18" y="{fmt(mouth_y - 8)}" width="36" height="9" rx="2" fill="#FFFFFF"/>'
            f'<ellipse cx="0" cy="{fmt(mouth_y + 16)}" rx="12" ry="7" fill="#EC6A74"/>'
            f"</g>"
            f'<path d="M -18,{fmt(mouth_y - 4)} Q 0,{fmt(mouth_y - 7)} 18,{fmt(mouth_y - 4)} '
            f'Q 16,{fmt(mouth_y + 18)} 0,{fmt(mouth_y + 18)} Q -16,{fmt(mouth_y + 18)} -18,{fmt(mouth_y - 4)} Z" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        )
    elif e in ("smug", "narcissistic", "determined"):
        parts.append(
            f'<path d="M -12,{fmt(mouth_y + 2)} Q 4,{fmt(mouth_y + 7)} 17,{fmt(mouth_y - 5)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linecap="round"/>'
            f'<path d="M 14,{fmt(mouth_y - 7)} Q 19,{fmt(mouth_y - 5)} 18,{fmt(mouth_y - 1)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="2.6" stroke-linecap="round"/>'
        )
    elif e in ("happy", "proud"):
        parts.append(
            f'<path d="M -15,{fmt(mouth_y - 2)} Q 0,{fmt(mouth_y + 14)} 15,{fmt(mouth_y - 2)} Z" '
            f'fill="#FFFFFF" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        )
    elif e == "relieved":
        parts.append(
            f'<path d="M -13,{fmt(mouth_y)} Q 0,{fmt(mouth_y + 10)} 13,{fmt(mouth_y)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="3.8" stroke-linecap="round"/>'
        )
    elif e == "thinking":
        parts.append(
            f'<path d="M -10,{fmt(mouth_y + 3)} Q -2,{fmt(mouth_y - 1)} 9,{fmt(mouth_y + 2)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="3.8" stroke-linecap="round"/>'
        )
    elif e == "deadpan":
        parts.append(
            f'<line x1="-13" y1="{fmt(mouth_y + 2)}" x2="13" y2="{fmt(mouth_y + 2)}" '
            f'stroke="{INK_COLOR}" stroke-width="4.0" stroke-linecap="round"/>'
        )
    elif e == "panic":
        # Wavy wide distressed mouth
        d = (
            f"M -17,{fmt(mouth_y + 6)} Q -14,{fmt(mouth_y - 8)} 0,{fmt(mouth_y - 7)} "
            f"Q 14,{fmt(mouth_y - 8)} 17,{fmt(mouth_y + 6)} Q 8,{fmt(mouth_y + 15)} 0,{fmt(mouth_y + 10)} "
            f"Q -8,{fmt(mouth_y + 15)} -17,{fmt(mouth_y + 6)} Z"
        )
        m_clip = svg.add_clip_path(f'<path d="{d}"/>')
        parts.append(
            f'<path d="{d}" fill="#6B1D29"/>'
            f'<g clip-path="{m_clip}">'
            f'<rect x="-18" y="{fmt(mouth_y - 9)}" width="36" height="7" fill="#FFFFFF"/>'
            f'<ellipse cx="0" cy="{fmt(mouth_y + 12)}" rx="10" ry="6" fill="#EC6A74"/>'
            f"</g>"
            f'<path d="{d}" fill="none" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        )
    elif e in ("stressed", "furious"):
        # Clenched grit teeth!
        d = (
            f"M -17,{fmt(mouth_y - 3)} Q 0,{fmt(mouth_y - 7)} 17,{fmt(mouth_y - 3)} "
            f"Q 19,{fmt(mouth_y + 9)} 14,{fmt(mouth_y + 10)} Q 0,{fmt(mouth_y + 8)} -14,{fmt(mouth_y + 10)} "
            f"Q -19,{fmt(mouth_y + 9)} -17,{fmt(mouth_y - 3)} Z"
        )
        parts.append(
            f'<path d="{d}" fill="#FFFFFF" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
            f'<line x1="-16" y1="{fmt(mouth_y + 3)}" x2="16" y2="{fmt(mouth_y + 3)}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
            f'<line x1="-7" y1="{fmt(mouth_y - 4)}" x2="-7" y2="{fmt(mouth_y + 9)}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
            f'<line x1="0" y1="{fmt(mouth_y - 5)}" x2="0" y2="{fmt(mouth_y + 9)}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
            f'<line x1="7" y1="{fmt(mouth_y - 4)}" x2="7" y2="{fmt(mouth_y + 9)}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
        )
    elif e == "shocked":
        parts.append(
            f'<ellipse cx="0" cy="{fmt(mouth_y + 5)}" rx="12.5" ry="15.0" fill="#6B1D29" '
            f'stroke="{INK_COLOR}" stroke-width="3.8"/>'
            f'<ellipse cx="0" cy="{fmt(mouth_y + 15)}" rx="7.5" ry="4.5" fill="#EC6A74"/>'
        )
    elif e == "stunned":
        parts.append(
            f'<ellipse cx="2" cy="{fmt(mouth_y + 3)}" rx="6.8" ry="8.0" fill="#6B1D29" '
            f'stroke="{INK_COLOR}" stroke-width="3.5"/>'
        )
    elif e in ("skeptical", "impatient"):
        parts.append(
            f'<path d="M -14,{fmt(mouth_y + 4)} Q -2,{fmt(mouth_y - 3)} 14,{fmt(mouth_y + 4)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="4.0" stroke-linecap="round"/>'
        )
    elif e == "confused":
        parts.append(
            f'<path d="M -13,{fmt(mouth_y + 4)} Q -4,{fmt(mouth_y - 2)} 3,{fmt(mouth_y + 5)} '
            f'Q 10,{fmt(mouth_y + 9)} 15,{fmt(mouth_y + 1)}" '
            f'fill="none" stroke="{INK_COLOR}" stroke-width="3.8" stroke-linecap="round"/>'
        )

    # Optional crisp Art Deco manager mustache (for Pak Bima)
    if has_mustache:
        m_grad = svg.add_linear_gradient(
            [(0.0, lighten(mustache_color, 0.24), 1.0), (1.0, darken(mustache_color, 0.25), 1.0)],
            x1=0.1,
            y1=0.0,
            x2=0.9,
            y2=1.0,
        )
        m_y = my - 3.5
        parts.append(
            f'<path d="M 0,{fmt(m_y - 7)} C -8,{fmt(m_y - 11)} -22,{fmt(m_y - 5)} -25,{fmt(m_y + 2)} '
            f'C -17,{fmt(m_y + 5)} -7,{fmt(m_y + 3)} 0,{fmt(m_y - 1)} '
            f'C 7,{fmt(m_y + 3)} 17,{fmt(m_y + 5)} 25,{fmt(m_y + 2)} '
            f'C 22,{fmt(m_y - 5)} 8,{fmt(m_y - 11)} 0,{fmt(m_y - 7)} Z" '
            f'fill="{m_grad}" stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        )

    # --- 5. SUPPORTING COMEDIC EMOTION FX ---
    if e == "panic":
        parts.append(_sweat_drop(svg, 46.0, -24.0, 0.85))
        parts.append(_sweat_drop(svg, -47.0, -8.0, 0.62))
    elif e == "stressed":
        parts.append(_sweat_drop(svg, 44.0, -18.0, 0.72))
        parts.append(_anger_vein(-42.0, -26.0, 0.85))
    elif e == "furious":
        parts.append(_anger_vein(42.0, -25.0, 0.95))
    elif e == "narcissistic":
        parts.append(_sparkle_star(49.0, -26.0, 12.5, "#FFD952"))
        parts.append(_sparkle_star(-47.0, 6.0, 8.5, "#FFF0A6"))
    elif e in ("aha", "proud"):
        parts.append(_sparkle_star(47.0, -29.0, 11.0, "#FFE066"))

    parts.append("</g>")
    return "".join(parts)
