# Card 3D Viewer

Interactive 3D layered card viewer.

A single-file web app that stacks 4 SVG layers along the Z axis and lets you rotate the card in 3D space, tweak spacing / scale / FOV in real time, and export high-resolution snapshots.

**Live preview:** https://ricardommatos.github.io/card-3d-viewer/

## Controls

- **Drag** — rotate the card
- **Wheel** — zoom (dolly in/out)
- **1 / 2 / 3 / 4** — front / iso / side / top rotation presets
- **Space** — toggle auto-rotate
- **R** — reset
- **E** — export PNG at 2×

## Stack

- `three@0.162` via ES Modules CDN
- JetBrains Mono for UI typography
- Zero build step — open `index.html` directly or via any static server
