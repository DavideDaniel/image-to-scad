---
name: print-fit
description: Rescale a component-plan model to fit a printer bed and calibrate assembly fit after test prints — without breaking joints. Use when a model or its parts don't fit the user's bed ("too big for my printer", "scale this down"), when the user reports how printed parts actually fit ("too tight", "won't seat", "wobbly", "spins loose"), or before slicing for a specific printer. Never let parts be scaled in the slicer when the model has an assembly — joint clearances are absolute tolerances and uniform scaling silently breaks the fit; this skill rescales the plan instead and re-reviews design rules.
---

# Print fit: bed scaling + assembly-fit calibration

Two jobs, one principle: **geometry scales, tolerances don't.** A 0.3 mm joint
clearance is a property of the printer, not of the model — so any resize must go
through the plan (where clearance is a separate number), never through uniform STL
scaling in a slicer.

## Job 1 — fit a model to a bed

1. Get the bed size (X Y Z, mm). If unknown, ask — common: 220² (Ender), 256²
   (Bambu X1/P1), 300²+ (large format). Also ask if any dimension is functional
   (e.g. "wells must stay ≥ mug diameter") — those pin the minimum scale.
2. Scale the plan, not the STL:
   ```bash
   venv/bin/python scripts/scale_plan.py plan.json plan_scaled.json --fit-bed 220 220 250
   ```
   It scales all component/cut/joint geometry, keeps every joint `clearance`
   untouched, floors the bevel at 0.4 mm, records the factor in
   `scaling_history`, and prints REVIEW flags (e.g. pegs falling under 2.5 mm
   radius).
3. **Refine — this is the reasoning step, do not skip it.** Scaling is uniform;
   design rules are absolute. Review the scaled plan and fix by editing numbers:
   - Pegs < 2.5 mm radius → fatten them (and their sockets stay matched
     automatically since the socket derives from the same cylinder + clearance);
     check ≥3 mm wall remains around each socket.
   - Thin features: walls/posts should stay ≥ 2 perimeters (~1.6 mm, prefer ≥3 mm);
     shallow features (well recesses, lips) that dropped under ~1 mm are no longer
     doing their job — restore them toward their original absolute size.
   - Functional dimensions the user named (cup wells, phone slots, shelf clearance)
     must be re-pinned to their real-world requirement, not the scaled value.
4. Rebuild with `--parts-dir`, re-run
   `venv/bin/python scripts/check_printability.py part_*.stl --bed-mm <bed>` on
   every part, and read the renders (per-part + `assembled_*`) before handing over
   STLs.

## Job 2 — calibrate fit from a test print

When the user reports how printed parts mate, adjust the plan's joint
`clearance` (per side), rebuild only the affected parts, and record the result:

| Report | Action |
|---|---|
| won't seat / needs hammering | clearance +0.10 mm |
| seats with firm push (press fit wanted) | keep |
| firm push but slip fit wanted | clearance +0.05 mm |
| slides but rattles / spins | clearance −0.05 to −0.10 mm |

- Adjust in ±0.05 steps; one variable at a time. First-layer squish ("elephant
  foot") often causes tightness only at the socket mouth — a small chamfer on the
  socket opening (or slicer elephant-foot compensation) beats growing the whole
  clearance.
- **Adjust the cheap side.** When a fit fails after parts are printed, fix it by
  resizing the small/fast part (pin, stud, dowel — minutes and grams) to match the
  as-printed socket, NOT by reprinting the large socketed part. Shrinking a male
  thread's major radius by X adds X of effective radial clearance against an
  existing female. Two exceptions: (1) a *blocked* tapped mouth (ungrooved ring)
  can't be fixed by a smaller thread — small enough to pass the ring means zero
  ridge engagement; either ream the mouth ring out (it's usually <1 mm of plastic,
  a drill bit does it) or switch that end of the pin to a smooth glue-in; (2) if
  the female is physically damaged. Author rescue pins against the AS-PRINTED
  female dimensions (the plan version that was actually printed, not the fixed one).
- **Record calibrated values** in the "Calibrated fits" table below (edit this
  file) so future models start from the right number for that printer + material.

## Calibrated fits (learned per printer/material)

| Printer | Material | Slip fit | Press fit | Notes |
|---|---|---|---|---|
| generic FDM (first-pass defaults, 2026-07-11) | any | 0.35 smooth bore | 0.2 | thread radial clearance: 0.35 vertical tapped bore, 0.45 horizontal tapped bore (sag); refine per printer after test prints |

## Rules of thumb

- Default clearance 0.3 mm/side (slip), 0.15–0.2 (press) for FDM pegs; resin ~0.1.
- Never scale up past factor 1.0 to "fill the bed" without re-checking wall/peg
  maximums against print time; scaling up is rarely wrong dimensionally but wastes
  material.
- After ANY scale change, joints were scaled too — re-check root depth ≥3 mm into
  the male part and ≥5 mm engagement into the female (they scaled with geometry
  and may now be too shallow; deepen by editing the joint cylinder).
- The plan is the source of truth: slicer scaling is only acceptable for
  single-piece models with no assembly, no threads, and no mating features.
