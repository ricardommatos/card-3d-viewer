"""Build and render "collaboration vs distraction": a fan of acrylic cards
against a burst of black dots on wire stems.

    python build.py --scale 0.3 --samples 24     # quick look at all 5 shots
    python build.py                              # full size
"""

import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)

import bpy  # noqa: E402  (bpy first: it provides bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont  # noqa: E402

import acrylic_poster as ap  # noqa: E402
import paper_texture  # noqa: E402
import poster  # noqa: E402
import solids as so  # noqa: E402

ap.PX = 0.003
FULL = (1337, 2000)
FONT_SLAB = os.path.join(HERE, "..", "fonts", "AlfaSlabOne-Regular.ttf")


def make_paper(path, scale=4):
    w, h = poster.W * scale, poster.H * scale
    img = Image.new("RGB", (w, h), tuple(int(c * 255) for c in poster.PAPER))
    noise = Image.effect_noise((w // 2, h // 2), 18).resize((w, h)).filter(ImageFilter.GaussianBlur(0.8))
    img = ImageChops.multiply(img, Image.merge("RGB", [noise.point(lambda v: 250 + (v - 128) * 0.1)] * 3))
    d = ImageDraw.Draw(img)
    ink = (20, 20, 20)
    k = poster.KICKER
    d.text((k["x"] * scale, k["y"] * scale), k["text"], fill=ink, anchor="ls",
           font=ImageFont.truetype(paper_texture.find_font("Inter-Medium.otf", "DejaVuSans.ttf"), k["size"] * scale))
    hl = poster.HEADLINE
    f = ImageFont.truetype(FONT_SLAB, hl["size"] * scale)
    for i, line in enumerate(hl["lines"]):
        d.text((hl["x"] * scale, (hl["y"] + i * hl["size"] * 1.12) * scale), line, font=f, fill=ink, anchor="ls")
    b = poster.BODY_COPY
    f = ImageFont.truetype(paper_texture.find_font("Inter-Regular.otf", "DejaVuSans.ttf"), round(b["size"] * scale))
    line, y = "", b["y"]
    for word in b["text"].split() + [None]:
        trial = (line + " " + word).strip() if word else line
        if word is None or f.getlength(trial) > b["width"] * scale:
            d.text((b["x"] * scale, y * scale), line, font=f, fill=ink, anchor="ls")
            line, y = (word or ""), y + b["leading"]
        else:
            line = trial
    # the eight-stripe IBM mark and a small globe
    lg = poster.LOGO
    f = ImageFont.truetype(FONT_SLAB, 100)
    l, t, r, bt = f.getbbox("IBM")
    mark = Image.new("L", (r - l, bt - t), 0)
    ImageDraw.Draw(mark).text((-l, -t), "IBM", font=f, fill=255)
    mark = mark.resize((lg["w"] * scale, lg["h"] * scale), Image.LANCZOS)
    stripes = Image.new("L", mark.size, 0)
    unit = mark.height / 15
    for i in range(8):
        ImageDraw.Draw(stripes).rectangle((0, 2 * i * unit, mark.width, (2 * i + 1) * unit), fill=255)
    img.paste(Image.new("RGB", mark.size, ink), (lg["x"] * scale, lg["y"] * scale), ImageChops.multiply(mark, stripes))
    gx, gy, gr = (lg["x"] + lg["w"] + 22) * scale, (lg["y"] + lg["h"] / 2) * scale, 14 * scale
    d.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), outline=ink, width=2 * scale)
    for e in (0.35, 0.7):
        d.ellipse((gx - gr * e, gy - gr, gx + gr * e, gy + gr), outline=ink, width=scale)
    d.line((gx - gr, gy, gx + gr, gy), fill=ink, width=scale)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


def stadium(r0, r1, half_w, n=16):
    """Band along +x from r0 to r1 with a round tip; local (x, y) in px."""
    pts = [(r0, -half_w)]
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((r1 - half_w + math.cos(a) * half_w, math.sin(a) * half_w))
    pts.append((r0, half_w))
    return pts


def fan(mats, col):
    hx, hy, hr = poster.HUB
    f = poster.FAN
    hub = so.w(poster, hx, hy)
    thick = 0.006
    for k in range(f["count"]):
        t = k / (f["count"] - 1)
        a = math.radians(f["start"] + (f["end"] - f["start"]) * t)
        ink = poster.FAN_COLORS[k % len(poster.FAN_COLORS)]
        bm = bmesh.new()
        # local frame: x along the band, z across it, y = thickness (towards the paper)
        face = bm.faces.new([bm.verts.new((x * ap.PX, 0, -y * ap.PX))
                             for x, y in stadium(hr * 0.7, f["radius"], f["band"] / 2)])
        ext = bmesh.ops.extrude_face_region(bm, geom=[face], use_keep_orig=True)
        bmesh.ops.translate(bm, verts=[g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)],
                            vec=Vector((0, thick, 0)))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        mesh = bpy.data.meshes.new(f"fan_{k:02d}")
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(mats[ink])
        obj = bpy.data.objects.new(mesh.name, mesh)
        col.objects.link(obj)
        # a fanned hand of cards: each a little further out, each turned on
        # its own long axis like a turbine blade
        depth = 0.03 + 0.011 * k
        obj.location = hub + Vector((0, -depth, 0))
        obj.rotation_euler = (math.radians(42) * math.sin(math.pi * t), a, 0)
        mod = obj.modifiers.new("soft", "BEVEL")
        mod.width, mod.segments = 0.0012, 2


