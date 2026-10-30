"""Build and render the IBM "nervous system" block city.

    python build.py --scale 0.3 --samples 24     # quick look at all 5 shots
    python build.py                              # full size
"""

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)

import bpy  # noqa: E402  (bpy first: it provides bmesh)
from mathutils import Vector  # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont  # noqa: E402

import acrylic_poster as ap  # noqa: E402
import paper_texture  # noqa: E402
import poster  # noqa: E402
import solids as so  # noqa: E402

ap.PX = 0.003
FULL = (1361, 2000)
FONT_SLAB = os.path.join(HERE, "..", "fonts", "AlfaSlabOne-Regular.ttf")


def rgb(name):
    return tuple(int(c * 255) for c in poster.INKS[name])


def make_paper(path, scale=4):
    """Headline, body copy and the striped IBM mark, printed on light stock."""
    w, h = poster.W * scale, poster.H * scale
    img = Image.new("RGB", (w, h), tuple(int(c * 255) for c in poster.PAPER))
    noise = Image.effect_noise((w // 2, h // 2), 18).resize((w, h)).filter(ImageFilter.GaussianBlur(0.8))
    img = ImageChops.multiply(img, Image.merge("RGB", [noise.point(lambda v: 250 + (v - 128) * 0.1)] * 3))
    d = ImageDraw.Draw(img)
    hl = poster.HEADLINE
    f = ImageFont.truetype(FONT_SLAB, hl["size"] * scale)
    for i, line in enumerate(hl["lines"]):
        d.text((hl["x"] * scale, (hl["y"] + i * hl["size"] * 1.1) * scale), line, font=f, fill=rgb(hl["ink"]),
               anchor="ls")
    b = poster.BODY_COPY
    body_font = paper_texture.find_font("Inter-Regular.otf", "DejaVuSans.ttf")
    f = ImageFont.truetype(body_font, round(b["size"] * scale))
    words, line, y = b["text"].split(), "", b["y"]
    for word in words + [None]:
        trial = (line + " " + word).strip() if word else line
        if word is None or f.getlength(trial) > b["width"] * scale:
            d.text((b["x"] * scale, y * scale), line, font=f, fill=rgb(b["ink"]), anchor="ls")
            line, y = (word or ""), y + b["leading"]
        else:
            line = trial
    # striped IBM: the word set in slab, cut into five coloured stripes
    lg = poster.LOGO_STRIPES
    f = ImageFont.truetype(FONT_SLAB, 100)
    l, t, r, bt = f.getbbox("IBM")
    mark = Image.new("L", (r - l, bt - t), 0)
    ImageDraw.Draw(mark).text((-l, -t), "IBM", font=f, fill=255)
    mark = mark.resize((lg["w"] * scale, lg["h"] * scale), Image.LANCZOS)
    n = len(lg["colors"])
    unit = mark.height / (2 * n - 1)
    for i, col in enumerate(lg["colors"]):
        band = Image.new("L", mark.size, 0)
        ImageDraw.Draw(band).rectangle((0, 2 * i * unit, mark.width, (2 * i + 1) * unit), fill=255)
        img.paste(Image.new("RGB", mark.size, rgb(col)), (lg["x"] * scale, lg["y"] * scale),
                  ImageChops.multiply(mark, band))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


def build_blocks(mats, col):
    c = poster.CELL
    for i, b in enumerate(poster.BLOCKS):
        gx, gy, gw, gh = b["box"]
        x, y, bw, bh = poster.GX + gx * c, poster.GY + gy * c, gw * c, gh * c
        pad = 2.5
        kind, name, h = b["kind"], f"b{i:02d}_{b['kind']}", b["h"]
        mat = mats.get((b.get("finish", "lacquer"), b["ink"] if isinstance(b["ink"], str) else None))
        if kind == "rect":
            so.prism(poster, name, so.rect(x + pad, y + pad, bw - 2 * pad, bh - 2 * pad), h, mat, col)
        elif kind == "rect_inset":
            so.prism(poster, name, so.rect(x + pad, y + pad, bw - 2 * pad, bh - 2 * pad), h, mat, col)
            so.prism(poster, name + "_inset", so.rect(x + bw * 0.3, y + bh * 0.62, bw * 0.4, bh * 0.2),
                     0.05, mats[("lacquer", "white")], col, base=h)
        elif kind == "circle":
            so.cylinder(poster, name, x + bw / 2, y + bh / 2, min(bw, bh) / 2 - pad, h, mat, col)
        elif kind in ("stripes_v", "stripes_h"):
            n = b["n"]
            for k in range(n):
                if kind == "stripes_v":
                    unit = (bw - 2 * pad) / (2 * n - 1)
                    pts = so.rect(x + pad + 2 * k * unit, y + pad, unit, bh - 2 * pad)
                else:
                    unit = (bh - 2 * pad) / (2 * n - 1)
                    pts = so.rect(x + pad, y + pad + 2 * k * unit, bw - 2 * pad, unit)
                # fins rise in a wave, so the set reads as one gesture in 3D
                so.prism(poster, f"{name}_{k}", pts, h * (0.6 + 0.4 * math.sin(math.pi * (k + 0.5) / n)), mat, col)
        elif kind == "dots":
            cols_ = gw
            r = c * 0.42
            for k, ink in enumerate(b["ink"]):
                cx = x + (k % cols_ + 0.5) * c
                cy = y + (k // cols_ + 0.5) * c
                so.sphere(poster, f"{name}_{k}", cx, cy, r, 0.15, mats[("lacquer", ink)], col)
        elif kind == "sunburst":
            cx, cy, rr = x + bw / 2, y + bh / 2, min(bw, bh) / 2 - pad
            for k in range(b["n"]):
                a = 2 * math.pi * k / b["n"]
                so.blade(poster, f"{name}_{k}", cx, cy, a, rr * 0.28, rr, 3.0,
                         h * (0.5 + 0.5 * (k % 2)), mats[("glass", b["ink"])], col)
        elif kind == "sunburst_disc":
            cx, cy, rr = x + bw / 2, y + bh / 2, min(bw, bh) / 2 - pad
            so.cylinder(poster, name, cx, cy, rr, h, mats[("lacquer", b["ink"])], col)
            for k in range(b["n"]):
                so.blade(poster, f"{name}_{k}", cx, cy, 2 * math.pi * k / b["n"], rr * 0.3, rr * 0.88, 2.2,
                         0.03, mats[("lacquer", "white")], col, base=h)


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
    mats = {}
    for ink, srgb in inks.items():
        mats[("lacquer", ink)] = ap.lacquer_material(f"lacquer_{ink}", srgb)
        mats[("glass", ink)] = ap.acrylic_material(f"glass_{ink}", srgb)
        mats[("frosted", ink)] = ap.frosted_materials(f"frosted_{ink}", srgb)
        mats[("gloss", ink)] = ap.gloss_black_material(f"gloss_{ink}", srgb)
    build_blocks(mats, cols["Poster"])

    ap.cyclorama(ap.matte_material("studio", (0.5, 0.5, 0.5), 0.9), cols["Studio"])
    world_ = bpy.data.worlds.new("World")
    world_.use_nodes = True
    world_.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.1
    scene.world = world_

    c = ap.poster_center(poster)
    L, C = cols["Lights"], cols["Cameras"]
    city = so.w(poster, 245, 520, 0.1)
    print_rig = [ap.sun_light("print_sun", L, (-0.07, -1.0, 0.06), 4.0, 1.5)]
    studio_rig = [
        # a low "late afternoon" sun across the city, long shadows
        ap.sun_light("studio_sun", L, (-1.0, -0.55, 0.45), 3.2, 2.0),
        ap.area_light("studio_fill", L, city + Vector((2.5, -4, 0.5)), city, 5.0, 300, (0.85, 0.9, 1.0)),
    ]
    shots = {
        "front": ap.camera("cam_front", C, (0, -10, c.z), c, ortho_scale=poster.H * ap.PX),
        "three_quarter": ap.camera("cam_three_quarter", C, city + Vector((-1.4, -2.3, 0.9)), city, lens=40,
                                   dof=(city, 8)),
        # from just below the poster's foot, grazing up along the surface
        "skyline": ap.camera("cam_skyline", C, so.w(poster, 330, 712, 0.62), so.w(poster, 230, 450, 0.1),
                             lens=30),
        "sunburst": ap.camera("cam_sunburst", C, so.w(poster, 400, 330, 0.85), so.w(poster, 295, 430, 0.05),
                              lens=60, dof=(so.w(poster, 295, 430, 0.08), 2.8)),
        "aerial": ap.camera("cam_aerial", C, city + Vector((1.2, -1.6, 1.5)), city, lens=35),
    }
    return scene, shots, (print_rig, studio_rig)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="front,three_quarter,skyline,sunburst,aerial")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--exposure", type=float, default=-0.6)
    p.add_argument("--no-render", action="store_true")
    args = p.parse_args(argv)

    scene, shots, (print_rig, studio_rig) = setup()
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "ibm-nervous-system.blend"), compress=True)
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
