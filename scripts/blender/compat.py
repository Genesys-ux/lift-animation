"""Blender 4.2 LTS / 4.5 / 5.x compatibility helpers for headless EEVEE + Freestyle rendering."""

from __future__ import annotations

import bpy


def configure_eevee_render(
    scene: bpy.types.Scene,
    width: int = 1080,
    height: int = 1920,
    samples: int = 32,
    use_freestyle: bool = True,
    line_thickness: float = 1.45,
    engine: str = "eevee",
) -> None:
    """Configure Blender EEVEE Next (default for fast headless CI) or Cycles CPU+OIDN cleanly."""
    available_engines = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}

    if engine.lower() == "cycles":
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = samples
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.055
        scene.cycles.use_denoising = True
        if hasattr(scene.cycles, "denoiser"):
            scene.cycles.denoiser = "OPENIMAGEDENOISE"
        scene.cycles.max_bounces = 3
        scene.cycles.diffuse_bounces = 1
        scene.cycles.glossy_bounces = 2
        scene.cycles.transmission_bounces = 1
        scene.cycles.transparent_max_bounces = 4
        scene.cycles.volume_bounces = 0
        scene.cycles.sample_clamp_indirect = 6.0
    else:
        if "BLENDER_EEVEE_NEXT" in available_engines:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        else:
            scene.render.engine = "BLENDER_EEVEE"

        eevee = scene.eevee
        if hasattr(eevee, "taa_render_samples"):
            eevee.taa_render_samples = samples
        if hasattr(eevee, "use_raytracing"):
            eevee.use_raytracing = True
            if hasattr(eevee, "ray_tracing_options"):
                rto = eevee.ray_tracing_options
                if hasattr(rto, "resolution_scale"):
                    rto.resolution_scale = "2"
                if hasattr(rto, "trace_max_roughness"):
                    rto.trace_max_roughness = 0.5
        if hasattr(eevee, "use_shadows"):
            eevee.use_shadows = True
        if hasattr(eevee, "shadow_resolution_scale"):
            eevee.shadow_resolution_scale = 1.0
        if hasattr(eevee, "use_gtao"):
            eevee.use_gtao = True

    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False

    # Punchy cinematic color management (AgX Medium High Contrast if available)
    vs = scene.view_settings
    try:
        vs.view_transform = "AgX"
        for look_name in ("AgX - Medium High Contrast", "AgX - Punchy", "None"):
            try:
                vs.look = look_name
                break
            except Exception:
                continue
    except Exception:
        vs.view_transform = "Filmic"
    vs.exposure = 0.05
    vs.gamma = 1.0

    # Subtle stylized Freestyle ink outlines (applied ONLY to 3D environment collection later!)
    scene.render.use_freestyle = use_freestyle
    scene.render.line_thickness_mode = "ABSOLUTE"
    scene.render.line_thickness = line_thickness


def configure_freestyle_for_collection(
    scene: bpy.types.Scene,
    env_collection: bpy.types.Collection,
    ink_color: tuple[float, float, float] = (0.04, 0.03, 0.06),
    thickness: float = 1.35,
    crease_angle_deg: float = 132.0,
) -> None:
    """Restrict Freestyle outlines strictly to the 3D Environment so 2.5D character cards have zero box outlines."""
    import math

    view_layer = scene.view_layers[0]
    view_layer.use_freestyle = True
    fs = view_layer.freestyle_settings
    fs.crease_angle = math.radians(crease_angle_deg)

    # Clear any default line sets
    while len(fs.linesets) > 0:
        fs.linesets.remove(fs.linesets[0])

    ls = fs.linesets.new("ArtDeco_ToonInk")
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    ls.select_contour = True
    ls.select_external_contour = True
    ls.select_edge_mark = False
    ls.select_by_collection = True
    ls.collection = env_collection
    ls.collection_negation = "INCLUSIVE"
    ls.visibility = "VISIBLE"

    style = ls.linestyle
    style.color = ink_color
    style.alpha = 0.84
    style.thickness = thickness
    style.thickness_position = "CENTER"
    style.caps = "ROUND"


def set_material_alpha_cutout(mat: bpy.types.Material) -> None:
    """Configure crisp alpha-cutout shading + accurate alpha-shaped shadow casting in Blender 4.2+ EEVEE."""
    if hasattr(mat, "surface_render_method"):
        # Blender 4.2+ EEVEE Next: DITHERED renders true alpha-cutout shadows and depth sorting!
        mat.surface_render_method = "DITHERED"
    if hasattr(mat, "blend_method"):
        try:
            mat.blend_method = "CLIP"
        except Exception:
            pass
    if hasattr(mat, "shadow_method"):
        try:
            mat.shadow_method = "CLIP"
        except Exception:
            pass
    if hasattr(mat, "alpha_threshold"):
        mat.alpha_threshold = 0.5
    mat.use_backface_culling = False


def get_or_create_collection(name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    target_parent = parent or bpy.context.scene.collection
    target_parent.children.link(col)
    return col


def link_obj_exclusive(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def clear_scene() -> None:
    """Start from a completely clean Blender scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    if scene.world is None:
        world = bpy.data.worlds.new("LobbyWorld")
        scene.world = world
    scene.world.use_nodes = True