def burst(mats, col):
    hx, hy, _ = poster.HUB
    b = poster.BURST
    rnd = random.Random(b["seed"])
    hub = so.w(poster, hx, hy, 0.04)
    stems, dots = bmesh.new(), bmesh.new()
    for _ in range(b["count"]):
        a = math.radians(rnd.uniform(*b["angle"]))
        r = b["radius"][0] + (b["radius"][1] - b["radius"][0]) * math.sqrt(rnd.random())
        tip = so.w(poster, hx + math.cos(a) * r, hy + math.sin(a) * r, rnd.uniform(0.02, 0.55) ** 1.2 + 0.02)
        d = tip - hub
        rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.create_cone(stems, cap_ends=True, segments=6, radius1=0.0012, radius2=0.0012, depth=d.length,
                              matrix=Matrix.Translation((hub + tip) / 2) @ rot)
        bmesh.ops.create_uvsphere(dots, u_segments=20, v_segments=10, radius=b["dot"] * ap.PX,
                                  matrix=Matrix.Translation(tip))
    for name, bm, mat in (("burst_stems", stems, mats["stem"]), ("burst_dots", dots, mats["dot"])):
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for p in mesh.polygons:
            p.use_smooth = True
        mesh.materials.append(mat)
        col.objects.link(bpy.data.objects.new(name, mesh))


def setup():
    tex = make_paper(os.path.join(HERE, "build", "paper.png"))
    scene = ap.reset_scene()
    root = scene.collection
    cols = {n: bpy.data.collections.new(n) for n in ("Poster", "Studio", "Lights", "Cameras")}
    for c in cols.values():
        root.children.link(c)
    inks = poster.INKS
    ap.paper_board(poster, ap.paper_material("paper", tex, poster.PAPER),
                   ap.matte_material("board_edge", poster.PAPER, 0.9), cols["Poster"])
    mats = {ink: ap.acrylic_material(f"card_{ink}", inks[ink]) for ink in poster.FAN_COLORS}
    mats["dot"] = ap.gloss_black_material("dot_black", inks["black"])
    mats["stem"] = ap.matte_material("stem_black", inks["black"], 0.4, 0.3)
    fan(mats, cols["Poster"])
    burst(mats, cols["Poster"])
    hx, hy, hr = poster.HUB
    so.cylinder(poster, "hub", hx, hy, hr, 0.06, ap.lacquer_material("hub_white", inks["white"]), cols["Poster"],
                bevel=0.01)

    ap.cyclorama(ap.matte_material("studio", (0.2, 0.195, 0.19), 0.9), cols["Studio"])
    world_ = bpy.data.worlds.new("World")
    world_.use_nodes = True
    world_.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.08
    scene.world = world_

    c = ap.poster_center(poster)
    L, C = cols["Lights"], cols["Cameras"]
    hub = so.w(poster, hx, hy, 0.15)
    print_rig = [ap.sun_light("print_sun", L, (-0.07, -1.0, 0.06), 4.0, 1.5)]
    studio_rig = [
        ap.spot_light("studio_key", L, hub + Vector((-2.4, -2.0, 2.4)), hub, 6500, 45, 0.7, 0.1, (1.0, 0.95, 0.88)),
        ap.area_light("studio_rim", L, hub + Vector((2.6, -0.8, 1.0)), hub, 1.5, 500, (0.85, 0.92, 1.0)),
        ap.area_light("studio_fill", L, hub + Vector((0.3, -5, 0.3)), hub, 5.0, 120),
    ]
    shots = {
        "front": ap.camera("cam_front", C, (0, -10, c.z), c, ortho_scale=poster.H * ap.PX),
        "three_quarter": ap.camera("cam_three_quarter", C, hub + Vector((-1.5, -2.4, 0.7)), hub, lens=45,
                                   dof=(hub, 6)),
        "fan": ap.camera("cam_fan", C, hub + Vector((-1.6, -0.9, -0.35)), hub + Vector((-0.25, 0, 0.05)), lens=40),
        "burst": ap.camera("cam_burst", C, hub + Vector((1.7, -1.2, 0.35)), hub + Vector((0.25, 0.05, 0)), lens=40,
                           dof=(hub + Vector((0.3, 0, 0)), 4)),
        "above": ap.camera("cam_above", C, hub + Vector((0.25, -0.75, 1.5)), hub + Vector((0, -0.12, 0)), lens=38,
                           dof=(hub + Vector((0, -0.15, 0)), 5.6)),
    }
    return scene, shots, (print_rig, studio_rig)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="front,three_quarter,fan,burst,above")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--exposure", type=float, default=-0.6)
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)

    scene, shots, (print_rig, studio_rig) = setup()
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "ibm-collaboration.blend"), compress=True)
    if args.no_render:
        return
    size = (round(FULL[0] * args.scale), round(FULL[1] * args.scale))
    for name in filter(None, args.shots.split(",")):
        front = name == "front"
        ap.render(scene, shots[name], os.path.join(HERE, "build", "renders", f"{name}.png"),
                  size, args.samples, print_rig if front else studio_rig, print_rig + studio_rig,
                  "Standard", 1 / 3 if front else 0.8, 0.0 if front else args.exposure)


if __name__ == "__main__":
    main()
