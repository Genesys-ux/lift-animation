"""Bezier camera choreography, 2.5D squash-and-stretch acting, sprite swapping & 3D prop animation helpers."""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import bpy
from mathutils import Euler, Vector

from .characters_3d import spawn_character_card
from .compat import get_or_create_collection, link_obj_exclusive
from .props_3d import attach_3d_art_deco_props


def _set_curve_interp(
    id_block,
    data_path: str,
    frame: float,
    interp: str = "BEZIER",
    easing: str = "AUTO",
    handle_type: str = "AUTO_CLAMPED",
) -> None:
    ad = getattr(id_block, "animation_data", None)
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path == data_path:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.01:
                    kp.interpolation = interp
                    if interp == "BEZIER":
                        kp.easing = easing
                        kp.handle_left_type = handle_type
                        kp.handle_right_type = handle_type


def key_loc(obj: bpy.types.Object, loc: Tuple[float, float, float], frame: float, interp: str = "BEZIER") -> None:
    obj.location = Vector(loc)
    obj.keyframe_insert(data_path="location", frame=frame)
    _set_curve_interp(obj, "location", frame, interp=interp)


def key_rot(obj: bpy.types.Object, rot_deg: Tuple[float, float, float], frame: float, interp: str = "BEZIER") -> None:
    obj.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
    obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    _set_curve_interp(obj, "rotation_euler", frame, interp=interp)


def key_scale(obj: bpy.types.Object, scale: Tuple[float, float, float], frame: float, interp: str = "BEZIER") -> None:
    obj.scale = Vector(scale)
    obj.keyframe_insert(data_path="scale", frame=frame)
    _set_curve_interp(obj, "scale", frame, interp=interp)


def key_visible(obj: bpy.types.Object, visible: bool, frame: float) -> None:
    obj.hide_render = not visible
    obj.hide_viewport = not visible
    obj.keyframe_insert(data_path="hide_render", frame=frame)
    obj.keyframe_insert(data_path="hide_viewport", frame=frame)
    _set_curve_interp(obj, "hide_render", frame, interp="CONSTANT")
    _set_curve_interp(obj, "hide_viewport", frame, interp="CONSTANT")


class CinemaCameraRig:
    """Target-tracked 9:16 cinema camera supporting crisp Bezier push-ins, whip-pans, orbits & parallax."""

    def __init__(self, name: str = "HeroCam"):
        cam_col = get_or_create_collection("Cameras")
        self.target = bpy.data.objects.new(f"{name}_Target", None)
        link_obj_exclusive(self.target, cam_col)

        cam_data = bpy.data.cameras.new(f"{name}_Data")
        cam_data.sensor_fit = "VERTICAL"
        cam_data.sensor_height = 36.0
        cam_data.clip_start = 0.08
        cam_data.clip_end = 120.0
        self.cam = bpy.data.objects.new(name, cam_data)
        link_obj_exclusive(self.cam, cam_col)

        track = self.cam.constraints.new(type="TRACK_TO")
        track.target = self.target
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

        bpy.context.scene.camera = self.cam

    def key_shot(
        self,
        frame: float,
        cam_loc: Tuple[float, float, float],
        target_loc: Tuple[float, float, float],
        lens_mm: float = 28.0,
        dof_fstop: Optional[float] = None,
    ) -> None:
        key_loc(self.cam, cam_loc, frame, interp="BEZIER")
        key_loc(self.target, target_loc, frame, interp="BEZIER")
        self.cam.data.lens = lens_mm
        self.cam.data.keyframe_insert(data_path="lens", frame=frame)
        _set_curve_interp(self.cam.data, "lens", frame, interp="BEZIER")

        if dof_fstop is not None:
            self.cam.data.dof.use_dof = True
            self.cam.data.dof.focus_object = self.target
            self.cam.data.dof.aperture_fstop = dof_fstop
        else:
            self.cam.data.dof.use_dof = False


