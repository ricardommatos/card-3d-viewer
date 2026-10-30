"""Build and render the Olivetti "A" acrylic sculpture.

    pip install bpy==5.2.3        # or run inside Blender:
    python build.py                       # build .blend + render every shot
    python build.py --shots front --scale 0.3 --samples 32   # quick look
    python build.py --reveal --shots none # flat poster -> sculpture animation
    python build.py --variant mixed       # mixed finishes: resin, lacquer, card...
    blender --background --python build.py -- --no-render   # .blend only
"""

import argparse
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import acrylic_poster as ap  # noqa: E402
import paper_texture  # noqa: E402
import poster  # noqa: E402

FULL = (1577, 2000)


def setup(variant=None):
    tex = paper_texture.make(poster, os.path.join(HERE, "build", "paper.png"))
    scene, cols = ap.build(poster, tex, variant=variant)
    c = ap.poster_center(poster)
    L, C = cols["Lights"], cols["Cameras"]

    # "print" rig: a sun almost on the lens axis, so every slab's coloured
    # shadow lands just beside it on the paper, like slightly off-register ink
    print_rig = [ap.sun_light("print_sun", L, (-0.07, -1.0, 0.06), 4.0, 1.5)]
    # "studio" rig: one raking spot from high left pools light on the poster
    # and throws long coloured shadows; a cool rim catches the slab edges
    studio_rig = [
        ap.spot_light("studio_key", L, (-3.4, -2.0, 3.6), (0.15, 0, 1.05), 7000, 48, 0.7, 0.12,
                      (1.0, 0.95, 0.88)),
        ap.area_light("studio_rim", L, (3.0, -0.6, 2.8), (0, -0.35, 1.2), 1.5, 500, (0.85, 0.92, 1.0)),
        ap.area_light("studio_fill", L, (0.5, -5.5, 1.4), c, 5.0, 120),
    ]
    lights = print_rig + studio_rig

    shots = {
        "front": (ap.camera("cam_front", C, (0, -8, c.z), c, ortho_scale=poster.H * ap.PX), print_rig),
        "three_quarter": (ap.camera("cam_three_quarter", C, (-2.4, -3.3, 1.4), (0.12, -0.25, 1.18), lens=52,
                                    dof=((-0.1, -0.35, 1.3), 5.6)), studio_rig),
        "side": (ap.camera("cam_side", C, (2.6, -2.2, 0.95), (-0.08, -0.3, 1.25), lens=40), studio_rig),
        "detail": (ap.camera("cam_detail", C, (-1.05, -2.5, 1.95), (-0.06, -0.45, 1.36), lens=90,
                             dof=((-0.06, -0.47, 1.36), 2.8)), studio_rig),
    }
    scene.camera = shots["three_quarter"][0]
    return scene, shots, (print_rig, studio_rig)


def smooth(a, b, t):
    t = min(max((t - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def reveal(scene, rigs, size, samples, exposure, tag="", hold_in=14, move=84, hold_out=22):
    """Dolly-zoom out of the flat poster into the sculpture.

    Starts on a 400 mm lens from far away (perspective flattened, the slabs
    line up into the printed poster under the "print" sun), then swings left
    while the lens widens to 50 mm and the light crossfades to the studio spot.
    Every frame is keyed, so the move can be scrubbed in the .blend.
    """
    print_rig, studio_rig = rigs
    start, end = ap.poster_center(poster), Vector((0.1, -0.25, 1.18))
    data = bpy.data.cameras.new("cam_reveal")
    data.clip_end = 200
    cam = bpy.data.objects.new("cam_reveal", data)
    bpy.data.collections["Cameras"].objects.link(cam)
    base = {l: l.data.energy for l in print_rig + studio_rig}
    acrylics = [m for m in bpy.data.materials if "ink_srgb" in m]
    frames = hold_in + move + hold_out
    for f in range(frames):
        t = smooth(hold_in, hold_in + move, f)
        lens = math.exp(math.log(400) + (math.log(50) - math.log(400)) * t)
        az, el = math.radians(-38) * t, math.radians(7) * t
        target = start.lerp(end, t)
        dist = lens / 36 * 2.3  # keep the poster's height in frame
        cam.location = target + dist * Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el),
                                               math.sin(el)))
        ap.look_at(cam, target)
        data.lens = lens
        light = smooth(0.12, 0.65, t)
        for l, e in base.items():
            l.data.energy = e * ((1 - light) if l in print_rig else light)
            l.data.keyframe_insert("energy", frame=f + 1)
        for m in acrylics:
            ap.set_tint(m, 1 / 3 + (0.8 - 1 / 3) * light)
            for node, sock in (("glass", "Base Color"), ("shadow", "Color")):
                m.node_tree.nodes[node].inputs[sock].keyframe_insert("default_value", frame=f + 1)
        scene.view_settings.exposure = exposure * light
        scene.view_settings.keyframe_insert("exposure", frame=f + 1)
        cam.keyframe_insert("location", frame=f + 1)
        cam.keyframe_insert("rotation_euler", frame=f + 1)
        data.keyframe_insert("lens", frame=f + 1)
    for l in print_rig + studio_rig:
        l.hide_render = l.hide_viewport = False
    scene.camera = cam
    scene.frame_start, scene.frame_end = 1, frames
    scene.render.fps = 24
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.cycles.samples = samples
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.image_settings.file_format = "PNG"
    out = os.path.join(HERE, "build", "reveal" + tag)
    scene.render.filepath = os.path.join(out, "f_####")
    bpy.ops.render.render(animation=True)
    # forward then backward, so the loop breathes in and out
    seq = os.path.join(out, "f_%04d.png")
    mp4 = os.path.join(HERE, "build", "renders", f"reveal{tag}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", seq, "-filter_complex",
                    "[0]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", mp4], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf",
                    "fps=15,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=200[p];[b][p]paletteuse",
                    mp4.replace(".mp4", ".gif")], check=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--shots", default="front,three_quarter,side,detail")
    ap_.add_argument("--scale", type=float, default=1.0)
    ap_.add_argument("--samples", type=int, default=256)
    ap_.add_argument("--no-render", action="store_true")
    ap_.add_argument("--reveal", action="store_true", help="also render the reveal animation")
    ap_.add_argument("--exposure", type=float, default=-0.7, help="stops, studio shots only")
    ap_.add_argument("--variant", help="named take from poster.VARIANTS, e.g. mixed")
    args = ap_.parse_args(argv)

    scene, shots, rigs = setup(args.variant)
    tag = f"-{args.variant}" if args.variant else ""
    lights = rigs[0] + rigs[1]
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", f"olivetti-a{tag}.blend"), compress=True)
    if args.no_render:
        return
    size = (round(FULL[0] * args.scale), round(FULL[1] * args.scale))
    for name in filter(None, args.shots.replace("none", "").split(",")):
        cam, rig = shots[name]
        ap.render(scene, cam, os.path.join(HERE, "build", "renders", f"{name}{tag}.png"),
                  size, args.samples, rig, lights,
                  *(("Standard", 1 / 3) if name == "front" else ("Standard", 0.8, args.exposure)))
    if args.reveal:
        reveal(scene, rigs, (round(720 * args.scale) // 2 * 2, round(912 * args.scale) // 2 * 2),
               args.samples, args.exposure, tag)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", f"olivetti-a{tag}.blend"), compress=True)


if __name__ == "__main__":
    main()
