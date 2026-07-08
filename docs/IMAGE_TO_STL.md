# Image → 3D → Printable STL

Turn a single photo (or a few views) of an object into a **watertight, manifold,
print-ready STL**, running **entirely locally** — no cloud, no API fees, no data
leaving your machine.

This supersedes the original depth-map → OpenSCAD approach (which could only make
2.5D reliefs). It uses a modern image-to-3D model (**Hunyuan3D-2.1**) whose mesh
comes out of a signed-distance field + marching cubes, so the topology is clean.

```
image(s) ──▶ Hunyuan3D-2.1 (shape only)  ──▶ gentle watertight finish ──▶ STL
              single OR multi-view (2mv)        (scripts/finish_print.py)
```

- **Single image** → fast, good for solid objects; softens fine surface detail.
- **Multi-view** (front / back / left / right) → much higher fidelity; recovers
  detail single-view has to guess. Fidelity is bounded by what your views *show* —
  a feature only reconstructs if some input view contains it.

---

## 1. Prerequisites (the "ideal setup")

| Need | Ideal | Minimum / notes |
|------|-------|-----------------|
| **GPU** | Apple Silicon (M-series, MPS) **or** NVIDIA CUDA GPU | CPU works but is very slow |
| **Unified RAM / VRAM** | 16 GB+ | the shape model peaks ~10 GB |
| **Disk** | ~20 GB free | model weights (~7 GB) + clone + outputs |
| **Python** | 3.11 | 3.10–3.12 likely fine |
| **git**, **curl/wget** | — | to clone the fork + fetch weights |
| **Blender** (optional) | 4.x / 5.x on PATH | only for `--render` QA images |
| **HuggingFace account** | not required | Hunyuan3D weights are **not gated** |

This repo's pipeline code is platform-agnostic. The only platform-specific part is
**installing PyTorch** (MPS build on macOS, CUDA build on Linux/Windows). The agent
instructions below branch on that.

> **Why a third-party clone?** The model code + weights (the `Hunyuan3D-2.1-mac`
> fork, ~7 GB) are too large to vendor and aren't ours to redistribute. We commit
> *our* orchestration/finishing code + a small compatibility shim, and you fetch
> the model side once via the steps below.

---

## 2. Setup — instructions an agent (or you) can follow

> Goal: end with a working `./Hunyuan3D-2.1-mac` clone + its `.venv`, so
> `image_to_stl.py` runs. Adapt commands to the OS; the logic is the same.

### Step 1 — Clone the model fork into the repo root
The fork adds Apple-Silicon/CPU fallbacks to Tencent's Hunyuan3D-2.1.
```bash
cd <this-repo>
git clone --depth 1 https://github.com/Brainkeys/Hunyuan3D-2.1-mac.git
```
(It's git-ignored. If you put it elsewhere, set `HUNYUAN_DIR=/path/to/clone`.)

### Step 2 — Create a Python 3.11 venv for it
```bash
python3.11 -m venv Hunyuan3D-2.1-mac/.venv
source Hunyuan3D-2.1-mac/.venv/bin/activate    # Windows: Hunyuan3D-2.1-mac\.venv\Scripts\activate
pip install --upgrade pip
```

### Step 3 — Install PyTorch for your platform
- **Apple Silicon (MPS):** `pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1`
- **NVIDIA CUDA (Linux/Win):** install the matching CUDA wheels from https://pytorch.org
  (e.g. `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124`).
- **CPU only:** the default `pip install torch torchvision torchaudio` (slow).

### Step 4 — Install the shape-pipeline dependencies
```bash
pip install -r requirements-shape.txt        # at this repo's root
pip install pymeshlab                         # arm64/x86 wheels exist; the fork's pinned version may not
```
`finish_print.py`'s default `gentle` method only needs `trimesh`/`numpy` (already
pulled in). `--method poisson`/`voxel`/`meshfix` additionally need
`open3d` / `scikit-image` / `pymeshfix` — install if you want those.

### Step 5 — Done — verify
```bash
HUNYUAN_DIR=Hunyuan3D-2.1-mac ./Hunyuan3D-2.1-mac/.venv/bin/python image_to_stl.py --help
```
The `hy3dgen` compatibility shim needed by the multi-view model is already vendored
in `hunyuan_compat/` and added to the path automatically — no action needed.

### Platform notes / gotchas
- **Apple Silicon:** run with `PYTORCH_ENABLE_MPS_FALLBACK=1` (the script sets this).
  A few ops fall back to CPU; expect ~14–20 min/generation at `--octree 384`.
