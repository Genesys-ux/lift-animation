"""All 10 animated scenes for 'Cermin Murah yang Mempercepat Lift' (60s, 30 FPS, 9:16).

Each scene builder configures its exact lighting mood, toggleable 3D props (Mirrors, Rocket Cart, Dust),
Bezier camera choreography, 2.5D character acting/expression swaps, and 3D Art Deco handheld props.
"""

from __future__ import annotations

import math
from typing import Dict

import bpy

from .anim_utils import (
    AnimatedCharacter25D,
    CinemaCameraRig,
    animate_clock_elastic_slow,
    animate_clock_hyper_spin,
    animate_collection_drop_in,
    animate_collection_slide_x,
    animate_dial_needle,
    animate_dust_float,
    animate_elevator_doors,
    key_loc,
    key_rot,
)
from .characters_3d import clear_characters
from .environment import set_collection_visibility
from .lighting import apply_lighting_mood


def build_scene(
    scene_id: int,
    num_frames: int,
    env: dict,
    mats: Dict[str, bpy.types.Material],
    manifest: dict,
) -> CinemaCameraRig:
    """Populate animation keyframes for scene `scene_id` spanning frames [1, num_frames]."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = num_frames

    clear_characters()
    cam = CinemaCameraRig(f"Cam_S{scene_id:02d}")
    f0, f1 = 1, num_frames

    def _f(ratio: float) -> int:
        return max(f0, min(f1, int(round(f0 + ratio * (f1 - f0)))))

    # =========================================================================
    # SCENE 1 — HOOK: Grand Art Deco Lobby Push-In & Foreground Parallax
    # =========================================================================
    if scene_id == 1:
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("morning_busy", mats, env["dust_col"])

        animate_clock_elastic_slow(env, f0, f1)
        animate_dial_needle(env, "L", -56.0, -52.0, f0, f1)

        doni = AnimatedCharacter25D(
            "Doni_S01", manifest, "doni", (-1.85, 3.25, 0.0), -8.0,
            [{"key": "furious", "angle": "three_quarter"}], mats,
        )
        doni.animate_panic_shake(f0, f1, amp_x=0.03, hop_z=0.04)

        bima = AnimatedCharacter25D(
            "Bima_S01", manifest, "bima", (0.35, 2.40, 0.0), -4.0,
            [{"key": "panic", "expression": "panic"}], mats,
        )
        bima.animate_panic_shake(f0, f1, amp_x=0.045, hop_z=0.05)

        raka = AnimatedCharacter25D(
            "Raka_S01", manifest, "raka", (-0.82, 0.95, 0.0), 14.0,
            [{"key": "chill", "angle": "three_quarter"}], mats,
        )
        raka.animate_idle_talk(f0, f1, period_frames=24, squash=0.025, sway_deg=1.4)

        # Sweeping foreground parallax past left stanchion & potted palm -> hero push-in!
        cam.key_shot(f0, (-1.65, -4.95, 1.55), (0.0, 3.80, 2.45), lens_mm=23.0)
        cam.key_shot(_f(0.55), (-0.30, -4.20, 1.75), (0.0, 4.10, 2.35), lens_mm=25.5)
        cam.key_shot(f1, (0.05, -3.15, 1.65), (0.0, 4.30, 2.20), lens_mm=28.0)

    # =========================================================================
    # SCENE 2 — ANGRY WAIT: Whip-Pan to Furious Pak Doni + Crawling Floor Dial
    # =========================================================================
    elif scene_id == 2:
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("midday_stress", mats, env["dust_col"])

        animate_clock_elastic_slow(env, f0, f1)
        animate_dial_needle(env, "L", -52.0, -46.0, f0, f1)

        doni = AnimatedCharacter25D(
            "Doni_S02", manifest, "doni", (-1.18, 3.40, 0.0), -10.0,
            [
                {"key": "furious_3q", "angle": "three_quarter"},
                {"key": "furious_front", "expression": "furious"},
            ],
            mats,
        )
        doni.show_variant("furious_3q", f0)
        doni.show_variant("furious_front", _f(0.45))
        doni.animate_panic_shake(f0, f1, amp_x=0.04, hop_z=0.07)

        bima = AnimatedCharacter25D(
            "Bima_S02", manifest, "bima", (0.55, 2.85, 0.0), -16.0,
            [{"key": "stressed", "expression": "stressed"}], mats,
        )
        bima.animate_idle_talk(f0, f1, period_frames=14, squash=0.04, sway_deg=3.0)

        # Whip-pan from lobby mid -> tight furious Pak Doni -> tilt up to crawling Floor Dial!
        cam.key_shot(f0, (0.65, -1.65, 1.40), (-0.40, 3.20, 1.40), lens_mm=26.0, dof_fstop=4.5)
        cam.key_shot(_f(0.24), (-0.98, 0.85, 1.12), (-1.12, 3.40, 1.05), lens_mm=34.0, dof_fstop=4.0)
        cam.key_shot(_f(0.62), (-1.05, 1.05, 1.15), (-1.15, 3.45, 1.10), lens_mm=38.0, dof_fstop=4.0)
        cam.key_shot(f1, (-1.15, 0.75, 1.55), (-1.75, 4.40, 3.10), lens_mm=42.0, dof_fstop=4.5)

    # =========================================================================
    # SCENE 3 — COMEDY: Panicking Manager & Clara's 3D Turbo-Rocket Cart!
    # =========================================================================
    elif scene_id == 3:
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], True)
        apply_lighting_mood("midday_stress", mats, env["dust_col"])

        animate_collection_slide_x(env["rocket_col"], offset_start_x=2.3, offset_end_x=-0.35, f0=_f(0.28), f1=_f(0.68))

        bima = AnimatedCharacter25D(
            "Bima_S03", manifest, "bima", (-0.55, 2.75, 0.0), 8.0,
            [
                {"key": "panic", "expression": "panic"},
                {"key": "shocked", "expression": "shocked"},
            ],
            mats,
        )
        bima.show_variant("panic", f0)
        bima.show_variant("shocked", _f(0.55))
        bima.animate_panic_shake(f0, _f(0.54), amp_x=0.05, hop_z=0.05)
        bima.animate_idle_talk(_f(0.55), f1, period_frames=12, squash=0.06, sway_deg=3.5)

        clara = AnimatedCharacter25D(
            "Clara_S03", manifest, "clara", (2.60, 2.55, 0.0), -18.0,
            [
                {"key": "excited", "expression": "excited"},
                {"key": "determined", "expression": "determined"},
            ],
            mats,
        )
        clara.show_variant("excited", f0)
        clara.show_variant("determined", _f(0.72))
        clara.animate_hop_move((2.60, 2.55, 0.0), (0.85, 2.55, 0.0), _f(0.24), _f(0.66), hops=3, hop_h=0.14)
        clara.animate_idle_talk(_f(0.66), f1, period_frames=14, squash=0.05, sway_deg=2.8)

        # Crash zoom on panicking Pak Bima -> aggressive whip-pan right to Clara & 3D Rocket Cart!
        cam.key_shot(f0, (-0.65, -0.65, 1.32), (-0.55, 2.75, 1.25), lens_mm=30.0, dof_fstop=4.5)
        cam.key_shot(_f(0.32), (-0.58, 0.25, 1.26), (-0.55, 2.75, 1.22), lens_mm=38.0, dof_fstop=4.2)
        cam.key_shot(_f(0.58), (0.35, -0.85, 1.28), (0.75, 2.55, 1.15), lens_mm=27.0, dof_fstop=4.5)
        cam.key_shot(f1, (0.55, -0.55, 1.22), (0.95, 2.55, 1.05), lens_mm=30.0, dof_fstop=4.2)

    # =========================================================================
    # SCENE 4 — PLOT TWIST: Chill Psychologist Raka Sipping 3D Art Deco Coffee
    # =========================================================================
    elif scene_id == 4:
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], True)
        apply_lighting_mood("midday_stress", mats, env["dust_col"])

        raka = AnimatedCharacter25D(
            "Raka_S04", manifest, "raka", (-0.82, 0.85, 0.0), 16.0,
            [
                {"key": "deadpan", "expression": "deadpan"},
                {"key": "chill", "expression": "chill"},
            ],
            mats,
        )
        raka.show_variant("deadpan", f0)
        raka.show_variant("chill", _f(0.48))
        raka.animate_idle_talk(f0, f1, period_frames=26, squash=0.028, sway_deg=1.5)
        # Subtle 3D coffee cup tilt-and-toast right inside Raka's hand grip (never detaches from fingers!)
        if "coffee" in raka.props:
            cup = raka.props["coffee"]
            key_rot(cup, (0.0, 0.0, 18.0), f0)
            key_rot(cup, (0.0, 16.0, 12.0), _f(0.55))
            key_rot(cup, (0.0, 0.0, 18.0), _f(0.85))

        bima = AnimatedCharacter25D(
            "Bima_S04", manifest, "bima", (0.35, 3.05, 0.0), -10.0,
            [{"key": "skeptical", "expression": "skeptical"}], mats,
        )
        bima.animate_idle_talk(f0, f1, period_frames=22, squash=0.02)

        clara = AnimatedCharacter25D(
            "Clara_S04", manifest, "clara", (1.35, 2.85, 0.0), -22.0,
            [{"key": "confused", "expression": "confused"}], mats,
        )
        clara.animate_idle_talk(f0, f1, period_frames=20, squash=0.025)

        # Smooth dolly gliding past foreground velvet stanchion toward calm Raka!
        cam.key_shot(f0, (-2.15, -2.35, 1.38), (-0.70, 0.95, 1.25), lens_mm=30.0, dof_fstop=4.0)
        cam.key_shot(_f(0.55), (-1.15, -1.65, 1.32), (-0.65, 0.95, 1.25), lens_mm=35.0, dof_fstop=3.8)
        cam.key_shot(f1, (-0.75, -1.35, 1.34), (-0.55, 1.10, 1.28), lens_mm=38.0, dof_fstop=3.8)

    # =========================================================================
    # SCENE 5 — AHA! MOMENT: Raka Raises 3D Gold Mirror + Tilt to Elastic Clock
    # =========================================================================
    elif scene_id == 5:
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("morning_busy", mats, env["dust_col"])

        animate_clock_elastic_slow(env, f0, f1)

        raka = AnimatedCharacter25D(
            "Raka_S05", manifest, "raka", (0.36, 2.15, 0.0), -12.0,
            [
                {"key": "thinking", "expression": "thinking"},
                {"key": "aha", "expression": "aha"},
            ],
            mats,
        )
        raka.show_variant("thinking", f0)
        raka.show_variant("aha", _f(0.24))
        raka.animate_idle_talk(f0, f1, period_frames=16, squash=0.045, sway_deg=2.4)
        # Tilt his gleaming 3D Art Deco Brass Hand Mirror proudly inside his hand grip on the Aha! beat!
        if "mirror" in raka.props:
            hm = raka.props["mirror"]
            key_rot(hm, (0.0, 0.0, -22.0), f0)
            key_rot(hm, (0.0, -14.0, -8.0), _f(0.45))
            key_rot(hm, (0.0, 8.0, -28.0), f1)

        # Low-angle hero shot on Raka -> smooth tilt up toward Giant Mechanical Art Deco Clock!
        cam.key_shot(f0, (0.72, -0.55, 1.32), (0.25, 2.35, 1.48), lens_mm=34.0, dof_fstop=4.0)
        cam.key_shot(_f(0.42), (0.82, -0.45, 1.48), (0.05, 3.85, 2.55), lens_mm=34.0, dof_fstop=4.2)
        cam.key_shot(f1, (0.65, -0.35, 1.72), (0.0, 4.45, 3.75), lens_mm=38.0, dof_fstop=4.5)

    # =========================================================================
    # SCENE 6 — UNOCCUPIED TIME: Claustrophobic Push-In on Plain Doors & Crawling Clock
    # =========================================================================
    elif scene_id == 6:
        set_collection_visibility(env["mirrors_col"], False)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("midday_stress", mats, env["dust_col"])

        animate_clock_elastic_slow(env, f0, f1)
        animate_dial_needle(env, "L", -46.0, -42.0, f0, f1)

        doni = AnimatedCharacter25D(
            "Doni_S06", manifest, "doni", (-1.10, 3.40, 0.0), -10.0,
            [
                {"key": "impatient", "expression": "impatient"},
                {"key": "deadpan", "expression": "deadpan"},
            ],
            mats,
        )
        doni.show_variant("impatient", f0)
        doni.show_variant("deadpan", _f(0.55))
        doni.animate_idle_talk(f0, f1, period_frames=32, squash=0.02, sway_deg=1.0)

        # Relentless slow tense push-in capturing blank brass doors & heavy Giant Clock overhead!
        cam.key_shot(f0, (-0.35, -2.55, 1.45), (-0.45, 4.35, 2.25), lens_mm=27.0, dof_fstop=4.8)
        cam.key_shot(f1, (-0.55, -0.45, 1.55), (-0.55, 4.35, 2.45), lens_mm=35.0, dof_fstop=4.2)

    # =========================================================================
    # SCENE 7 — MIRROR DROP-IN REVEAL: Golden-Hour Magic + Elastic Bounce!
    # =========================================================================
    elif scene_id == 7:
        set_collection_visibility(env["mirrors_col"], True)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("golden_mirror", mats, env["dust_col"])

        animate_collection_drop_in(env["mirrors_col"], drop_z=3.6, f0=_f(0.14), f_land=_f(0.38), f_settle=_f(0.52))
        animate_dust_float(env["dust_col"], f0, f1)

        clara = AnimatedCharacter25D(
            "Clara_S07", manifest, "clara", (1.28, 2.65, 0.0), -20.0,
            [
                {"key": "shocked", "expression": "shocked", "back_angle": "back"},
                {"key": "deadpan", "expression": "deadpan", "back_angle": "back"},
            ],
            mats,
        )
        clara.show_variant("shocked", f0)
        clara.show_variant("deadpan", _f(0.65))
        clara.animate_idle_talk(f0, f1, period_frames=18, squash=0.045, sway_deg=2.2)

        bima = AnimatedCharacter25D(
            "Bima_S07", manifest, "bima", (-1.32, 2.68, 0.0), 18.0,
            [
                {"key": "skeptical", "expression": "skeptical", "back_angle": "back"},
                {"key": "relieved", "expression": "relieved", "back_angle": "back"},
            ],
            mats,
        )
        bima.show_variant("skeptical", f0)
        bima.show_variant("relieved", _f(0.62))
        bima.animate_idle_talk(f0, f1, period_frames=18, squash=0.04, sway_deg=2.0)

        # Dynamic reveal tracking from ceiling -> locked hero frame on gleaming Gold Art Deco Mirror!
        cam.key_shot(f0, (0.0, -2.45, 2.55), (0.0, 4.35, 3.25), lens_mm=24.0)
        cam.key_shot(_f(0.42), (0.0, -1.55, 1.62), (0.0, 4.35, 1.85), lens_mm=27.0)
        cam.key_shot(f1, (0.18, -0.85, 1.55), (0.0, 4.35, 1.75), lens_mm=30.0)

    # =========================================================================
    # SCENE 8 — THE MONEY SHOT: Live 3D Mirror Reflection (Stunned -> Narcissistic!)
    # =========================================================================
    elif scene_id == 8:
        set_collection_visibility(env["mirrors_col"], True)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("golden_mirror", mats, env["dust_col"])

        animate_dust_float(env["dust_col"], f0, f1)
        animate_clock_hyper_spin(env, f0, f1, turns=1.2)

        # Smart Double-Sided Card: camera sees Pak Doni's back 3/4, real 3D Mirror reflects
        # his live comedic expression swap from STUNNED (O_o) -> NARCISSISTIC smolder + 3D Gold Comb!
        doni = AnimatedCharacter25D(
            "Doni_S08", manifest, "doni", (0.14, 3.25, 0.0), 12.0,
            [
                {"key": "stunned_refl", "angle": "back_three_quarter", "back_expression": "stunned"},
                {"key": "narc_refl", "angle": "back_three_quarter", "back_expression": "narcissistic"},
            ],
            mats,
            flip_x=True,
            emission_boost=0.14,
        )
        doni.show_variant("stunned_refl", f0)
        doni.show_variant("narc_refl", _f(0.38))
        doni.animate_idle_talk(f0, f1, period_frames=20, squash=0.04, sway_deg=2.2)

        # Animate his real 3D Gold Art Deco Comb brushing rhythmically right inside his hand grip!
        if "comb" in doni.props:
            comb = doni.props["comb"]
            cx0, cy0, cz0 = comb.location.x, comb.location.y, comb.location.z
            key_loc(comb, (cx0, cy0, cz0), f0)
            key_loc(comb, (cx0 + 0.02, cy0, cz0 + 0.05), _f(0.45))
            key_loc(comb, (cx0 + 0.04, cy0, cz0 + 0.02), _f(0.62))
            key_loc(comb, (cx0 + 0.01, cy0, cz0 + 0.05), _f(0.80))
            key_loc(comb, (cx0, cy0, cz0), f1)
            key_rot(comb, (0.0, 0.0, -18.0), f0)
            key_rot(comb, (0.0, -22.0, -8.0), _f(0.55))
            key_rot(comb, (0.0, 12.0, -22.0), _f(0.78))
            key_rot(comb, (0.0, -14.0, -12.0), f1)

        bima = AnimatedCharacter25D(
            "Bima_S08", manifest, "bima", (-1.22, 2.72, 0.0), 16.0,
            [{"key": "relieved", "expression": "relieved", "back_angle": "back"}], mats,
        )
        bima.animate_idle_talk(f0, f1, period_frames=22, squash=0.03)

        raka = AnimatedCharacter25D(
            "Raka_S08", manifest, "raka", (1.28, 2.82, 0.0), -22.0,
            [{"key": "smug", "expression": "smug", "back_angle": "back"}], mats,
        )
        raka.animate_idle_talk(f0, f1, period_frames=24, squash=0.025)

        # Cinematic over-the-shoulder glide locking Pak Doni's live mirror reflection dead-center!
        cam.key_shot(f0, (-1.05, -0.90, 1.46), (0.04, 4.35, 1.66), lens_mm=24.0, dof_fstop=5.0)
        cam.key_shot(_f(0.45), (-1.15, -0.45, 1.44), (0.02, 4.35, 1.66), lens_mm=27.5, dof_fstop=4.8)
        cam.key_shot(f1, (-1.22, -0.05, 1.42), (-0.04, 4.35, 1.62), lens_mm=31.0, dof_fstop=4.5)

    # =========================================================================
    # SCENE 9 — CLIMAX PAYOFF: Hyper-Spinning Clock + Elevator DING & Doors Open!
    # =========================================================================
    elif scene_id == 9:
        set_collection_visibility(env["mirrors_col"], True)
        set_collection_visibility(env["rocket_col"], False)
        apply_lighting_mood("golden_mirror", mats, env["dust_col"])

        animate_dust_float(env["dust_col"], f0, f1)
        animate_clock_hyper_spin(env, f0, f1, turns=3.5)
        animate_dial_needle(env, "L", -52.0, 58.0, f0, _f(0.46))
        animate_elevator_doors(env, "L", _f(0.48), _f(0.78), open_amount=0.72)

        doni = AnimatedCharacter25D(
            "Doni_S09", manifest, "doni", (-1.55, 3.25, 0.0), 8.0,
            [{"key": "happy", "expression": "happy", "back_angle": "back"}], mats,
        )
        doni.animate_idle_talk(f0, f1, period_frames=14, squash=0.05, sway_deg=3.0)

        bima = AnimatedCharacter25D(
            "Bima_S09", manifest, "bima", (0.25, 2.55, 0.0), -6.0,
            [
                {"key": "relieved", "expression": "relieved", "back_angle": "back"},
                {"key": "proud", "expression": "proud", "back_angle": "back"},
            ],
            mats,
        )
        bima.show_variant("relieved", f0)
        bima.show_variant("proud", _f(0.56))
        bima.animate_hop_move((0.25, 2.55, 0.0), (0.25, 2.35, 0.0), _f(0.56), _f(0.92), hops=3, hop_h=0.18)

        # Whip-tilt UP to Hyper-Spinning Giant Wall Clock -> drop down to Elevator Doors gliding OPEN!
        cam.key_shot(f0, (0.0, -1.25, 2.35), (0.0, 4.45, 4.40), lens_mm=34.0)
        cam.key_shot(_f(0.42), (-0.15, -1.65, 2.25), (-0.10, 4.45, 4.25), lens_mm=30.0)
        cam.key_shot(_f(0.68), (-0.45, -2.35, 1.55), (-0.75, 4.25, 1.65), lens_mm=26.0)
        cam.key_shot(f1, (-0.30, -2.65, 1.52), (-0.55, 4.25, 1.55), lens_mm=25.0)

    # =========================================================================
    # SCENE 10 — OUTRO & MICRO-GAG: Raka Toast + Clara Drags Rejected Rocket Away!
    # =========================================================================
    else:
        set_collection_visibility(env["mirrors_col"], True)
        set_collection_visibility(env["rocket_col"], True)
        apply_lighting_mood("golden_mirror", mats, env["dust_col"])

        animate_dust_float(env["dust_col"], f0, f1)
        animate_clock_hyper_spin(env, f0, f1, turns=1.5)
        # Final comedic micro-gag: Clara sheepishly drags her rejected 3D Turbo-Rocket Cart offscreen!
        animate_collection_slide_x(env["rocket_col"], offset_start_x=-0.20, offset_end_x=2.25, f0=_f(0.18), f1=f1)

        raka = AnimatedCharacter25D(
            "Raka_S10", manifest, "raka", (-0.15, 0.75, 0.0), 4.0,
            [
                {"key": "smug", "expression": "smug", "back_angle": "back"},
                {"key": "laugh", "expression": "laugh", "back_angle": "back"},
            ],
            mats,
        )
        raka.show_variant("smug", f0)
        raka.show_variant("laugh", _f(0.48))
        raka.animate_idle_talk(f0, f1, period_frames=16, squash=0.04, sway_deg=2.2)

        # Pak Doni STILL blissfully grooming himself in the Grand Mirror in the background!
        doni = AnimatedCharacter25D(
            "Doni_S10", manifest, "doni", (0.12, 3.30, 0.0), 10.0,
            [{"key": "narc", "angle": "back_three_quarter", "back_expression": "narcissistic"}],
            mats, flip_x=True, emission_boost=0.14,
        )
        doni.animate_idle_talk(f0, f1, period_frames=20, squash=0.03)

        bima = AnimatedCharacter25D(
            "Bima_S10", manifest, "bima", (-1.45, 2.65, 0.0), 14.0,
            [{"key": "proud", "expression": "proud", "back_angle": "back"}], mats,
        )
        bima.animate_idle_talk(f0, f1, period_frames=18, squash=0.04)

        clara = AnimatedCharacter25D(
            "Clara_S10", manifest, "clara", (1.45, 2.50, 0.0), -14.0,
            [{"key": "deadpan", "expression": "deadpan"}], mats,
        )
        clara.animate_hop_move((1.45, 2.50, 0.0), (3.40, 2.50, 0.0), _f(0.18), f1, hops=5, hop_h=0.08)

        # Heroic closing pull-back down the golden Art Deco lobby carpet!
        cam.key_shot(f0, (-0.15, -1.75, 1.45), (-0.10, 0.85, 1.38), lens_mm=32.0, dof_fstop=4.5)
        cam.key_shot(_f(0.55), (-0.05, -3.35, 1.65), (0.0, 2.85, 1.95), lens_mm=26.5, dof_fstop=5.6)
        cam.key_shot(f1, (0.0, -4.85, 1.85), (0.0, 4.35, 2.45), lens_mm=24.0, dof_fstop=None)

    return cam
