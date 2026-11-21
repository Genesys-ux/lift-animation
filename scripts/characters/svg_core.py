"""Core SVG generation utilities: volumetric shading, clean gradients, and variable-width ink outlines."""

from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence, Tuple

Point = Tuple[float, float]

# Consistent studio key light from upper-left (normalized in SVG +Y-down coordinates)
_LX, _LY = -0.62, -0.78
_LMAG = math.hypot(_LX, _LY)
LIGHT_DIR: Point = (_LX / _LMAG, _LY / _LMAG)

INK_COLOR = "#16141B"
SOFT_INK = "#25212E"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def fmt(v: float) -> str:
    return f"{v:.2f}"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{clamp(int(round(r)), 0, 255):02X}{clamp(int(round(g)), 0, 255):02X}{clamp(int(round(b)), 0, 255):02X}"


def mix_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    t = clamp(t, 0.0, 1.0)
    return rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def darken(c: str, amount: float = 0.25) -> str:
    # Shift shadows slightly toward deep warm/cool ink instead of flat grey
    return mix_color(c, "#181424", amount)


def lighten(c: str, amount: float = 0.25) -> str:
    return mix_color(c, "#FFFDF5", amount)


def pts_to_path(pts: Sequence[Point], closed: bool = True) -> str:
    if not pts:
        return ""
    parts = [f"M {fmt(pts[0][0])},{fmt(pts[0][1])}"]
    for x, y in pts[1:]:
        parts.append(f"L {fmt(x)},{fmt(y)}")
    if closed:
        parts.append("Z")
    return " ".join(parts)


def sample_quad(p0: Point, p1: Point, p2: Point, steps: int = 24) -> List[Point]:
    out: List[Point] = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1.0 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        out.append((x, y))
    return out


def sample_cubic(p0: Point, p1: Point, p2: Point, p3: Point, steps: int = 28) -> List[Point]:
    out: List[Point] = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1.0 - t
        mt2 = mt * mt
        t2 = t * t
        x = mt2 * mt * p0[0] + 3 * mt2 * t * p1[0] + 3 * mt * t2 * p2[0] + t2 * t * p3[0]
        y = mt2 * mt * p0[1] + 3 * mt2 * t * p1[1] + 3 * mt * t2 * p2[1] + t2 * t * p3[1]
        out.append((x, y))
    return out


def sample_ellipse(cx: float, cy: float, rx: float, ry: float, steps: int = 72) -> List[Point]:
    # Clockwise in SVG (+Y down): angle 0 is right, +angle goes downward (clockwise)
    pts: List[Point] = []
    for i in range(steps):
        a = (2.0 * math.pi * i) / steps
        pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    return pts


def sample_rounded_capsule(
    cx: float,
    top_y: float,
    w_top: float,
    w_mid: float,
    w_bot: float,
    height: float,
    dome_ratio: float = 0.28,
    bot_ratio: float = 0.22,
    steps_per_arc: int = 28,
) -> List[Point]:
    """Sample a smooth, organically tapered pill/capsule silhouette clockwise in SVG coords.

    Allows distinct character body shapes (tall sleek bean, broad-chested capsule, stocky pill)
    while staying unmistakably in the 2.5D stylized pill/capsule family.
    """
    bot_y = top_y + height
    ry_top = height * dome_ratio
    ry_bot = height * bot_ratio
    rx_top = w_top * 0.5
    rx_mid = w_mid * 0.5
    rx_bot = w_bot * 0.5

    y_upper = top_y + ry_top
    y_lower = bot_y - ry_bot
    y_mid = (y_upper + y_lower) * 0.5

    pts: List[Point] = []

    # Top dome: left (-pi) to right (0) clockwise
    for i in range(steps_per_arc):
        a = math.pi + (math.pi * i) / steps_per_arc
        pts.append((cx + math.cos(a) * rx_top, y_upper + math.sin(a) * ry_top))

    # Right torso flank: smooth cubic curve through mid width
    right_side = sample_cubic(
        (cx + rx_top, y_upper),
        (cx + rx_mid, y_upper + (y_mid - y_upper) * 0.65),
        (cx + rx_mid, y_lower - (y_lower - y_mid) * 0.55),
        (cx + rx_bot, y_lower),
        steps=22,
    )
    pts.extend(right_side[:-1])

    # Bottom dome: right (0) to left (+pi) clockwise
    for i in range(steps_per_arc):
        a = (math.pi * i) / steps_per_arc
        pts.append((cx + math.cos(a) * rx_bot, y_lower + math.sin(a) * ry_bot))

    # Left torso flank: smooth cubic curve back to upper left
    left_side = sample_cubic(
        (cx - rx_bot, y_lower),
        (cx - rx_mid, y_lower - (y_lower - y_mid) * 0.55),
        (cx - rx_mid, y_upper + (y_mid - y_upper) * 0.65),
        (cx - rx_top, y_upper),
        steps=22,
    )
    pts.extend(left_side[:-1])

    return pts


