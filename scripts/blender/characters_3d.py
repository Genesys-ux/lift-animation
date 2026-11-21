"""2.5D Character Card placement inside Blender 3D with exact metric scale, alpha-cutout shadows & mirror backfacing."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import bmesh
import bpy
from mathutils import Euler

from .compat import get_or_create_collection, link_obj_exclusive, set_material_alpha_cutout
from .props_3d import attach_3d_art_deco_props, clear_handheld_props

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "assets" / "characters" / "manifest.json"


def load_character_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def resolve_sprite_path(
    manifest: dict,
    char_id: str,
    expression: Optional[str] = None,
    angle: Optional[str] = None,
    noprops: bool = False,
) -> Path:
    """Resolve the PNG path for either an expression sprite (front) or a turnaround angle sprite."""
    char_entry = manifest["characters"][char_id]
    if angle and angle != "front":
        key = "turnaround_noprops" if (noprops and "turnaround_noprops" in char_entry) else "turnaround"
        rel = char_entry[key][angle]["png"]
        return (REPO_ROOT / rel).resolve()
    expr = expression or char_entry["default_expression"]
    key = "sprites_noprops" if (noprops and "sprites_noprops" in char_entry) else "sprites"
    rel = char_entry[key][expr]["png"]
    return (REPO_ROOT / rel).resolve()


def _load_image(path: Path) -> bpy.types.Image:
    abs_str = str(path.resolve())
    for img in bpy.data.images:
        if Path(bpy.path.abspath(img.filepath)).resolve() == path.resolve():
            return img
    img = bpy.data.images.load(abs_str, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    img.alpha_mode = "STRAIGHT"
    return img


def _build_card_material(
    name: str,
    front_path: Path,
    back_path: Optional[Path] = None,
    emission_boost: float = 0.06,
    flip_front_x: bool = False,
) -> bpy.types.Material:
    """Build a 2.5D stylized card shader receiving 3D ambient light tint + casting alpha-cutout shadows."""
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    set_material_alpha_cutout(mat)

    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (760, 0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (420, 0)
    bsdf.inputs["Roughness"].default_value = 0.86
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.08
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_boost

    # UV Mapping for front face
    uv_node = nt.nodes.new("ShaderNodeTexCoord")
    uv_node.location = (-840, 120)

    front_map = nt.nodes.new("ShaderNodeMapping")
    front_map.location = (-600, 220)
    if flip_front_x:
        front_map.inputs["Location"].default_value = (1.0, 0.0, 0.0)
        front_map.inputs["Scale"].default_value = (-1.0, 1.0, 1.0)
    nt.links.new(uv_node.outputs["UV"], front_map.inputs["Vector"])

    tex_front = nt.nodes.new("ShaderNodeTexImage")
    tex_front.location = (-340, 240)
    tex_front.image = _load_image(front_path)
    tex_front.extension = "CLIP"
    nt.links.new(front_map.outputs["Vector"], tex_front.inputs["Vector"])

    if back_path is None:
        color_out = tex_front.outputs["Color"]
        alpha_out = tex_front.outputs["Alpha"]
    else:
        # Smart Double-Sided Card (Front faces camera, Back faces mirror for true live mirror reflections!)
        geom = nt.nodes.new("ShaderNodeNewGeometry")
        geom.location = (-340, 460)

        back_map = nt.nodes.new("ShaderNodeMapping")
        back_map.location = (-600, -140)
        # Mirror horizontally on back face so reflection reads naturally in the 3D mirror
        back_map.inputs["Location"].default_value = (1.0, 0.0, 0.0)
        back_map.inputs["Scale"].default_value = (-1.0, 1.0, 1.0)
        nt.links.new(uv_node.outputs["UV"], back_map.inputs["Vector"])

        tex_back = nt.nodes.new("ShaderNodeTexImage")
        tex_back.location = (-340, -140)
        tex_back.image = _load_image(back_path)
        tex_back.extension = "CLIP"
        nt.links.new(back_map.outputs["Vector"], tex_back.inputs["Vector"])

        mix_col = nt.nodes.new("ShaderNodeMix")
        mix_col.data_type = "RGBA"
        mix_col.location = (20, 180)
        nt.links.new(geom.outputs["Backfacing"], mix_col.inputs["Factor"])
        nt.links.new(tex_front.outputs["Color"], mix_col.inputs[6])
        nt.links.new(tex_back.outputs["Color"], mix_col.inputs[7])
        color_out = mix_col.outputs[2]

        mix_alpha = nt.nodes.new("ShaderNodeMix")
        mix_alpha.data_type = "FLOAT"
        mix_alpha.location = (20, -60)
        nt.links.new(geom.outputs["Backfacing"], mix_alpha.inputs["Factor"])
        nt.links.new(tex_front.outputs["Alpha"], mix_alpha.inputs[2])
        nt.links.new(tex_back.outputs["Alpha"], mix_alpha.inputs[3])
        alpha_out = mix_alpha.outputs[0]

    # Crisp binary alpha threshold so shadows & cutout edges have zero fuzzy halo
    alpha_clip = nt.nodes.new("ShaderNodeMath")
    alpha_clip.operation = "GREATER_THAN"
    alpha_clip.location = (210, -140)
    alpha_clip.inputs[1].default_value = 0.42
    nt.links.new(alpha_out, alpha_clip.inputs[0])

    nt.links.new(color_out, bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        nt.links.new(color_out, bsdf.inputs["Emission Color"])
    bsdf.inputs["Alpha"].default_value = 1.0

    # Explicit Transparent BSDF Mix guarantees 100% pure zero-halo transparent cutout in BOTH EEVEE Next & Cycles!
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    trans.location = (420, -240)
    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    mix_sh.location = (620, 0)
    nt.links.new(alpha_clip.outputs["Value"], mix_sh.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix_sh.inputs[1])
    nt.links.new(bsdf.outputs["BSDF"], mix_sh.inputs[2])
    nt.links.new(mix_sh.outputs["Shader"], out.inputs["Surface"])

    return mat


def spawn_character_card(
    name: str,
    manifest: dict,
    char_id: str,
    loc: Tuple[float, float, float],
    rot_z_deg: float = 0.0,
    expression: Optional[str] = None,
    angle: Optional[str] = None,
    back_expression: Optional[str] = None,
    flip_x: bool = False,
    scale: float = 1.0,
    emission_boost: float = 0.06,
    mats: Optional[Dict[str, bpy.types.Material]] = None,
    use_3d_props: bool = True,
) -> bpy.types.Object:
    """Create a grounded 2.5D character card in 'Chars_25D' + optional true 3D Art Deco props in 'Env_3D'!

    At rot_z_deg = 0, the card faces -Y (straight toward a camera looking +Y into the elevator wall).
    """
    chars_col = get_or_create_collection("Chars_25D")
    noprops = bool(use_3d_props and mats is not None)
    effective_angle = angle or "front"

    cw, ch = manifest["canvas_px"]
    ppm = float(manifest["pixels_per_meter"])
    floor_uv_y = float(manifest["floor_uv_y"])

    plane_w = (cw / ppm) * scale
    plane_h = (ch / ppm) * scale
    z_bot = -floor_uv_y * plane_h
    z_top = (1.0 - floor_uv_y) * plane_h
    half_w = plane_w * 0.5

    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    # Quad in XZ plane with front normal pointing cleanly toward -Y!
    v0 = bm.verts.new((-half_w, 0.0, z_bot))
    v1 = bm.verts.new((half_w, 0.0, z_bot))
    v2 = bm.verts.new((half_w, 0.0, z_top))
    v3 = bm.verts.new((-half_w, 0.0, z_top))
    face = bm.faces.new((v0, v1, v2, v3))

    uv_layer = bm.loops.layers.uv.new("UVMap")
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler((0.0, 0.0, math.radians(rot_z_deg)), "XYZ")

    front_path = resolve_sprite_path(manifest, char_id, expression=expression, angle=effective_angle, noprops=noprops)
    back_path = (
        resolve_sprite_path(manifest, char_id, expression=back_expression, angle="front", noprops=noprops)
        if back_expression
        else None
    )

    mat = _build_card_material(
        name=f"Mat_{name}",
        front_path=front_path,
        back_path=back_path,
        emission_boost=emission_boost,
        flip_front_x=flip_x,
    )
    obj.data.materials.append(mat)
    link_obj_exclusive(obj, chars_col)

    # Mount true 3D Art Deco stylized Toon-PBR handheld props directly onto character's gripping hands!
    if noprops and mats is not None:
        attach_3d_art_deco_props(
            card_obj=obj,
            manifest=manifest,
            char_id=char_id,
            angle_key=effective_angle,
            mats=mats,
            flip_x=flip_x,
            scale=scale,
        )

    return obj


def clear_characters() -> None:
    clear_handheld_props()
    if "Chars_25D" not in bpy.data.collections:
        return
    col = bpy.data.collections["Chars_25D"]
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
