"""Detailed 3D-volumetric handheld props tailored to 'The Slow Elevator & Mirror' story."""

from __future__ import annotations

from .svg_core import INK_COLOR, Point, SvgBuilder, darken, fmt, lighten


def draw_coffee_cup(svg: SvgBuilder, pos: Point, angle_deg: float = -6.0, scale: float = 1.0) -> str:
    """Raka's cylindrical paper coffee cup with corrugated kraft sleeve, domed lid & warm steam."""
    cup_g = svg.add_cylindrical_gradient("#FAF3E3", lit_shift=0.18, shadow_shift=0.22, bounce_color="#F5D399")
    sleeve_g = svg.add_cylindrical_gradient("#C9894F", lit_shift=0.22, shadow_shift=0.34, bounce_color="#F2B872")
    lid_g = svg.add_linear_gradient(
        [(0.0, "#FFFFFF", 1.0), (0.5, "#ECE6DC", 1.0), (1.0, "#C7BEB2", 1.0)],
        x1=0.1,
        y1=0.0,
        x2=0.9,
        y2=1.0,
    )
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        # Subtle warm steam curls
        f'<path d="M -5,-44 Q -10,-55 -4,-64 Q 1,-71 -3,-78" fill="none" stroke="#FFFDF5" '
        f'stroke-width="3.2" stroke-linecap="round" opacity="0.65"/>'
        f'<path d="M 7,-46 Q 12,-56 6,-66" fill="none" stroke="#FFFDF5" '
        f'stroke-width="2.6" stroke-linecap="round" opacity="0.52"/>'
        # Tapered cup body
        f'<path d="M -17,-25 L 17,-25 L 12,26 Q 0,30 -12,26 Z" fill="{cup_g}" '
        f'stroke="{INK_COLOR}" stroke-width="3.4" stroke-linejoin="round"/>'
        # Corrugated kraft sleeve wrapping along curved cylinder
        f'<path d="M -16,-11 Q 0,-7 16,-11 L 14,13 Q 0,17 -14,13 Z" fill="{sleeve_g}" '
        f'stroke="{INK_COLOR}" stroke-width="2.8" stroke-linejoin="round"/>'
        # Cast shadow under sleeve
        f'<path d="M -13.5,14 Q 0,18.5 13.5,14 L 13,18 Q 0,22 -13,18 Z" fill="#8A6C52" opacity="0.30"/>'
        # Coffee emblem circle on sleeve
        f'<circle cx="0" cy="2" r="6.5" fill="#F6E9D2" stroke="{INK_COLOR}" stroke-width="2.0"/>'
        f'<ellipse cx="0" cy="2" rx="3.2" ry="4.5" transform="rotate(-18 0 2)" fill="#63381E"/>'
        f'<path d="M -1,-1.5 Q 1,2 -0.5,5.5" fill="none" stroke="#F6E9D2" stroke-width="1.3"/>'
        # Cast shadow under lid rim
        f'<path d="M -17,-25 Q 0,-21 17,-25 L 16.5,-20 Q 0,-16 -16.5,-20 Z" fill="#473A30" opacity="0.28"/>'
        # Domed plastic lid
        f'<path d="M -21,-26 Q 0,-22 21,-26 L 18,-35 Q 0,-39 -18,-35 Z" fill="{lid_g}" '
        f'stroke="{INK_COLOR}" stroke-width="3.2" stroke-linejoin="round"/>'
        f'<ellipse cx="0" cy="-35" rx="16.5" ry="4.2" fill="{lid_g}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        # Specular highlight on lid & cup left flank
        f'<path d="M -12,-33 Q -4,-35 3,-33" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" opacity="0.85"/>'
        f'<line x1="-10" y1="-8" x2="-8.5" y2="10" stroke="#FFE6C2" stroke-width="2.8" stroke-linecap="round" opacity="0.45"/>'
        f"</g>"
    )


