#!/usr/bin/env python
"""image-to-stl: turn an image (or multiple views) into a watertight, print-ready
STL, fully locally, using Hunyuan3D-2.1 (shape only) on Apple Silicon.

Modes
-----
Single image:
    image_to_stl.py photo.png --output thing

Multi-view from one composite sheet (auto-split + background keyed out):
    image_to_stl.py --sheet grid.png --layout 2x2 --order front back left right --output thing

Multi-view from explicit view files:
    image_to_stl.py --front f.png --back b.png --left l.png --right r.png --output thing

Pipeline: generate (Hunyuan single or 2mv multi-view) -> gentle watertight finish
-> scale to --size-mm -> STL. Add --render for Blender QA images.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Location of the third-party Hunyuan3D-2.1 fork (cloned per docs/IMAGE_TO_STL.md).
# Override with HUNYUAN_DIR if you cloned it elsewhere.
HUNYUAN = Path(os.environ.get("HUNYUAN_DIR", HERE / "Hunyuan3D-2.1-mac"))
if not (HUNYUAN / "hy3dshape").is_dir():
    sys.exit(f"Hunyuan fork not found at {HUNYUAN}. See docs/IMAGE_TO_STL.md "
             f"(clone it there, or set HUNYUAN_DIR).")
sys.path.insert(0, str(HUNYUAN / "hy3dshape"))   # third-party hy3dshape package
sys.path.insert(0, str(HERE / "hunyuan_compat"))  # our hy3dgen compat shim (for 2mv)
sys.path.insert(0, str(HERE / "scripts"))         # finish_print, split_views
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402

from split_views import keyout_background, split_grid  # noqa: E402
from finish_print import finish  # noqa: E402

VIEW_NAMES = ("front", "back", "left", "right")
_REMBG = None


def _subject(img, no_rembg):
    """RGBA subject: keep an existing alpha mask, else remove background."""
    img = img.convert("RGBA")
    a = np.array(img)[:, :, 3]
    if (a.min() < 250 and (a > 10).mean() < 0.98) or no_rembg:
        return img
    global _REMBG
    if _REMBG is None:
        from hy3dshape.rembg import BackgroundRemover
        _REMBG = BackgroundRemover()
    return _REMBG(img.convert("RGB"))


def _views_from_sheet(sheet_path, layout, order, keep_bg):
    im = Image.open(sheet_path).convert("RGBA")
    if not keep_bg:
        im = keyout_background(im)  # white/uniform bg -> transparent, keeps detached parts
    rows, cols = (int(x) for x in layout.lower().split("x"))
    crops = split_grid(im, rows, cols)
    if len(crops) != len(order):
        print(f"  WARNING: sheet has {len(crops)} cells but order lists {len(order)}")
    return {name: crop for name, crop in zip(order, crops)}


def generate(views, single_image, octree, steps, dtype, no_rembg):
    """views: dict[name->PIL] for multi-view, or None. single_image: path or None."""
    from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline

    td = torch.float16 if dtype == "fp16" else torch.float32
    mv = views is not None
    t0 = time.time()
    if mv:
        print(f"Loading multi-view model (views={list(views)})...")
        pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            "tencent/Hunyuan3D-2mv", subfolder="hunyuan3d-dit-v2-mv", dtype=td)
        image = {k: _subject(v, no_rembg) for k, v in views.items()}
    else:
        print("Loading single-image model...")
        pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            "tencent/Hunyuan3D-2.1", dtype=td)
        image = _subject(Image.open(single_image), no_rembg)
    print(f"  loaded in {time.time()-t0:.0f}s; device={pipe.device}")

    t0 = time.time()
    print(f"Generating (octree={octree}, steps={steps})...")
    mesh = pipe(image=image, octree_resolution=octree, num_inference_steps=steps)[0]
    print(f"  generated in {time.time()-t0:.0f}s: "
          f"{len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")
    return mesh


def main():
    p = argparse.ArgumentParser(description="Image -> watertight print-ready STL (local, Hunyuan3D)")
    p.add_argument("image", nargs="?", help="single input image")
    p.add_argument("--sheet", help="one composite image containing multiple views")
    for v in VIEW_NAMES:
        p.add_argument(f"--{v}", help=f"explicit {v} view image (multi-view mode)")
    p.add_argument("--layout", default="2x2", help="[--sheet] grid, e.g. 2x2 or 1x4 (default 2x2)")
    p.add_argument("--order", nargs="+", default=list(VIEW_NAMES),
                   help="[--sheet] view names in reading order (default: front back left right)")
    p.add_argument("--output", "-o", required=True, help="output basename (writes <output>.stl)")
    p.add_argument("--size-mm", type=float, default=100.0, help="longest axis in mm (default 100)")
    p.add_argument("--octree", type=int, default=384, help="detail resolution (default 384)")
    p.add_argument("--steps", type=int, default=50, help="diffusion steps (default 50)")
    p.add_argument("--dtype", choices=["fp16", "fp32"], default="fp16")
    p.add_argument("--keep-bg", action="store_true", help="don't key out the sheet background")
    p.add_argument("--no-rembg", action="store_true", help="skip background removal on inputs")
    p.add_argument("--render", action="store_true", help="also render Blender QA views")
    args = p.parse_args()

    explicit = {v: getattr(args, v) for v in VIEW_NAMES if getattr(args, v)}
    if args.sheet:
        views = _views_from_sheet(args.sheet, args.layout, args.order, args.keep_bg)
    elif explicit:
        views = {k: Image.open(v) for k, v in explicit.items()}
    elif args.image:
        views = None
    else:
        p.error("provide a single image, --sheet, or explicit --front/--back/--left/--right")

    mesh = generate(views, args.image, args.octree, args.steps, args.dtype, args.no_rembg)

    out = Path(args.output)
    raw_obj = out.with_name(out.stem + "_raw.obj")
    out.parent.mkdir(parents=True, exist_ok=True) if out.parent != Path("") else None
    mesh.export(raw_obj)

    print("Finishing (gentle, watertight)...")
    finish(str(raw_obj), str(out.with_suffix(".stl")), args.size_mm,
           min_component_frac=0.02, method="gentle", res=400, close_iter=2)

    if args.render:
        rdir = out.with_name(out.stem + "_renders")
        print(f"Rendering QA views -> {rdir}")
        subprocess.run(["blender", "--background", "--python", str(HERE / "scripts/render_views.py"),
                        "--", str(out.with_suffix(".stl")), str(rdir), "1000"],
                       check=False, capture_output=True)
        print(f"  renders in {rdir}")

    print(f"\nDone -> {out.with_suffix('.stl')}")


if __name__ == "__main__":
    main()
