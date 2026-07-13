# Tall stack shelf — part versions

`parts/` always mirrors the newest build. Once anything is printed, use the
frozen folders below and match pins to the generation of each printed part.

## parts_v2_asprinted/  (screw design, commit 4fa9b91 — what was printed 2026-07-10)
- deck stud sockets: 0.25 clearance, **blocked mouth** (ungrooved ring — the
  original studs cannot start; ream ~0.55 mm with a 10.5 mm bit, or use rescue studs)
- leg foot taps 0.30, leg stud bores 0.30
- mate with: `../rescue/parts/` pins (no reaming), or reamed mouths + standard studs

## parts_v3_fixed/  (commit 82af428)
- deck taps: open mouth, 0.35; leg foot taps 0.45; leg stud bores 0.35
- mate with: the standard pins (`part_leg_stud_x4`, `part_foot_screw_x4`,
  `part_deck_dowel_x2`)

## Identical across v2 and v3 (safe to mix generations)
- all pins: leg studs, foot screws, deck dowels — byte-for-byte unchanged
- deck↔deck midline dowel bores, stacking pads/receiver pockets, side clip sockets
- so a v2 deck half mates a v3 deck half; any leg fits any deck (via matching pins)

## Rule per physical part
Look at WHEN a socketed part was printed:
- printed before 2026-07-11 (v2) → rescue pins for its sockets
- printed from parts_v3_fixed → standard pins
