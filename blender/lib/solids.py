"""Small solid-building helpers in poster pixel space (y down), shared by
the block-style posters. Depth is metres off the paper, towards the viewer."""

import math

import bpy
import bmesh
from mathutils import Vector

import acrylic_poster as ap


def w(poster, x, y, depth=0.0):
    wx, wz = ap.to_world(poster, x, y)
    return Vector((wx, -depth, wz))


def link(obj, collection):
    for col in obj.users_collection:
        col.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def prism(poster, name, pts_px, depth, material, collection, base=0.0, bevel=0.003):
    """Extrude a px outline from the paper (or from `base`) out to `base + depth`."""
    bm = bmesh.new()
    face = bm.faces.new([bm.verts.new(w(poster, x, y, base)) for x, y in pts_px])
    ext = bmesh.ops.extrude_face_region(bm, geom=[face], use_keep_orig=True)
    moved = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=Vector((0, -depth, 0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.set_sharp_from_angle(angle=math.radians(35))
    for m in material if isinstance(material, tuple) else (material,):
        mesh.materials.append(m)
    if len(mesh.materials) > 1:
        for poly in mesh.polygons:
            poly.material_index = 1 if poly.normal.y > 0.99 else 0
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if bevel:
        mod = obj.modifiers.new("soft", "BEVEL")
        mod.width, mod.segments = bevel, 3
        mod.limit_method = "ANGLE"
        mod.harden_normals = True
    return obj


def rect(x, y, wd, ht):
    return [(x, y), (x + wd, y), (x + wd, y + ht), (x, y + ht)]


def cylinder(poster, name, cx, cy, r_px, depth, material, collection, base=0.0, bevel=0.003):
    c = w(poster, cx, cy, base + depth / 2)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r_px * ap.PX, depth=depth, location=c,
                                        rotation=(math.radians(90), 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material if not isinstance(material, tuple) else material[0])
    bpy.ops.object.shade_smooth()
    if bevel:
        mod = obj.modifiers.new("soft", "BEVEL")
        mod.width, mod.segments = bevel, 3
        mod.limit_method = "ANGLE"
        mod.harden_normals = True
    return link(obj, collection)


def sphere(poster, name, cx, cy, r_px, sink, material, collection):
    """Sphere half sunk into the paper (sink = fraction of radius below)."""
    r = r_px * ap.PX
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r,
                                         location=w(poster, cx, cy, r * (1 - 2 * sink)))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return link(obj, collection)


def blade(poster, name, cx, cy, angle, r0_px, r1_px, width_px, depth, material, collection, base=0.0):
    """Thin radial fin from r0 to r1 around (cx, cy), `angle` radians (px space)."""
    ca, sa = math.cos(angle), math.sin(angle)
    hw = width_px / 2
    pts = [(cx + ca * r - sa * s * hw, cy + sa * r + ca * s * hw)
           for r, s in ((r0_px, -1), (r1_px, -1), (r1_px, 1), (r0_px, 1))]
    return prism(poster, name, pts, depth, material, collection, base, bevel=0.0015)