def draw_gold_hand_mirror(svg: SvgBuilder, pos: Point, angle_deg: float = 12.0, scale: float = 1.0) -> str:
    """Raka's Art Deco beveled brass hand mirror — central story icon."""
    gold_lit = svg.add_linear_gradient(
        [(0.0, "#FFF1A8", 1.0), (0.35, "#E8B73E", 1.0), (0.75, "#B8811C", 1.0), (1.0, "#E0AE3B", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=1.0,
        y2=1.0,
    )
    gold_bevel = svg.add_linear_gradient(
        [(0.0, "#9E6A14", 1.0), (0.5, "#D9A42E", 1.0), (1.0, "#FFF0A8", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=1.0,
        y2=1.0,
    )
    glass_g = svg.add_linear_gradient(
        [(0.0, "#E8FAFF", 1.0), (0.45, "#A8DCF0", 1.0), (1.0, "#6BAAC9", 1.0)],
        x1=0.1,
        y1=0.0,
        x2=0.9,
        y2=1.0,
    )
    handle_g = svg.add_cylindrical_gradient("#C99224", lit_shift=0.35, shadow_shift=0.38)
    clip = svg.add_clip_path('<ellipse cx="0" cy="-34" rx="22" ry="27"/>')
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        # Turned Art Deco handle
        f'<path d="M -6,-5 L 6,-5 L 8,28 Q 0,34 -8,28 Z" fill="{handle_g}" '
        f'stroke="{INK_COLOR}" stroke-width="3.4" stroke-linejoin="round"/>'
        f'<ellipse cx="0" cy="29" rx="7.5" ry="4.5" fill="{gold_lit}" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        f'<rect x="-9" y="-6" width="18" height="6" rx="3" fill="{gold_lit}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        # Outer faceted gold frame
        f'<ellipse cx="0" cy="-34" rx="29" ry="35" fill="{gold_lit}" stroke="{INK_COLOR}" stroke-width="4.0"/>'
        # Art Deco crown crest on top of frame
        f'<path d="M -11,-66 L 0,-77 L 11,-66 Z" fill="{gold_lit}" stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
        # Recessed inner bevel ring
        f'<ellipse cx="0" cy="-34" rx="24.5" ry="30" fill="{gold_bevel}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
        # Reflective mirror glass with diagonal shimmer bands
        f'<ellipse cx="0" cy="-34" rx="22" ry="27" fill="{glass_g}"/>'
        f'<g clip-path="{clip}">'
        f'<polygon points="-28,-46 14,-68 24,-58 -24,-30" fill="#FFFFFF" opacity="0.65"/>'
        f'<polygon points="-24,-22 24,-48 28,-42 -20,-14" fill="#FFFFFF" opacity="0.38"/>'
        f'<polygon points="-10,-2 26,-24 30,-16 -6,6" fill="#FFFFFF" opacity="0.28"/>'
        f"</g>"
        f'<ellipse cx="0" cy="-34" rx="22" ry="27" fill="none" stroke="{INK_COLOR}" stroke-width="2.5"/>'
        # Crisp pinpoint specular glint on top-left frame
        f'<circle cx="-16" cy="-54" r="3.2" fill="#FFFFFF"/>'
        f"</g>"
    )


def draw_complaint_clipboard(svg: SvgBuilder, pos: Point, angle_deg: float = -10.0, scale: float = 1.0) -> str:
    """Pak Bima's wooden clipboard covered with a skyrocketing red complaint chart & brass clip."""
    board_g = svg.add_linear_gradient(
        [(0.0, "#B07346", 1.0), (0.6, "#854F28", 1.0), (1.0, "#5C3316", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=1.0,
        y2=1.0,
    )
    clip_g = svg.add_linear_gradient(
        [(0.0, "#FFF2B2", 1.0), (0.5, "#DFAA34", 1.0), (1.0, "#9E6E14", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=0.0,
        y2=1.0,
    )
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        # Clipboard wood backing with 3D right/bottom edge bevel
        f'<rect x="-32" y="-42" width="68" height="88" rx="8" fill="#47250F" stroke="{INK_COLOR}" stroke-width="3.6"/>'
        f'<rect x="-35" y="-45" width="68" height="88" rx="8" fill="{board_g}" stroke="{INK_COLOR}" stroke-width="3.6"/>'
        # Slightly askew bottom paper sheet
        f'<rect x="-26" y="-33" width="54" height="68" rx="2" transform="rotate(3 0 0)" '
        f'fill="#EDE5D5" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        # Top paper sheet with curled corner
        f'<path d="M -28,-35 L 26,-35 L 26,23 L 16,33 L -28,33 Z" fill="#FFFDF7" '
        f'stroke="{INK_COLOR}" stroke-width="2.4" stroke-linejoin="round"/>'
        f'<path d="M 16,33 L 16,23 L 26,23 Z" fill="#D9D0C1" stroke="{INK_COLOR}" stroke-width="2.0" stroke-linejoin="round"/>'
        # Red header bar ("99%!")
        f'<rect x="-22" y="-26" width="42" height="9" rx="2" fill="#D93829"/>'
        f'<line x1="-18" y1="-21.5" x2="10" y2="-21.5" stroke="#FFFDF7" stroke-width="2.8" stroke-linecap="round"/>'
        # Mini grid lines
        f'<line x1="-21" y1="18" x2="19" y2="18" stroke="#9AA3B2" stroke-width="2.0"/>'
        f'<line x1="-21" y1="-10" x2="-21" y2="18" stroke="#9AA3B2" stroke-width="2.0"/>'
        f'<line x1="-21" y1="8" x2="18" y2="8" stroke="#DCE1EA" stroke-width="1.4"/>'
        f'<line x1="-21" y1="-2" x2="18" y2="-2" stroke="#DCE1EA" stroke-width="1.4"/>'
        # Skyrocketing red complaint spike!
        f'<polyline points="-19,14 -8,11 1,1 9,4 18,-12" fill="none" stroke="#E02D24" '
        f'stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<polygon points="18,-16 12,-9 21,-7" fill="#E02D24"/>'
        # Yellow panic sticky note sticking off side
        f'<rect x="14" y="-6" width="22" height="20" rx="2" transform="rotate(10 25 4)" '
        f'fill="#FFE15C" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        f'<text x="24" y="9" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="13" font-weight="900" fill="#D92626" transform="rotate(10 25 4)">!</text>'
        # Cast shadow under brass clip
        f'<rect x="-15" y="-36" width="30" height="8" rx="2" fill="#3B2B1E" opacity="0.25"/>'
        # Faceted brass spring clip
        f'<rect x="-15" y="-49" width="30" height="14" rx="4" fill="{clip_g}" stroke="{INK_COLOR}" stroke-width="3.0"/>'
        f'<circle cx="0" cy="-47" r="5" fill="{clip_g}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        f'<line x1="-10" y1="-44" x2="8" y2="-44" stroke="#FFFFFF" stroke-width="2.0" stroke-linecap="round" opacity="0.75"/>'
        f"</g>"
    )


def draw_red_pen(svg: SvgBuilder, pos: Point, angle_deg: float = 35.0, scale: float = 1.0) -> str:
    """Pak Bima's glossy fountain pen."""
    pen_g = svg.add_linear_gradient(
        [(0.0, "#FF6E5E", 1.0), (0.5, "#D93225", 1.0), (1.0, "#851812", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=0.0,
        y2=1.0,
    )
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        f'<rect x="-24" y="-4.5" width="40" height="9" rx="3" fill="{pen_g}" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        f'<polygon points="16,-4.5 29,0 16,4.5" fill="#E8B948" stroke="{INK_COLOR}" stroke-width="2.4" stroke-linejoin="round"/>'
        f'<rect x="-18" y="-6.5" width="16" height="3" rx="1.5" fill="#F2C85B" stroke="{INK_COLOR}" stroke-width="1.6"/>'
        f'<line x1="-20" y1="-1.5" x2="11" y2="-1.5" stroke="#FFFFFF" stroke-width="1.8" opacity="0.55" stroke-linecap="round"/>'
        f"</g>"
    )


def draw_leather_briefcase(svg: SvgBuilder, pos: Point, angle_deg: float = 4.0, scale: float = 1.0) -> str:
    """Pak Doni's 3D-perspective vintage saddle-leather briefcase with stitched trim & brass latches."""
    front_g = svg.add_linear_gradient(
        [(0.0, "#AD6234", 1.0), (0.5, "#87441E", 1.0), (1.0, "#592A10", 1.0)],
        x1=0.05,
        y1=0.0,
        x2=0.95,
        y2=1.0,
    )
    top_g = svg.add_linear_gradient(
        [(0.0, "#C97D49", 1.0), (1.0, "#995328", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=1.0,
        y2=1.0,
    )
    side_g = darken("#7A3C19", 0.35)
    brass_g = svg.add_linear_gradient(
        [(0.0, "#FFF0A6", 1.0), (0.5, "#E0AC34", 1.0), (1.0, "#946414", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=1.0,
        y2=1.0,
    )
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        # Curved leather handle at top (hand grips right around y=0)
        f'<path d="M -16,12 L -16,1 Q -16,-7 -7,-7 L 7,-7 Q 16,-7 16,1 L 16,12" '
        f'fill="none" stroke="{INK_COLOR}" stroke-width="11.0" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M -16,12 L -16,1 Q -16,-7 -7,-7 L 7,-7 Q 16,-7 16,1 L 16,12" '
        f'fill="none" stroke="#9C5328" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/>'
        # 3D right side depth panel
        f'<path d="M 38,13 L 49,19 L 49,69 Q 49,75 43,77 L 36,79 Z" fill="{side_g}" '
        f'stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        # 3D top bevel ledge
        f'<path d="M -42,14 L -32,9 L 38,9 L 49,19 L 38,21 L -42,21 Z" fill="{top_g}" '
        f'stroke="{INK_COLOR}" stroke-width="3.4" stroke-linejoin="round"/>'
        # Main front face
        f'<rect x="-44" y="14" width="84" height="64" rx="8" fill="{front_g}" '
        f'stroke="{INK_COLOR}" stroke-width="4.0"/>'
        # Upper flap & cast shadow beneath flap
        f'<path d="M -43,39 L 39,39 L 39,45 L -43,45 Z" fill="#2A1206" opacity="0.34"/>'
        f'<path d="M -44,21 Q -44,14 -36,14 L 32,14 Q 40,14 40,21 L 40,36 Q 40,40 34,40 L -38,40 Q -44,40 -44,36 Z" '
        f'fill="{top_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>'
        # Decorative leather stitching
        f'<rect x="-37" y="45" width="70" height="26" rx="4" fill="none" stroke="#D99B66" '
        f'stroke-width="1.8" stroke-dasharray="4 4" opacity="0.65"/>'
        # Leather corner reinforcements
        f'<path d="M -44,66 L -32,78 L -38,78 Q -44,78 -44,72 Z" fill="#59280F" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        f'<path d="M 40,66 L 28,78 L 34,78 Q 40,78 40,72 Z" fill="#59280F" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        # Dual faceted brass latches
        f'<rect x="-25" y="33" width="11" height="14" rx="2.5" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<rect x="10" y="33" width="11" height="14" rx="2.5" fill="{brass_g}" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<circle cx="-21" cy="37" r="1.8" fill="#FFFFFF"/>'
        f'<circle cx="14" cy="37" r="1.8" fill="#FFFFFF"/>'
        # Specular sheen across upper flap
        f'<line x1="-34" y1="20" x2="20" y2="20" stroke="#FFE5C2" stroke-width="3.0" stroke-linecap="round" opacity="0.5"/>'
        f"</g>"
    )


def draw_gold_wristwatch(svg: SvgBuilder, pos: Point, angle_deg: float = -20.0, scale: float = 1.0) -> str:
    """Pak Doni's oversized gleaming gold wristwatch he furiously checks while waiting."""
    gold_g = svg.add_linear_gradient(
        [(0.0, "#FFF4B8", 1.0), (0.45, "#E8B738", 1.0), (1.0, "#9E6E14", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=1.0,
        y2=1.0,
    )
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        # Watch strap wrapping wrist
        f'<rect x="-13" y="-7" width="26" height="14" rx="4" fill="#633519" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        # Beveled brass casing
        f'<circle cx="0" cy="0" r="11.5" fill="{gold_g}" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        # Crown knob
        f'<rect x="10" y="-2.5" width="4.5" height="5" rx="1.5" fill="{gold_g}" stroke="{INK_COLOR}" stroke-width="2.0"/>'
        # Crisp white watch dial + red ticking second hand
        f'<circle cx="0" cy="0" r="8.0" fill="#FFFDF5" stroke="{INK_COLOR}" stroke-width="1.8"/>'
        f'<line x1="0" y1="0" x2="0" y2="-5.5" stroke="{INK_COLOR}" stroke-width="2.0" stroke-linecap="round"/>'
        f'<line x1="0" y1="0" x2="4.5" y2="1.5" stroke="#D92B2B" stroke-width="1.8" stroke-linecap="round"/>'
        f'<circle cx="0" cy="0" r="1.4" fill="{INK_COLOR}"/>'
        # Glass glint
        f'<path d="M -5,-4 L -1,-6" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" opacity="0.85"/>'
        f"</g>"
    )


def draw_pocket_comb(svg: SvgBuilder, pos: Point, angle_deg: float = -30.0, scale: float = 1.0) -> str:
    """Pak Doni's tortoiseshell pocket comb for grooming his pompadour in the mirror."""
    comb_g = svg.add_linear_gradient(
        [(0.0, "#E0913E", 1.0), (0.5, "#9E4C1B", 1.0), (1.0, "#5C260B", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=1.0,
        y2=1.0,
    )
    x, y = pos
    teeth = []
    for i in range(-22, 24, 5):
        teeth.append(
            f'<rect x="{i}" y="1" width="2.8" height="12" rx="1" fill="{comb_g}" stroke="{INK_COLOR}" stroke-width="1.2"/>'
        )
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        f"{''.join(teeth)}"
        f'<rect x="-26" y="-7" width="52" height="10" rx="4.5" fill="{comb_g}" stroke="{INK_COLOR}" stroke-width="2.8"/>'
        f'<line x1="-20" y1="-3.5" x2="18" y2="-3.5" stroke="#FFE0A6" stroke-width="2.0" stroke-linecap="round" opacity="0.65"/>'
        f"</g>"
    )


def draw_rocket_blueprint(svg: SvgBuilder, pos: Point, angle_deg: float = -18.0, scale: float = 1.0) -> str:
    """Clara's rolled cyan architectural blueprint 'TURBO LIFT' with uncurling schematic edge."""
    roll_g = svg.add_cylindrical_gradient("#2378C4", lit_shift=0.28, shadow_shift=0.35, bounce_color="#7AC8FA")
    inner_g = svg.add_linear_gradient([(0.0, "#D8EEFF", 1.0), (1.0, "#85BCEB", 1.0)], 0, 0, 1, 1)
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        # Uncurling schematic corner flap peeking out
        f'<path d="M 10,-28 L 36,-34 Q 44,-14 34,12 L 10,8 Z" fill="#1E6DB5" '
        f'stroke="{INK_COLOR}" stroke-width="3.0" stroke-linejoin="round"/>'
        # White technical schematic lines (mini rocket + pulley!)
        f'<line x1="16" y1="-22" x2="32" y2="-25" stroke="#FFFFFF" stroke-width="1.5" opacity="0.7"/>'
        f'<line x1="16" y1="-13" x2="33" y2="-16" stroke="#FFFFFF" stroke-width="1.5" opacity="0.7"/>'
        f'<path d="M 24,-10 L 28,-2 L 20,-2 Z" fill="none" stroke="#FFFFFF" stroke-width="1.8"/>'
        f'<circle cx="24" cy="4" r="3.5" fill="none" stroke="#FFFFFF" stroke-width="1.5"/>'
        # Main rolled blueprint cylinder
        f'<path d="M -14,-44 L 14,-44 L 14,34 Q 0,41 -14,34 Z" fill="{roll_g}" '
        f'stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        # Top spiral opening
        f'<ellipse cx="0" cy="-44" rx="14" ry="6.5" fill="{inner_g}" stroke="{INK_COLOR}" stroke-width="3.2"/>'
        f'<path d="M -7,-44 Q 0,-47 6,-44 Q 4,-41 -3,-42" fill="none" stroke="#1F5F99" stroke-width="2.2" stroke-linecap="round"/>'
        # White blueprint grid lines wrapping cylinder
        f'<path d="M -13,-18 Q 0,-13 13,-18" fill="none" stroke="#BFE3FF" stroke-width="1.6" opacity="0.65"/>'
        f'<path d="M -13,18 Q 0,23 13,18" fill="none" stroke="#BFE3FF" stroke-width="1.6" opacity="0.65"/>'
        # Red rubber band holding roll + cast shadow
        f'<path d="M -15,2 Q 0,8 15,2 L 15,8 Q 0,14 -15,8 Z" fill="#12304F" opacity="0.3"/>'
        f'<path d="M -15,-3 Q 0,3 15,-3 L 15,4 Q 0,10 -15,4 Z" fill="#E33E33" stroke="{INK_COLOR}" stroke-width="2.6"/>'
        # Specular band along cylinder
        f'<line x1="-6" y1="-34" x2="-6" y2="28" stroke="#FFFFFF" stroke-width="3.2" stroke-linecap="round" opacity="0.38"/>'
        f"</g>"
    )


def draw_steel_wrench(svg: SvgBuilder, pos: Point, angle_deg: float = 28.0, scale: float = 1.0) -> str:
    """Clara's beveled brushed-steel mechanical wrench."""
    steel_lit = svg.add_linear_gradient(
        [(0.0, "#F2F7FC", 1.0), (0.45, "#B6C4D4", 1.0), (1.0, "#6E7E91", 1.0)],
        x1=0.0,
        y1=0.0,
        x2=1.0,
        y2=1.0,
    )
    x, y = pos
    return (
        f'<g transform="translate({fmt(x)},{fmt(y)}) rotate({fmt(angle_deg)}) scale({fmt(scale)})">'
        # Open-end wrench silhouette (C-jaw at top, shaft, closed ring end at bottom)
        f'<path d="M -15,-48 C -22,-36 -18,-22 -8,-17 L -7,28 C -14,32 -14,44 -5,48 '
        f'C 4,51 14,44 12,34 C 11,31 9,29 7,28 L 8,-17 C 18,-22 22,-36 15,-48 '
        f'L 7,-33 L -7,-33 Z" fill="{steel_lit}" stroke="{INK_COLOR}" stroke-width="3.6" stroke-linejoin="round"/>'
        # Recessed bevel groove down shaft
        f'<rect x="-3" y="-12" width="6" height="34" rx="3" fill="#7D8DA1" stroke="#536173" stroke-width="1.4"/>'
        # Ring hole at bottom
        f'<circle cx="0" cy="38" r="5.5" fill="#FFFFFF" opacity="0.0" stroke="{INK_COLOR}" stroke-width="2.4"/>'
        f'<circle cx="0" cy="38" r="5.2" fill="#2A323D" stroke="{INK_COLOR}" stroke-width="2.2"/>'
        # Crisp metallic specular edge on left jaw
        f'<path d="M -13,-42 Q -15,-32 -10,-23" fill="none" stroke="#FFFFFF" stroke-width="2.8" stroke-linecap="round" opacity="0.82"/>'
        f'<line x1="-5" y1="-10" x2="-5" y2="20" stroke="#FFFFFF" stroke-width="2.0" stroke-linecap="round" opacity="0.65"/>'
        f"</g>"
    )