class AnimatedCharacter25D:
    """2.5D character rig with squash-and-stretch root Empty, live 3D Art Deco props & frame-exact expression swaps."""

    def __init__(
        self,
        name: str,
        manifest: dict,
        char_id: str,
        loc: Tuple[float, float, float],
        rot_z_deg: float,
        variants: List[dict],
        mats: Dict[str, bpy.types.Material],
        flip_x: bool = False,
        scale: float = 1.0,
        emission_boost: float = 0.07,
    ):
        chars_col = get_or_create_collection("Chars_25D")
        self.name = name
        self.char_id = char_id
        self.base_scale = scale

        self.root = bpy.data.objects.new(f"Rig_{name}", None)
        self.root.location = Vector(loc)
        self.root.rotation_euler = Euler((0.0, 0.0, math.radians(rot_z_deg)), "XYZ")
        link_obj_exclusive(self.root, chars_col)

        self.cards: Dict[str, bpy.types.Object] = {}
        first_angle = variants[0].get("angle") or "front"

        for idx, v in enumerate(variants):
            key = v["key"]
            card = spawn_character_card(
                name=f"{name}_{key}",
                manifest=manifest,
                char_id=char_id,
                loc=(0.0, 0.0, 0.0),
                rot_z_deg=0.0,
                expression=v.get("expression"),
                angle=v.get("angle"),
                back_expression=v.get("back_expression"),
                flip_x=flip_x,
                scale=scale,
                emission_boost=emission_boost,
                mats=mats,
                use_3d_props=False,  # Attach shared 3D Art Deco props once to self.root!
            )
            # Re-bind sprite to noprops version cleanly since we mount real 3D Art Deco props onto self.root!
            from .characters_3d import _build_card_material, resolve_sprite_path

            eff_angle = v.get("angle") or "front"
            front_p = resolve_sprite_path(manifest, char_id, expression=v.get("expression"), angle=eff_angle, noprops=True)
            if v.get("back_expression"):
                back_p = resolve_sprite_path(manifest, char_id, expression=v.get("back_expression"), angle="front", noprops=True)
            elif v.get("back_angle"):
                back_p = resolve_sprite_path(manifest, char_id, angle=v.get("back_angle"), noprops=True)
            else:
                back_p = None
            card.data.materials[0] = _build_card_material(
                f"Mat_{name}_{key}",
                front_path=front_p,
                back_path=back_p,
                emission_boost=emission_boost,
                flip_front_x=flip_x,
            )
            card.parent = self.root
            self.cards[key] = card
            if idx > 0:
                card.hide_render = True
                card.hide_viewport = True

        # Attach true 3D Art Deco handheld props directly to self.root so they bounce & move with character!
        self.props = attach_3d_art_deco_props(
            card_obj=self.root,
            manifest=manifest,
            char_id=char_id,
            angle_key=first_angle,
            mats=mats,
            flip_x=flip_x,
            scale=scale,
        )

    def show_variant(self, active_key: str, frame: float) -> None:
        for key, card in self.cards.items():
            key_visible(card, key == active_key, frame)

    def animate_idle_talk(
        self,
        f0: int,
        f1: int,
        period_frames: int = 18,
        squash: float = 0.045,
        sway_deg: float = 2.2,
    ) -> None:
        """Organic 2.5D squash-and-stretch acting & breathing bounce."""
        base_z = self.root.location.z
        base_rot_z = math.degrees(self.root.rotation_euler.z)
        step = max(4, period_frames // 2)
        f = f0
        phase = 0
        while f <= f1:
            if phase % 2 == 0:
                key_scale(self.root, (1.0 + squash * 0.65, 1.0, 1.0 - squash), f)
                key_rot(self.root, (0.0, -sway_deg if (phase // 2) % 2 == 0 else sway_deg, base_rot_z), f)
            else:
                key_scale(self.root, (1.0 - squash * 0.55, 1.0, 1.0 + squash * 1.1), f)
                key_rot(self.root, (0.0, sway_deg if (phase // 2) % 2 == 0 else -sway_deg, base_rot_z), f)
            f += step
            phase += 1
        key_scale(self.root, (1.0, 1.0, 1.0), f1)
        key_rot(self.root, (0.0, 0.0, base_rot_z), f1)
        self.root.location.z = base_z

    def animate_panic_shake(self, f0: int, f1: int, amp_x: float = 0.045, hop_z: float = 0.06) -> None:
        """Rapid comedic panic/fury shudder with energetic micro-hops!"""
        bx, by, bz = self.root.location.x, self.root.location.y, self.root.location.z
        brz = math.degrees(self.root.rotation_euler.z)
        f = f0
        idx = 0
        while f <= f1:
            sgn = 1.0 if idx % 2 == 0 else -1.0
            lift = hop_z if idx % 4 == 1 else 0.0
            key_loc(self.root, (bx + sgn * amp_x, by, bz + lift), f)
            key_rot(self.root, (0.0, sgn * 3.5, brz), f)
            key_scale(self.root, (1.0 - 0.04 * (lift > 0), 1.0, 1.0 + 0.06 * (lift > 0)), f)
            f += 4
            idx += 1
        key_loc(self.root, (bx, by, bz), f1)
        key_rot(self.root, (0.0, 0.0, brz), f1)
        key_scale(self.root, (1.0, 1.0, 1.0), f1)

    def animate_hop_move(
        self,
        start_loc: Tuple[float, float, float],
        end_loc: Tuple[float, float, float],
        f0: int,
        f1: int,
        hops: int = 4,
        hop_h: float = 0.14,
    ) -> None:
        """Playful 2.5D animated hop-walk arc with squash on takeoff/landing and stretch at apex."""
        steps = max(1, hops)
        seg = (f1 - f0) / steps
        for i in range(steps):
            fa = f0 + i * seg
            fm = fa + seg * 0.5
            fb = f0 + (i + 1) * seg
            t0 = i / steps
            tm = (i + 0.5) / steps
            t1 = (i + 1) / steps
            p0 = (start_loc[0] + (end_loc[0] - start_loc[0]) * t0, start_loc[1] + (end_loc[1] - start_loc[1]) * t0, start_loc[2])
            pm = (start_loc[0] + (end_loc[0] - start_loc[0]) * tm, start_loc[1] + (end_loc[1] - start_loc[1]) * tm, start_loc[2] + hop_h)
            p1 = (start_loc[0] + (end_loc[0] - start_loc[0]) * t1, start_loc[1] + (end_loc[1] - start_loc[1]) * t1, start_loc[2])

            key_loc(self.root, p0, fa)
            key_scale(self.root, (1.06, 1.0, 0.93), fa)
            key_loc(self.root, pm, fm)
            key_scale(self.root, (0.94, 1.0, 1.08), fm)
            key_loc(self.root, p1, fb)
            key_scale(self.root, (1.05, 1.0, 0.95), fb)
        key_scale(self.root, (1.0, 1.0, 1.0), f1)


# ==============================================================================
# 3D ENVIRONMENT & VISUAL METAPHOR ANIMATION HELPERS
# ==============================================================================

def animate_clock_elastic_slow(env: dict, f0: int, f1: int) -> None:
    """3D Visual Metaphor: Giant Clock second hand drags painfully slow like heavy stretched rubber!"""
    sec = env["clock_sec"]
    gear_a = env["clock_gear_a"]
    gear_b = env["clock_gear_b"]
    # Painfully slow stuttering micro-ticks with elastic recoil!
    total = max(1, f1 - f0)
    steps = [
        (0.00, -140.0),
        (0.18, -145.0),  # pulls backward elastically!
        (0.28, -134.0),  # sluggish tick #1
        (0.46, -137.0),
        (0.58, -128.0),  # sluggish tick #2
        (0.76, -131.0),
        (0.88, -122.0),  # sluggish tick #3
        (1.00, -124.0),
    ]
    for ratio, deg in steps:
        fr = f0 + ratio * total
        key_rot(sec, (0.0, deg, 0.0), fr)
        key_rot(gear_a, (90.0, deg * 0.4, 0.0), fr)
        key_rot(gear_b, (90.0, -deg * 0.55, 0.0), fr)


def animate_clock_hyper_spin(env: dict, f0: int, f1: int, turns: float = 3.0) -> None:
    """3D Visual Metaphor: Giant Clock & gears whip wildly fast when mirror makes wait fly by!"""
    sec = env["clock_sec"]
    min_h = env["clock_min"]
    hr_h = env["clock_hour"]
    gear_a = env["clock_gear_a"]
    gear_b = env["clock_gear_b"]

    key_rot(sec, (0.0, -40.0, 0.0), f0)
    key_rot(sec, (0.0, -40.0 + turns * 360.0, 0.0), f1)
    key_rot(min_h, (0.0, -50.0, 0.0), f0)
    key_rot(min_h, (0.0, -50.0 + turns * 95.0, 0.0), f1)
    key_rot(hr_h, (0.0, 60.0, 0.0), f0)
    key_rot(hr_h, (0.0, 60.0 + turns * 25.0, 0.0), f1)
    key_rot(gear_a, (90.0, 0.0, 0.0), f0)
    key_rot(gear_a, (90.0, turns * 240.0, 0.0), f1)
    key_rot(gear_b, (90.0, 0.0, 0.0), f0)
    key_rot(gear_b, (90.0, -turns * 320.0, 0.0), f1)


def animate_elevator_doors(env: dict, side: str, f0: int, f1: int, open_amount: float = 0.72) -> None:
    """Smoothly slide twin Art Deco brass elevator doors open!"""
    bay = env["elev_l"] if side == "L" else env["elev_r"]
    dl = bay["door_l"]
    dr = bay["door_r"]
    xl0, yl0, zl0 = dl.location.x, dl.location.y, dl.location.z
    xr0, yr0, zr0 = dr.location.x, dr.location.y, dr.location.z

    key_loc(dl, (xl0, yl0, zl0), f0)
    key_loc(dr, (xr0, yr0, zr0), f0)
    key_loc(dl, (xl0 - open_amount, yl0, zl0), f1)
    key_loc(dr, (xr0 + open_amount, yr0, zr0), f1)


def animate_dial_needle(env: dict, side: str, deg_start: float, deg_end: float, f0: int, f1: int) -> None:
    bay = env["elev_l"] if side == "L" else env["elev_r"]
    needle = bay["dial_needle"]
    key_rot(needle, (0.0, deg_start, 0.0), f0)
    key_rot(needle, (0.0, deg_end, 0.0), f1)


def animate_collection_drop_in(col: bpy.types.Collection, drop_z: float, f0: int, f_land: int, f_settle: int) -> None:
    """Drop an entire collection (e.g. Grand Art Deco Mirror!) cleanly from above with elastic bounce."""
    for obj in col.objects:
        if obj.parent is not None:
            continue
        bx, by, bz = obj.location.x, obj.location.y, obj.location.z
        key_loc(obj, (bx, by, bz + drop_z), f0)
        key_loc(obj, (bx, by, bz - 0.05), f_land)
        key_loc(obj, (bx, by, bz + 0.04), int((f_land + f_settle) * 0.5))
        key_loc(obj, (bx, by, bz), f_settle)


def animate_collection_slide_x(col: bpy.types.Collection, offset_start_x: float, offset_end_x: float, f0: int, f1: int) -> None:
    """Roll an entire prop collection horizontally (e.g. Clara's 3D Turbo-Rocket Booster Cart!)."""
    for obj in col.objects:
        if obj.parent is not None:
            continue
        bx, by, bz = obj.location.x, obj.location.y, obj.location.z
        key_loc(obj, (bx + offset_start_x, by, bz), f0)
        key_loc(obj, (bx + offset_end_x, by, bz), f1)


def animate_dust_float(dust_col: bpy.types.Collection, f0: int, f1: int) -> None:
    """Gently drift glowing golden dust motes upward & sideways for golden-hour magic."""
    for idx, obj in enumerate(dust_col.objects):
        bx, by, bz = obj.location.x, obj.location.y, obj.location.z
        dx = 0.22 * math.sin(idx * 1.7)
        dz = 0.28 + 0.14 * math.cos(idx * 1.3)
        key_loc(obj, (bx, by, bz), f0)
        key_loc(obj, (bx + dx, by, bz + dz), f1)
