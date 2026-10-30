"""Printed-paper texture: warm stock, faint grain, and the poster's type."""

import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FONT_DIRS = ["/usr/share/fonts", "/Library/Fonts", "/System/Library/Fonts",
             os.path.expanduser("~/Library/Fonts"), "C:/Windows/Fonts"]


def find_font(*names):
    """First font found, in order of preference."""
    for n in names:
        for base in FONT_DIRS:
            for root, _, files in os.walk(base):
                if n in files:
                    return os.path.join(root, n)
    return None


def _ink(c):
    return tuple(int(v * 255) for v in c)


def make(poster, path, scale=2, seed=7):
    w, h = poster.W * scale, poster.H * scale
    img = Image.new("RGB", (w, h), _ink(poster.PAPER))

    # grain: soft gaussian noise multiplied in, plus a few long fibres
    noise = Image.effect_noise((w // 2, h // 2), 18).resize((w, h)).filter(ImageFilter.GaussianBlur(0.8))
    noise = Image.merge("RGB", [noise.point(lambda v: 250 + (v - 128) * 0.12)] * 3)
    img = ImageChops.multiply(img, noise)
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(900):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        dx, dy = rnd.uniform(-30, 30), rnd.uniform(-30, 30)
        d.line([(x, y), (x + dx, y + dy)], fill=(120, 100, 80, 10), width=1)

    ink = _ink(poster.INKS[poster.LOGO["ink"]]) + (255,)
    logo = poster.LOGO
    logo_font = find_font("Inter-Black.otf", "InterDisplay-Black.otf", "Arial Black.ttf", "DejaVuSans-Bold.ttf")
    if logo_font:
        # set the wordmark, then stretch it to the poster's wide proportions
        f = ImageFont.truetype(logo_font, logo["size"] * scale)
        l, t, r, b = f.getbbox(logo["text"], anchor="ls")
        mark = Image.new("L", (r - l, b - t), 0)
        ImageDraw.Draw(mark).text((-l, -t), logo["text"], font=f, fill=255, anchor="ls")
        mark = mark.resize((round(logo["width"] * scale), mark.height), Image.LANCZOS)
        img.paste(Image.new("RGB", mark.size, ink[:3]),
                  (logo["x"] * scale, logo["baseline"] * scale + t), mark)

    body = poster.BODY
    body_font = find_font("c0583bt_.pfb", "CourierPrime-Bold.ttf", "Courier New Bold.ttf",
                          "LiberationMono-Bold.ttf", "DejaVuSansMono-Bold.ttf")
    if body_font:
        f = ImageFont.truetype(body_font, round(body["size"] * scale))
        for i, line in enumerate(body["lines"]):
            y = (body["first_baseline"] + i * body["leading"]) * scale
            d.text((body["x"] * scale, y), line, font=f, fill=ink, anchor="ls")

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)
    return path
