"""Split one composite multi-view image into per-view images for the
multi-view 3D pipeline.

Two modes:
  --grid RxC     Even crop into a tidy R-by-C grid (most reliable for clean sheets).
  (default)      Auto-detect: find the separate subjects on a uniform/transparent
                 background and crop each with padding. Handles irregular spacing.

Panels are ordered reading-order (top->bottom rows, left->right within a row) and
mapped to --order names (default: front left right back).

Usage:
    python split_views.py sheet.png --out-dir nike_views --order front left right back
    python split_views.py sheet.png --out-dir nike_views --grid 2x2
"""
import argparse
import os
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def _foreground_mask(arr, thresh=90):
    """Boolean foreground mask. Uses alpha if present, else segments from the
    background colour sampled at the image corners. The threshold is set high
    enough to reject soft contact shadows (light grey ~ background) while keeping
    a saturated subject — shadows left in create flared bases / tendril artifacts
    in the 3D reconstruction."""
    if arr.shape[2] == 4 and arr[:, :, 3].min() < 250:
        return arr[:, :, 3] > 30
    rgb = arr[:, :, :3].astype(int)
    h, w = rgb.shape[:2]
    corners = np.stack([rgb[0, 0], rgb[0, w - 1], rgb[h - 1, 0], rgb[h - 1, w - 1]])
    bg = np.median(corners, axis=0)
    dist = np.abs(rgb - bg).sum(axis=2)
    return dist > thresh


def _order_boxes(boxes):
    """Sort (y0,x0,y1,x1) boxes into reading order, clustering rows by y-overlap."""
    boxes = sorted(boxes, key=lambda b: b[0])
    rows, cur = [], [boxes[0]]
    for b in boxes[1:]:
        cy_prev = (cur[-1][0] + cur[-1][2]) / 2
        if b[0] <= cy_prev <= b[2] or abs(b[0] - cur[-1][0]) < (cur[-1][2] - cur[-1][0]) * 0.5:
            cur.append(b)
        else:
            rows.append(cur); cur = [b]
    rows.append(cur)
    out = []
    for row in rows:
        out.extend(sorted(row, key=lambda b: b[1]))
    return out


def split_auto(im, pad_frac=0.06):
    arr = np.array(im)
    fg = _foreground_mask(arr)
    fg = ndimage.binary_closing(fg, iterations=3)
    lbl, n = ndimage.label(fg)
    if n == 0:
        raise SystemExit("No foreground detected — try --grid mode.")
    sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * 0.10]
    slices = ndimage.find_objects(lbl)
    boxes = []
    for i in keep:
        ys, xs = slices[i - 1]
        boxes.append((ys.start, xs.start, ys.stop, xs.stop))
    boxes = _order_boxes(boxes)
    crops = []
    H, W = arr.shape[:2]
    for (y0, x0, y1, x1) in boxes:
        py, px = int((y1 - y0) * pad_frac), int((x1 - x0) * pad_frac)
        crops.append(im.crop((max(0, x0 - px), max(0, y0 - py),
                              min(W, x1 + px), min(H, y1 + py))))
    return crops


def split_grid(im, rows, cols):
    W, H = im.size
    cw, ch = W // cols, H // rows
    return [im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
            for r in range(rows) for c in range(cols)]


def keyout_background(im):
    """Return an RGBA copy with the uniform background made transparent.
    Keeps ALL non-background pixels (e.g. a detached swoosh), unlike a
    salient-object remover. Uses the existing alpha if the image already has one."""
    arr = np.array(im)
    if arr.shape[2] == 4 and arr[:, :, 3].min() < 250:
        return im  # already has a usable alpha mask
    mask = _foreground_mask(arr)
    mask = ndimage.binary_opening(mask, iterations=2)   # drop thin shadow skirts
    mask = ndimage.binary_closing(mask, iterations=2)
    mask = ndimage.binary_fill_holes(mask)
    out = arr.copy()
    if out.shape[2] == 3:
        out = np.dstack([out, np.full(out.shape[:2], 255, np.uint8)])
    out[:, :, 3] = (mask * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--order", nargs="+", default=["front", "left", "right", "back"],
                    help="view names in reading order (default: front left right back)")
    ap.add_argument("--grid", help="even crop, e.g. 2x2 or 1x4 (skips auto-detect)")
    ap.add_argument("--keep-bg", action="store_true",
                    help="keep the background (default: key uniform bg to transparent)")
    args = ap.parse_args()

    im = Image.open(args.image).convert("RGBA")
    if not args.keep_bg:
        im = keyout_background(im)
    if args.grid:
        r, c = (int(x) for x in args.grid.lower().split("x"))
        crops = split_grid(im, r, c)
    else:
        crops = split_auto(im)

    print(f"Found {len(crops)} panels; mapping to {args.order[:len(crops)]}")
    if len(crops) != len(args.order):
        print(f"  WARNING: {len(crops)} panels but {len(args.order)} names — "
              f"check the sheet / --order / try --grid.")

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    for crop, name in zip(crops, args.order):
        p = out / f"{name}.png"
        crop.save(p)
        print(f"  {name}: {crop.size}  -> {p}")


if __name__ == "__main__":
    main()
