# Posters as acrylic sculptures (Blender)

Every ink layer of a flat poster becomes a slab of tinted acrylic floating at
its own depth in front of the printed paper.

- **Head-on** (orthographic camera, "print" light almost on the lens axis), the
  slabs line up into the original poster. Overlaps mix subtractively, the way
  overprinted ink does, and each slab's coloured shadow lands just beside it,
  like slightly off-register printing.
- **From any other angle** the composition opens up into depth. A raking
  studio spot throws long coloured shadows across the paper and the floor.

## Layout

```
blender/
  lib/
    shapes2d.py        tracing helpers: polygons with soft, hand-drawn corners
    acrylic_poster.py  scene builder: slabs, materials, studio, lights, cameras
    paper_texture.py   printed paper: grain + the poster's typography
  olivetti-a/
    poster.py          the poster as data: inks, shapes (px), depth per layer
    build.py           cameras, light rigs, shots, reveal animation
    renders/           finished stills and the reveal loop
```

To recreate another poster, copy `olivetti-a/`. Trace its ink layers in
`poster.py`, in pixels of the reference scan. Then move the cameras in
`build.py` to suit.

## Run

Use Blender 5.2, or the standalone module (`pip install bpy==5.2.3`):

```bash
cd blender/olivetti-a
python build.py --shots front --scale 0.3 --samples 24   # quick look
python build.py                                          # all stills, full size
python build.py --shots none --reveal --samples 48       # reveal animation (mp4 + gif)
```

Each run writes `build/olivetti-a.blend` (fully editable, texture packed),
`build/renders/*.png` and, with `--reveal`, `build/renders/reveal.mp4/.gif`.
`build/` is not committed; copy keepers into `renders/`.

## Knobs worth playing with

| Where | What |
| --- | --- |
| `poster.py` → `z`, `depth` | how far each layer floats, and how thick the slab is |
| `acrylic_material(frost=…)` | 0.015 is polished; 0.2+ is frosted, softer and more like paper |
| `render(tint=…)` | colour strength: 1/3 is exact head-on, higher is richer at an angle |
| `print_sun` direction | how far the shadows drift off-register in the front view |
| `studio_key` | the dramatic raking spot: position, cone, softness |