def _signed_area(pts: Sequence[Point]) -> float:
    n = len(pts)
    area = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return 0.5 * area


def _dedupe_points(pts: Sequence[Point], eps: float = 0.25) -> List[Point]:
    out: List[Point] = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def variable_ink_closed(
    pts: Sequence[Point],
    min_w: float = 3.0,
    max_w: float = 7.4,
    color: str = INK_COLOR,
    light_dir: Point = LIGHT_DIR,
) -> str:
    """Create a filled SVG path representing a variable-width organic ink outline around a closed contour.

    Sunlit upper-left edges stay crisp & thin; shadowed bottom-right edges become bold & grounded.
    """
    clean = _dedupe_points(pts)
    n = len(clean)
    if n < 4:
        return ""

    # Ensure clockwise orientation in SVG (+Y down) so (dy, -dx) is outward normal
    if _signed_area(clean) < 0:
        clean = list(reversed(clean))

    outer: List[Point] = []
    inner: List[Point] = []
    lx, ly = light_dir

    for i in range(n):
        prev_p = clean[(i - 1) % n]
        curr_p = clean[i]
        next_p = clean[(i + 1) % n]
        dx = next_p[0] - prev_p[0]
        dy = next_p[1] - prev_p[1]
        mag = math.hypot(dx, dy)
        if mag < 1e-6:
            nx, ny = 0.0, -1.0
        else:
            # Outward normal for clockwise polygon in +Y down coordinates
            nx, ny = dy / mag, -dx / mag

        lit = nx * lx + ny * ly  # +1 facing light, -1 facing shadow
        shadow_f = clamp((1.0 - lit) * 0.5, 0.0, 1.0)
        w = min_w + (max_w - min_w) * (shadow_f ** 1.35)

        outer.append((curr_p[0] + nx * (w * 0.58), curr_p[1] + ny * (w * 0.58)))
        inner.append((curr_p[0] - nx * (w * 0.42), curr_p[1] - ny * (w * 0.42)))

    d = f"{pts_to_path(outer, closed=True)} {pts_to_path(list(reversed(inner)), closed=True)}"
    return f'<path d="{d}" fill="{color}" fill-rule="evenodd"/>'


def variable_ink_open(
    pts: Sequence[Point],
    min_w: float = 2.4,
    max_w: float = 6.0,
    taper_start: float = 0.35,
    taper_end: float = 0.35,
    color: str = INK_COLOR,
    light_dir: Point = LIGHT_DIR,
) -> str:
    """Create a tapered variable-width calligraphic ink stroke along an open polyline."""
    clean = _dedupe_points(pts)
    n = len(clean)
    if n < 2:
        return ""

    left_side: List[Point] = []
    right_side: List[Point] = []
    lx, ly = light_dir

    for i in range(n):
        if i == 0:
            dx = clean[1][0] - clean[0][0]
            dy = clean[1][1] - clean[0][1]
        elif i == n - 1:
            dx = clean[-1][0] - clean[-2][0]
            dy = clean[-1][1] - clean[-2][1]
        else:
            dx = clean[i + 1][0] - clean[i - 1][0]
            dy = clean[i + 1][1] - clean[i - 1][1]
        mag = math.hypot(dx, dy) or 1.0
        nx, ny = dy / mag, -dx / mag

        t = i / (n - 1)
        # Smooth end tapering
        env = 1.0
        if taper_start > 0 and t < 0.25:
            u = t / 0.25
            env *= taper_start + (1.0 - taper_start) * math.sin(u * math.pi * 0.5)
        if taper_end > 0 and t > 0.75:
            u = (1.0 - t) / 0.25
            env *= taper_end + (1.0 - taper_end) * math.sin(u * math.pi * 0.5)

        lit = nx * lx + ny * ly
        shadow_f = clamp((1.0 - lit) * 0.5, 0.0, 1.0)
        half_w = 0.5 * (min_w + (max_w - min_w) * (shadow_f ** 1.2)) * env

        cx, cy = clean[i]
        left_side.append((cx + nx * half_w, cy + ny * half_w))
        right_side.append((cx - nx * half_w, cy - ny * half_w))

    poly = left_side + list(reversed(right_side))
    return f'<path d="{pts_to_path(poly, closed=True)}" fill="{color}"/>'