- **First run downloads ~7 GB** of weights to `~/.cache/hy3dgen` (one time).
- Don't run two generations at once on one GPU — they time-slice and both slow down.
- The model's `mc_algo` is `mc` (scikit-image, CPU) — works everywhere; do **not**
  switch to `dmc` (needs CUDA).

---

## 3. Usage

Run with the fork's venv python. `OUT` is a basename; it writes `OUT.stl`.

```bash
PY=./Hunyuan3D-2.1-mac/.venv/bin/python

# Single image
$PY image_to_stl.py photo.png -o out/thing --size-mm 120 --render

# Multi-view from ONE composite sheet (auto-splits + keys out background)
$PY image_to_stl.py --sheet sheet.png --layout 2x2 \
    --order front back left right -o out/thing --size-mm 120 --render

# Multi-view from explicit per-view files
$PY image_to_stl.py --front f.png --back b.png --left l.png --right r.png \
    -o out/thing --render
```

### Key flags
| Flag | Default | Meaning |
|------|---------|---------|
| `--size-mm` | 100 | scale longest axis to this many mm |
| `--octree` | 384 | detail resolution; 512 = sharper edges, ~2× slower |
| `--steps` | 50 | diffusion steps |
| `--sheet` + `--layout` + `--order` | — | one composite image; grid e.g. `2x2`/`1x4`; view names in reading order |
| `--render` | off | also write Blender QA views next to the STL |
| `--dtype` | fp16 | `fp32` if you hit fp16 instability |
| `--base-cut` | none | slice a flat print base off one face (`auto`/`z-`/`z+`/…); also trims tendrils below it |
| `--base-cut-mm` | 1.0 | how much to slice off the base-cut face, in mm |

### Flat base for printing (`--base-cut`)
Feed-forward 3D models output a closed solid; for a relief/nameplate the back
isn't perfectly flat, so it won't sit cleanly on the bed and can have thin
tendril artifacts hanging off the base. `--base-cut auto --base-cut-mm 1.5`
slices a thin sliver off the flat "back" face and caps it — giving a flat print
seat and removing those tendrils in one step. Use an explicit face (`z-`, `y-`,
…) if `auto` picks the wrong side (verify in the `--render` output).
*Note:* this won't separate the letters into individual pieces with open gaps —
that's CAD/parametric modeling, not image-to-3D reconstruction.

### Getting good multi-view inputs
- Provide **canonical, head-on angles**: true front, back, left profile, right profile
  (not dramatic 3/4 shots).
- **Same scale/centering** in every view; **transparent or plain background**
  (transparent PNG is best — it preserves detached parts like a logo floating above text).
- Every important feature must be **visible in at least one view** (e.g. a top-face
  detail needs a top-ish view).

---

## 4. What's in this repo vs. fetched

| Committed here (ours) | Fetched via setup (third-party / large) |
|---|---|
| `image_to_stl.py` — unified CLI | `Hunyuan3D-2.1-mac/` clone (git-ignored) |
| `scripts/finish_print.py` — repair → watertight STL | its `.venv` and model weights |
| `scripts/split_views.py` — composite → per-view | `~/.cache/hy3dgen` weights |
| `scripts/render_views.py` — Blender QA renders | |
| `hunyuan_compat/` — `hy3dgen` shim for the 2mv model | |
| `requirements-shape.txt` | |

## 5. Finishing methods (settled 2026-07: Blender is the repair backend)
- **Clean SDF meshes (Hunyuan, the default path):** `scripts/finish_print.py --method gentle`
  — only removes the few faces causing non-manifold edges, fills tiny holes, preserves
  all detail. Used automatically by `image_to_stl.py`. Nothing heavier is needed here.
- **Broken-but-detailed meshes (e.g. raw TRELLIS output):** `scripts/blender_finish.py`
  — headless Blender OpenVDB voxel remesh:
  ```bash
  blender --background --python scripts/blender_finish.py -- \
      broken.obj fixed.stl --res 384 --target-mm 120
  ```
  Reconstructs a watertight manifold from a signed-distance field at fine resolution,
  preserving the pockets and thin walls that trimesh-based repairs flood-fill shut.
  Validated on a TRELLIS mug holder: 60K boundary + 44K non-manifold edges → 72/0,
  detail intact — where every trimesh path (`poisson`/`voxel`/`meshfix`) melted it
  into a blob. Those trimesh methods still exist inside `finish_print.py` but are
  deprecated for repair; do not reach for them before `blender_finish.py`.
