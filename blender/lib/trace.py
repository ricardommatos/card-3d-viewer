"""Trace a flat-colour poster straight from its pixels.

Every pixel is snapped to the nearest colour of a known palette, each colour
becomes a mask, and each connected region of a mask becomes a polygon with
holes (OpenCV contours). Regions keep their area, so a scene can decide how
far each one rises. Coordinates: image pixels, origin top-left, y down.
"""

import cv2
import numpy as np


def load_rgb(path):
    return cv2.cvtColor(cv2.imread(path, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)


def classify(img, palette):
    """Label map: index of the nearest palette colour (RGB 0-255) per pixel."""
    pal = np.array(palette, dtype=np.float32)
    d = ((img.astype(np.float32)[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
    labels = d.argmin(-1).astype(np.uint8)
    return cv2.medianBlur(labels, 5)  # anti-aliased edges snap to one side


def regions(labels, index, min_area=30, epsilon=0.7, scale=1.0):
    """Polygons for one palette colour: [(outer, [holes], area)], px * scale."""
    mask = (labels == index).astype(np.uint8) * 255
    if scale != 1.0:
        mask = cv2.resize(mask, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        mask = (mask > 127).astype(np.uint8) * 255
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None:
        return []
    out = []
    hierarchy = hierarchy[0]

    def poly(c):
        c = cv2.approxPolyDP(c, epsilon * scale, True)[:, 0, :].astype(float) / scale
        return [tuple(p) for p in c]

    for i, c in enumerate(contours):
        if hierarchy[i][3] != -1:  # a hole; collected with its parent
            continue
        area = cv2.contourArea(c) / scale / scale
        if area < min_area:
            continue
        holes = []
        child = hierarchy[i][2]
        while child != -1:
            if cv2.contourArea(contours[child]) / scale / scale >= min_area * 0.3:
                h = poly(contours[child])
                if len(h) >= 3:
                    holes.append(h)
            child = hierarchy[child][0]
        o = poly(c)
        if len(o) >= 3:
            out.append((o, holes, area))
    return out
