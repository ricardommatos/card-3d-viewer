"""Build a 'poster as coloured acrylic sculpture' scene in Blender.

Every ink layer of a flat poster becomes a slab of tinted acrylic floating
at its own distance in front of the printed paper. Seen head-on through an
orthographic camera the slabs line up into the original poster (overlaps mix
subtractively like overprinted ink); from any other angle the composition
opens up into depth, throwing coloured shadows onto the paper.

Generic: a poster module supplies W, H, INKS, PAPER, SHAPES (see
olivetti-a/poster.py) and this module does the rest.
"""

import math
import os

import bpy
import bmesh
from mathutils import Vector

from shapes2d import resolve, signed_area

PX = 0.001          # metres per poster pixel
BOARD_DEPTH = 0.025
FLOOR_GAP = 0.12    # poster board floats slightly above the floor


def srgb_to_linear(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def to_world(poster, x, y):
    """Poster px (y down) -> world X/Z on the paper plane (Y = 0)."""
    return ((x - poster.W / 2) * PX, (poster.H - y) * PX + FLOOR_GAP)


# ---------------------------------------------------------------- scene


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    cy = scene.cycles
    cy.device = "CPU"
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    # coloured shadows come from the shadow-ray trick in the acrylic shader,
    # so true caustics (slow, noisy) can stay off
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.max_bounces = 16
    cy.transmission_bounces = 16
    cy.transparent_max_bounces = 32
    cy.glossy_bounces = 6
    scene.view_settings.view_transform = "Standard"  # keep the inks graphic, not filmic
    scene.render.film_transparent = False
    return scene


def _node(nodes, kind, loc, **inputs):
    n = nodes.new(kind)
    n.location = loc
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def acrylic_material(name, srgb, frost=0.015, strength=0.42):
    """Tinted acrylic that also casts tinted (not black) shadows.

    Light reaching the paper passes the slab once (shadow tint) and the camera
    looks through it twice (in and out), so the base tint is the cube root of
    the target ink colour; stacked, it lands back on the ink. ``strength``
    trades that exactness (1/3) for richer colour when seen at an angle.
    """
    mat = bpy.data.materials.new(name)
    mat["ink_srgb"] = srgb
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = _node(nodes, "ShaderNodeOutputMaterial", (600, 0))
    glass = _node(nodes, "ShaderNodeBsdfPrincipled", (0, 120), **{
        "Roughness": frost, "IOR": 1.49, "Transmission Weight": 1.0})
    glass.name = "glass"
    shadow = _node(nodes, "ShaderNodeBsdfTransparent", (0, -260))
    shadow.name = "shadow"
    path = _node(nodes, "ShaderNodeLightPath", (-300, 300))
    mix = _node(nodes, "ShaderNodeMixShader", (350, 0))
    links.new(path.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    links.new(glass.outputs["BSDF"], mix.inputs[1])
    links.new(shadow.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    set_tint(mat, strength)
    return mat


def set_tint(mat, strength):
    strength = max(strength, mat.get("min_tint", 0.0))
    tint = tuple(c ** strength for c in srgb_to_linear(mat["ink_srgb"])) + (1.0,)
    mat.node_tree.nodes["glass"].inputs["Base Color"].default_value = tint
    mat.node_tree.nodes["shadow"].inputs["Color"].default_value = tint


def gloss_black_material(name, srgb):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = srgb_to_linear(srgb) + (1.0,)
    # mirror-polished lacquer: a tight highlight stays out of the near-axis
    # "print" light, so it reads as solid ink head-on and reflects the
    # coloured slabs from an angle
    p.inputs["Roughness"].default_value = 0.02
    return mat


def resin_material(name, srgb, thickness, glow=0.0):
    """Cast resin block: clear surface, colour absorbed inside the volume, so
    thin edges glow pale and the thick core goes deep. Density is scaled to
    the block's thickness so every block lands near its ink head-on.
    glow > 0 makes the volume emit its own colour, like edge-lit acrylic."""
    c = tuple(x ** 0.5 for x in srgb_to_linear(srgb)) + (1.0,)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = _node(nodes, "ShaderNodeOutputMaterial", (600, 0))
    glass = _node(nodes, "ShaderNodeBsdfPrincipled", (0, 120), **{
        "Base Color": (1, 1, 1, 1), "Roughness": 0.01, "IOR": 1.54, "Transmission Weight": 1.0})
    shadow = _node(nodes, "ShaderNodeBsdfTransparent", (0, -260))
    path = _node(nodes, "ShaderNodeLightPath", (-300, 300))
    mix = _node(nodes, "ShaderNodeMixShader", (350, 0))
    vol = _node(nodes, "ShaderNodeVolumeAbsorption", (350, -250), Color=c, Density=1.6 / thickness)
    links.new(path.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    links.new(glass.outputs["BSDF"], mix.inputs[1])
    links.new(shadow.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    if glow:
        emit = _node(nodes, "ShaderNodeEmission", (350, -450), Color=c, Strength=glow / thickness)
        add = _node(nodes, "ShaderNodeAddShader", (500, -300))
        links.new(vol.outputs["Volume"], add.inputs[0])
        links.new(emit.outputs["Emission"], add.inputs[1])
        links.new(add.outputs["Shader"], out.inputs["Volume"])
    else:
        links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return mat


def frosted_materials(name, srgb):
    """Satin-back acrylic: polished face towards the viewer (no glare under
    the print light), frosted face towards the paper, which softens what
    shows through. Returns (polished, frosted)."""
    pair = []
    for suffix, frost in (("", 0.015), ("_back", 0.3)):
        mat = acrylic_material(name + suffix, srgb, frost=frost)
        mat["min_tint"] = 0.75  # scattering slabs need more pigment
        set_tint(mat, 0.75)
        pair.append(mat)
    return tuple(pair)


def lacquer_material(name, srgb):
    """Opaque painted block under a mirror clear coat. The base layer has no
    specular of its own, so the near-axis print light can't wash it out."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes["Principled BSDF"]
    # a touch deeper than the ink: opaque paint reads lighter than overprint
    p.inputs["Base Color"].default_value = tuple(c ** 1.3 for c in srgb_to_linear(srgb)) + (1.0,)
    p.inputs["Roughness"].default_value = 0.4
    p.inputs["Specular IOR Level"].default_value = 0.0
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.02
    return mat


def paper_material(name, texture_path, srgb):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    p = nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.85
    if texture_path:
        tex = _node(nodes, "ShaderNodeTexImage", (-400, 200))
        tex.image = bpy.data.images.load(texture_path)
        tex.interpolation = "Cubic"
        links.new(tex.outputs["Color"], p.inputs["Base Color"])
        bump = _node(nodes, "ShaderNodeBump", (-200, -200), Strength=0.04, Distance=0.002)
        links.new(tex.outputs["Color"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], p.inputs["Normal"])
    else:
        p.inputs["Base Color"].default_value = srgb_to_linear(srgb) + (1.0,)
    return mat


def matte_material(name, srgb, roughness=0.7, specular=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = srgb_to_linear(srgb) + (1.0,)
    p.inputs["Roughness"].default_value = roughness
    p.inputs["Specular IOR Level"].default_value = specular
    return mat


FINISHES = ("clear", "frosted", "resin", "lacquer", "card")


def finish_material(poster, spec, cache):
    """Material(s) for a shape's ink + finish (default: clear acrylic, black
    inks as mirror lacquer): one material, or (front, back-face) for frosted.
    Resin is per shape, since it depends on depth."""
    ink = spec["ink"]
    finish = spec.get("finish", "gloss" if ink in ("black", "brown") else "clear")
    srgb = poster.INKS[ink]
    if finish == "resin":
        return resin_material(f"resin_{ink}_{len(cache)}", srgb, spec["depth"])
    key = (ink, finish)
    if key not in cache:
        name = f"{finish}_{ink}"
        cache[key] = {
            "clear": lambda: acrylic_material(name, srgb),
            "frosted": lambda: frosted_materials(name, srgb),
            "lacquer": lambda: lacquer_material(name, srgb),
            "card": lambda: matte_material(name, srgb, 0.85, 0.15),
            "gloss": lambda: gloss_black_material(name, srgb),
        }[finish]()
    return cache[key]


# ---------------------------------------------------------------- geometry


def slab(poster, name, spec, material, collection):
    """Extrude one traced shape into a slab between y=-z and y=-(z+depth)."""
    pts = resolve(spec["pts"])
    if signed_area(pts) > 0:  # y-down px space: make it CCW once flipped to Z-up
        pts.reverse()
    z0, z1 = -spec["z"], -(spec["z"] + spec["depth"])
    bm = bmesh.new()
    front = [bm.verts.new((*_xz(poster, x, y, z0),)) for x, y in pts]
    face = bm.faces.new(front)
    ext = bmesh.ops.extrude_face_region(bm, geom=[face], use_keep_orig=True)  # closed slab
    moved = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=Vector((0, z1 - z0, 0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.set_sharp_from_angle(angle=math.radians(35))
    for m in material if isinstance(material, tuple) else (material,):
        mesh.materials.append(m)
    if len(mesh.materials) > 1:  # second material goes on the face towards the paper
        for poly in mesh.polygons:
            poly.material_index = 1 if poly.normal.y > 0.99 else 0
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    bev = obj.modifiers.new("edge", "BEVEL")
    bev.width = spec.get("bevel", 0.0025)
    bev.segments = 3
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(35)
    bev.harden_normals = True
    return obj


def _xz(poster, x, y, depth_y):
    wx, wz = to_world(poster, x, y)
    return wx, depth_y, wz


def paper_board(poster, material, edge_material, collection):
    w, h = poster.W * PX, poster.H * PX
    bpy.ops.mesh.primitive_plane_add(size=1)
    face = bpy.context.object
    face.name = "paper"
    face.scale = (w, h, 1)
    face.rotation_euler = (math.radians(90), 0, 0)
    face.location = (0, -0.0005, h / 2 + FLOOR_GAP)
    face.data.materials.append(material)
    bpy.ops.mesh.primitive_cube_add(size=1)
    board = bpy.context.object
    board.name = "board"
    board.scale = (w, BOARD_DEPTH, h)
    board.location = (0, BOARD_DEPTH / 2, h / 2 + FLOOR_GAP)
    board.data.materials.append(edge_material)
    for o in (face, board):
        for c in o.users_collection:
            c.objects.unlink(o)
        collection.objects.link(o)


def cyclorama(material, collection, radius=2.5, size=30):
    """Floor that sweeps up into a back wall, so there is no horizon line."""
    bm = bmesh.new()
    prof = [(-size, 0.0)]
    back = 3.0
    for i in range(17):
        a = math.radians(90 * i / 16)
        prof.append((back - radius + radius * math.sin(a), radius - radius * math.cos(a)))
    prof.append((back, size))
    rows = []
    for x in (-size, size):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if bm.faces[0].normal.z < 0:  # an open sheet can come out facing away from the studio
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new("cyclorama")
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(material)
    obj = bpy.data.objects.new("cyclorama", mesh)
    obj.visible_shadow = False  # the tall sweep must never shade the set from a low sun
    collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------- build


def build(poster, texture_path=None, backdrop=(0.16, 0.155, 0.15), variant=None):
    """variant: name of an entry in poster.VARIANTS, whose per-shape overrides
    (finish, z, depth, bevel...) are laid over SHAPES."""
    overrides = getattr(poster, "VARIANTS", {}).get(variant, {}) if variant else {}
    shapes = {n: {**s, **overrides.get(n, {})} for n, s in poster.SHAPES.items()}
    scene = reset_scene()
    root = scene.collection
    cols = {n: bpy.data.collections.new(n) for n in ("Poster", "Studio", "Lights", "Cameras")}
    for c in cols.values():
        root.children.link(c)

    cache = {}
    for name, spec in shapes.items():
        slab(poster, name, spec, finish_material(poster, spec, cache), cols["Poster"])

    paper_board(poster, paper_material("paper", texture_path, poster.PAPER),
                matte_material("board_edge", poster.PAPER, 0.9), cols["Poster"])
    cyclorama(matte_material("studio", backdrop, 0.9), cols["Studio"])

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.85, 0.85, 0.85, 1)
    bg.inputs["Strength"].default_value = 0.05
    scene.world = world
    return scene, cols


def poster_center(poster):
    return Vector((0, 0, poster.H * PX / 2 + FLOOR_GAP))


def area_light(name, collection, location, target, size, power, color=(1, 1, 1), size_y=None):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.color = color
    if size_y:
        data.shape = "RECTANGLE"
        data.size, data.size_y = size, size_y
    else:
        data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    look_at(obj, target)
    collection.objects.link(obj)
    return obj


def sun_light(name, collection, direction_from, strength, angle_deg=1.0):
    """Sun shining from direction_from (a vector pointing towards the light)."""
    data = bpy.data.lights.new(name, "SUN")
    data.energy = strength
    data.angle = math.radians(angle_deg)
    obj = bpy.data.objects.new(name, data)
    obj.rotation_euler = (-Vector(direction_from)).to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(obj)
    return obj


def spot_light(name, collection, location, target, power, cone_deg, blend, radius, color=(1, 1, 1)):
    data = bpy.data.lights.new(name, "SPOT")
    data.energy = power
    data.color = color
    data.spot_size = math.radians(cone_deg)
    data.spot_blend = blend
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    look_at(obj, target)
    collection.objects.link(obj)
    return obj


def camera(name, collection, location, target, lens=50, ortho_scale=None, dof=None):
    data = bpy.data.cameras.new(name)
    if ortho_scale:
        data.type = "ORTHO"
        data.ortho_scale = ortho_scale
    else:
        data.lens = lens
    if dof:
        data.dof.use_dof = True
        data.dof.focus_distance = (Vector(dof[0]) - Vector(location)).length
        data.dof.aperture_fstop = dof[1]
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    look_at(obj, target)
    collection.objects.link(obj)
    return obj


def look_at(obj, target):
    direction = Vector(target) - Vector(obj.location)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render(scene, cam, path, size, samples, lights_on, all_lights, view="Standard", tint=1 / 3, exposure=0.0):
    """view: "Standard" keeps flat inks exact; "AgX" rolls off studio highlights.
    tint: acrylic colour strength (see acrylic_material)."""
    scene.camera = cam
    for mat in bpy.data.materials:
        if "ink_srgb" in mat:
            set_tint(mat, tint)
    scene.view_settings.view_transform = view
    scene.view_settings.look = "AgX - Punchy" if view == "AgX" else "None"
    scene.view_settings.exposure = exposure
    for light in all_lights:
        light.hide_render = light not in lights_on
        light.hide_viewport = light not in lights_on
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.cycles.samples = samples
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
