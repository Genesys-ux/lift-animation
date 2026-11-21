"""Procedural Stylized Toon-PBR material library for the Grand Art Deco Skyscraper Lobby."""

from __future__ import annotations

from typing import Dict, Tuple

import bpy


def _new_mat(name: str) -> tuple[bpy.types.Material, bpy.types.NodeTree, bpy.types.ShaderNodeBsdfPrincipled]:
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (520, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat, nt, bsdf


def _set_input(node: bpy.types.Node, name: str, val) -> None:
    if name in node.inputs:
        node.inputs[name].default_value = val


def build_material_library() -> Dict[str, bpy.types.Material]:
    """Create and return the full Stylized Toon-PBR Art Deco material dictionary."""
    mats: Dict[str, bpy.types.Material] = {}

    # 1. Checkered Emerald & Warm Ivory Marble Floor (with procedural veining + tile grout bump!)
    mat, nt, bsdf = _new_mat("ArtDeco_CheckeredMarble")
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-950, 0)

    # Rotate 45° for iconic diamond-checkered Art Deco grand lobby tiles!
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.location = (-740, 80)
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, 0.785398)
    mapping.inputs["Scale"].default_value = (1.15, 1.15, 1.15)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    checker = nt.nodes.new("ShaderNodeTexChecker")
    checker.location = (-500, 140)
    checker.inputs["Scale"].default_value = 8.0
    # Warm ivory vs rich Art Deco deep emerald-slate marble
    checker.inputs["Color1"].default_value = (0.86, 0.80, 0.67, 1.0)
    checker.inputs["Color2"].default_value = (0.055, 0.175, 0.155, 1.0)
    nt.links.new(mapping.outputs["Vector"], checker.inputs["Vector"])

    # Stylized marble veining noise
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-520, -140)
    noise.inputs["Scale"].default_value = 3.6
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Distortion"].default_value = 1.6
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    vein_ramp = nt.nodes.new("ShaderNodeValToRGB")
    vein_ramp.location = (-280, -140)
    vein_ramp.color_ramp.elements[0].position = 0.44
    vein_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    vein_ramp.color_ramp.elements[1].position = 0.56
    vein_ramp.color_ramp.elements[1].color = (0.85, 0.74, 0.46, 1.0)
    nt.links.new(noise.outputs["Fac"], vein_ramp.inputs["Fac"])

    mix_vein = nt.nodes.new("ShaderNodeMix")
    mix_vein.data_type = "RGBA"
    mix_vein.blend_type = "MIX"
    mix_vein.location = (-40, 80)
    mix_vein.inputs["Factor"].default_value = 0.16
    nt.links.new(checker.outputs["Color"], mix_vein.inputs[6])
    nt.links.new(vein_ramp.outputs["Color"], mix_vein.inputs[7])
    nt.links.new(mix_vein.outputs[2], bsdf.inputs["Base Color"])

    # Subtle roughness variation across marble polish
    rough_map = nt.nodes.new("ShaderNodeMapRange")
    rough_map.location = (-40, -120)
    rough_map.inputs["From Min"].default_value = 0.25
    rough_map.inputs["From Max"].default_value = 0.75
    rough_map.inputs["To Min"].default_value = 0.14
    rough_map.inputs["To Max"].default_value = 0.28
    nt.links.new(noise.outputs["Fac"], rough_map.inputs["Value"])
    nt.links.new(rough_map.outputs["Result"], bsdf.inputs["Roughness"])

    _set_input(bsdf, "Coat Weight", 0.35)
    _set_input(bsdf, "Coat Roughness", 0.08)
    mats["floor_marble"] = mat

    # 2. Deep Emerald-Teal Architectural Wall Paneling
    mat, nt, bsdf = _new_mat("ArtDeco_EmeraldWall")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 5.5
    ns.inputs["Detail"].default_value = 4.0
    ns.inputs["Distortion"].default_value = 0.8
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.045, 0.155, 0.145, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.095, 0.255, 0.225, 1.0)
    nt.links.new(ns.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_input(bsdf, "Roughness", 0.36)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.05
    nt.links.new(ns.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mats["emerald_wall"] = mat

    # 3. Warm Champagne Art Deco Plaster (upper walls & coffered ceiling)
    mat, nt, bsdf = _new_mat("ArtDeco_WarmPlaster")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 9.0
    ns.inputs["Detail"].default_value = 5.0
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.2
    ramp.color_ramp.elements[0].color = (0.76, 0.67, 0.52, 1.0)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (0.89, 0.81, 0.66, 1.0)
    nt.links.new(ns.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_input(bsdf, "Roughness", 0.62)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.07
    nt.links.new(ns.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mats["warm_plaster"] = mat

    # 4. Brushed Art Deco Gold Brass (Elevator Doors, Frame, Clock, Mirror Frame, Chandelier)
    mat, nt, bsdf = _new_mat("ArtDeco_BrushedBrass")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.5, 1.5, 22.0)  # Horizontal brushed grain
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 6.0
    ns.inputs["Detail"].default_value = 5.0
    nt.links.new(mp.outputs["Vector"], ns.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.68, 0.48, 0.16, 1.0)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.94, 0.74, 0.30, 1.0)
    nt.links.new(ns.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_input(bsdf, "Metallic", 0.88)
    _set_input(bsdf, "Roughness", 0.25)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    nt.links.new(ns.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mats["brass"] = mat

    # 5. Dark Architectural Bronze (recesses, elevator door inlays, window mullions)
    mat, nt, bsdf = _new_mat("ArtDeco_DarkBronze")
    _set_input(bsdf, "Base Color", (0.14, 0.10, 0.075, 1.0))
    _set_input(bsdf, "Metallic", 0.82)
    _set_input(bsdf, "Roughness", 0.32)
    mats["dark_bronze"] = mat

    # 6. Warm Walnut Wood (Concierge Desk, Wainscoting, Bench)
    mat, nt, bsdf = _new_mat("ArtDeco_WalnutWood")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.inputs["Scale"].default_value = 4.2
    wv.inputs["Distortion"].default_value = 4.5
    wv.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.2
    ramp.color_ramp.elements[0].color = (0.14, 0.065, 0.032, 1.0)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (0.34, 0.165, 0.075, 1.0)
    nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_input(bsdf, "Roughness", 0.34)
    _set_input(bsdf, "Coat Weight", 0.25)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.06
    nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mats["walnut"] = mat

    # 7. Plush Royal Burgundy Art Deco Runner Carpet (deep velvety contrast, zero white sheen washout!)
    mat, nt, bsdf = _new_mat("ArtDeco_CrimsonCarpet")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 46.0
    ns.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (0.18, 0.018, 0.028, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.34, 0.036, 0.048, 1.0)
    nt.links.new(ns.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_input(bsdf, "Roughness", 0.94)
    _set_input(bsdf, "Specular IOR Level", 0.12)
    _set_input(bsdf, "Sheen Weight", 0.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.14
    nt.links.new(ns.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mats["carpet_red"] = mat

    # 8. Gold Carpet Trim
    mat, nt, bsdf = _new_mat("ArtDeco_CarpetGold")
    _set_input(bsdf, "Base Color", (0.82, 0.62, 0.20, 1.0))
    _set_input(bsdf, "Roughness", 0.75)
    mats["carpet_gold"] = mat

    # 9. Frosted Warm Sconce & Chandelier Glass (Dynamic emission controlled by lighting mood!)
    mat, nt, bsdf = _new_mat("ArtDeco_FrostedGlass")
    _set_input(bsdf, "Base Color", (1.0, 0.91, 0.72, 1.0))
    _set_input(bsdf, "Roughness", 0.28)
    _set_input(bsdf, "Emission Color", (1.0, 0.84, 0.52, 1.0))
    _set_input(bsdf, "Emission Strength", 4.5)
    mats["sconce_glass"] = mat

    # 10. Clock & Floor Dial Illuminated Cream Enamel Face
    mat, nt, bsdf = _new_mat("ArtDeco_ClockFace")
    _set_input(bsdf, "Base Color", (0.98, 0.94, 0.82, 1.0))
    _set_input(bsdf, "Roughness", 0.22)
    _set_input(bsdf, "Emission Color", (1.0, 0.93, 0.76, 1.0))
    _set_input(bsdf, "Emission Strength", 0.85)
    mats["clock_face"] = mat

    # 11. Hero Crimson Lacquer (Clock Second Hand, Floor Dial Needle, Rocket Nosecone!)
    mat, nt, bsdf = _new_mat("ArtDeco_CrimsonLacquer")
    _set_input(bsdf, "Base Color", (0.82, 0.11, 0.09, 1.0))
    _set_input(bsdf, "Roughness", 0.24)
    _set_input(bsdf, "Coat Weight", 0.4)
    mats["crimson_lacquer"] = mat

    # 12. TRUE ART DECO MIRROR GLASS (Physical mirror + translucent portal glass tint for fast zero-raytrace CI!)
    mat, nt, bsdf = _new_mat("ArtDeco_MirrorGlass")
    _set_input(bsdf, "Base Color", (0.94, 0.97, 0.99, 1.0))
    _set_input(bsdf, "Metallic", 1.0)
    _set_input(bsdf, "Roughness", 0.012)
    _set_input(bsdf, "IOR", 1.52)
    mats["mirror_glass"] = mat

    # Crisp subtle warm-white corner glass highlight streak (2.5D animated mirror sheen!)
    mat, nt, bsdf = _new_mat("ArtDeco_MirrorSheen")
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.22
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (1.0, 0.97, 0.88, 1.0)
    emit.inputs["Strength"].default_value = 1.35
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emit.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    if hasattr(mat, "use_transparent_shadow"):
        mat.use_transparent_shadow = True
    mats["mirror_sheen"] = mat

    # 13. Stylized Lobby Palm Foliage
    mat, nt, bsdf = _new_mat("ArtDeco_Foliage")
    _set_input(bsdf, "Base Color", (0.09, 0.34, 0.16, 1.0))
    _set_input(bsdf, "Roughness", 0.42)
    _set_input(bsdf, "Subsurface Weight", 0.15)
    mats["foliage"] = mat

    # 14. Brushed Riveted Steel (Clara's Over-Engineered Turbo-Rocket Cart!)
    mat, nt, bsdf = _new_mat("Prop_BrushedSteel")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 14.0
    ns.inputs["Detail"].default_value = 5.0
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.48, 0.54, 0.62, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.76, 0.81, 0.88, 1.0)
    nt.links.new(ns.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_input(bsdf, "Metallic", 0.85)
    _set_input(bsdf, "Roughness", 0.28)
    mats["steel"] = mat

    # 15. Elevator Call Button Glow (Glowing Red/Amber!)
    mat, nt, bsdf = _new_mat("ArtDeco_ButtonGlow")
    _set_input(bsdf, "Base Color", (1.0, 0.24, 0.16, 1.0))
    _set_input(bsdf, "Emission Color", (1.0, 0.22, 0.12, 1.0))
    _set_input(bsdf, "Emission Strength", 8.0)
    mats["button_glow"] = mat

    # 16. Emerald Banker's Lamp Shade (Concierge Desk)
    mat, nt, bsdf = _new_mat("ArtDeco_BankerGreen")
    _set_input(bsdf, "Base Color", (0.06, 0.48, 0.24, 1.0))
    _set_input(bsdf, "Roughness", 0.18)
    _set_input(bsdf, "Emission Color", (0.12, 0.78, 0.36, 1.0))
    _set_input(bsdf, "Emission Strength", 2.2)
    mats["banker_green"] = mat

    # 17. Window Sky Glass (Emissive mood backdrop right outside arched windows)
    mat, nt, bsdf = _new_mat("ArtDeco_WindowSky")
    _set_input(bsdf, "Base Color", (0.85, 0.93, 1.0, 1.0))
    _set_input(bsdf, "Emission Color", (0.95, 0.90, 0.78, 1.0))
    _set_input(bsdf, "Emission Strength", 3.2)
    mats["window_sky"] = mat

    # 18. Crisp Cream & Red Complaint Papers (Concierge Desk)
    mat, nt, bsdf = _new_mat("Prop_PaperCream")
    _set_input(bsdf, "Base Color", (0.95, 0.92, 0.84, 1.0))
    _set_input(bsdf, "Roughness", 0.85)
    mats["paper_cream"] = mat

    mat, nt, bsdf = _new_mat("Prop_PaperRed")
    _set_input(bsdf, "Base Color", (0.86, 0.18, 0.14, 1.0))
    _set_input(bsdf, "Roughness", 0.80)
    mats["paper_red"] = mat

    # 19. Golden Floating Dust Mote Particles
    mat, nt, bsdf = _new_mat("FX_GoldenDust")
    _set_input(bsdf, "Base Color", (1.0, 0.88, 0.55, 1.0))
    _set_input(bsdf, "Emission Color", (1.0, 0.82, 0.42, 1.0))
    _set_input(bsdf, "Emission Strength", 6.5)
    mats["dust_mote"] = mat

    # 20. Art Deco Polished Saddle Leather (Pak Doni's Briefcase & Watch Strap)
    mat, nt, bsdf = _new_mat("Prop_SaddleLeather")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 28.0
    ns.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.22, 0.085, 0.028, 1.0)
    ramp.color_ramp.elements[1].position = 0.80
    ramp.color_ramp.elements[1].color = (0.44, 0.19, 0.065, 1.0)
    nt.links.new(ns.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set_input(bsdf, "Roughness", 0.34)
    _set_input(bsdf, "Coat Weight", 0.28)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.06
    nt.links.new(ns.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mats["leather"] = mat

    # 21. Prussian Blueprint Blue (Clara's Rolled Rocket Schematic)
    mat, nt, bsdf = _new_mat("Prop_BlueprintBlue")
    _set_input(bsdf, "Base Color", (0.045, 0.23, 0.58, 1.0))
    _set_input(bsdf, "Roughness", 0.65)
    mats["blueprint_blue"] = mat

    # 22. Panic Sticky Note Yellow (Pak Bima's Clipboard)
    mat, nt, bsdf = _new_mat("Prop_StickyYellow")
    _set_input(bsdf, "Base Color", (0.96, 0.78, 0.16, 1.0))
    _set_input(bsdf, "Roughness", 0.72)
    mats["sticky_yellow"] = mat

    # 23. Art Deco Café Cream Porcelain/Paper Cup (Raka's Coffee Cup)
    mat, nt, bsdf = _new_mat("Prop_CoffeeCream")
    _set_input(bsdf, "Base Color", (0.95, 0.90, 0.78, 1.0))
    _set_input(bsdf, "Roughness", 0.38)
    _set_input(bsdf, "Coat Weight", 0.18)
    mats["coffee_cream"] = mat

    return mats