class SvgBuilder:
    """Clean, composable SVG document builder with automatic unique IDs for gradients and clip paths."""

    def __init__(self, width: float, height: float, viewbox: Optional[str] = None, prefix: str = "id"):
        self.width = width
        self.height = height
        self.viewbox = viewbox or f"0 0 {fmt(width)} {fmt(height)}"
        self.prefix = prefix
        self._counter = 0
        self.defs: List[str] = []
        self.elements: List[str] = []

    def next_id(self, tag: str = "el") -> str:
        self._counter += 1
        return f"{self.prefix}_{tag}_{self._counter}"

    def add_def(self, markup: str) -> None:
        self.defs.append(markup)

    def add(self, markup: str) -> None:
        if markup:
            self.elements.append(markup)

    def add_linear_gradient(
        self,
        stops: Sequence[Tuple[float, str, float]],
        x1: float = 0.0,
        y1: float = 0.0,
        x2: float = 1.0,
        y2: float = 0.0,
        units: str = "objectBoundingBox",
    ) -> str:
        gid = self.next_id("lg")
        stop_lines = [
            f'<stop offset="{o * 100:.1f}%" stop-color="{col}" stop-opacity="{op:.3f}"/>'
            for o, col, op in stops
        ]
        self.add_def(
            f'<linearGradient id="{gid}" x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
            f'gradientUnits="{units}">{"".join(stop_lines)}</linearGradient>'
        )
        return f"url(#{gid})"

    def add_radial_gradient(
        self,
        stops: Sequence[Tuple[float, str, float]],
        cx: float = 0.35,
        cy: float = 0.30,
        r: float = 0.72,
        fx: Optional[float] = None,
        fy: Optional[float] = None,
        units: str = "objectBoundingBox",
    ) -> str:
        gid = self.next_id("rg")
        fx_s = f' fx="{fx:.3f}"' if fx is not None else ""
        fy_s = f' fy="{fy:.3f}"' if fy is not None else ""
        stop_lines = [
            f'<stop offset="{o * 100:.1f}%" stop-color="{col}" stop-opacity="{op:.3f}"/>'
            for o, col, op in stops
        ]
        self.add_def(
            f'<radialGradient id="{gid}" cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}"{fx_s}{fy_s} '
            f'gradientUnits="{units}">{"".join(stop_lines)}</radialGradient>'
        )
        return f"url(#{gid})"

    def add_clip_path(self, inner_svg: str) -> str:
        cid = self.next_id("clip")
        self.add_def(f'<clipPath id="{cid}">{inner_svg}</clipPath>')
        return f"url(#{cid})"

    def add_cylindrical_gradient(
        self,
        base_color: str,
        lit_shift: float = 0.24,
        shadow_shift: float = 0.34,
        bounce_color: Optional[str] = None,
        bounce_strength: float = 0.22,
    ) -> str:
        """3D cylindrical cel-PBR shading: bright upper-left key, crisp base, deep core shadow, warm rim bounce."""
        c_hi = lighten(base_color, lit_shift)
        c_mid = base_color
        c_core = darken(base_color, shadow_shift)
        c_bounce = mix_color(c_core, bounce_color or "#FFCF86", bounce_strength)
        return self.add_linear_gradient(
            [
                (0.00, c_hi, 1.0),
                (0.24, c_mid, 1.0),
                (0.62, c_mid, 1.0),
                (0.84, c_core, 1.0),
                (1.00, c_bounce, 1.0),
            ],
            x1=0.05,
            y1=0.08,
            x2=0.98,
            y2=0.52,
        )

    def render(self, background: Optional[str] = None) -> str:
        bg_el = (
            f'<rect x="0" y="0" width="{fmt(self.width)}" height="{fmt(self.height)}" fill="{background}"/>'
            if background
            else ""
        )
        defs_block = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        body = "".join(self.elements)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(self.width)}" height="{fmt(self.height)}" '
            f'viewBox="{self.viewbox}" shape-rendering="geometricPrecision">'
            f"{defs_block}{bg_el}{body}</svg>"
        )
