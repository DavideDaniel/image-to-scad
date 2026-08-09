# image-to-stl — Android companion (`android-app/`)

Native Android app: load a `component-plan/v0` (the same JSON format
`scripts/blender_build_components.py` builds), show its dimensions as
sliders, live-preview the resulting 3D model, and export/share a binary STL —
entirely on-device, no network calls.

## Why it's structured this way

Blender isn't available on Android, so the geometry can't reuse
`scripts/blender_build_components.py`. Since `component-plan/v0` only ever
describes axis-aligned boxes and cylinders (union, then subtract — see
ADR-002 in the root `CLAUDE.md`), that CSG is cheap enough to do directly on
the phone with a small BSP-tree boolean engine, so the whole pipeline runs
locally with no server round-trip.

```
android-app/
├── core/   pure-Kotlin/JVM module: plan parsing, CSG engine, STL writer. No Android dependency.
└── app/    Android app: Jetpack Compose UI, OpenGL ES preview, STL export/share.
```

## What's verified, what isn't

**`:core` is unit-tested and the tests pass**, including against two of this
repo's real plans (`outputs/circular_shelf_poc/plan.json` and
`outputs/component_mug_shelf_stackable_poc/stand_plan.json`, copied into
`core/src/test/resources/`): box/cylinder winding, union, subtract (with a
through-hole cutter, the case ADR-001 flags as the sharp edge for boolean
ops), live dimension edits, and STL round-tripping. All of that ran in this
session with plain Gradle + Maven Central — see `core/src/test/kotlin/`.

**`:app` (the Compose UI, GL renderer, STL export/share) has not been
compiled or run.** This sandbox's egress policy blocks `dl.google.com`, which
is where the Android Gradle Plugin, `android.jar`, and the AndroidX/Compose
artifacts all live — there's no way to build or emulate an Android app here.
The code was written carefully against known-stable APIs, but treat it as
**unverified** until you've opened it in Android Studio. First things to
check: does it build, does the sample plan render, do the sliders resize the
model live, does STL export/share work.

## Getting an APK without a computer

`.github/workflows/android-build.yml` builds `:app` on GitHub's own runners
(which have normal internet access, unlike this sandbox) and uploads the
debug APK as a build artifact. From a phone:

1. Open the repo on GitHub → **Actions** tab → **Android build** workflow.
2. If it hasn't run yet, trigger it manually (the "Run workflow" button —
   `workflow_dispatch`), or push any change under `android-app/`.
3. Open the latest run. A green check means it *compiled* — that alone
   answers "does it build". Under **Artifacts**, download
   `image-to-stl-debug-apk`.
4. It downloads as a `.zip` containing the `.apk`; extract it (most phone
   file managers can), then open the `.apk` to install. Android will ask you
   to allow installs from this source the first time.
5. If the build goes red instead, the job log says exactly which Gradle task
   and line failed — that's the next thing to fix, not a dead end.

## Building it

1. Open `android-app/` in Android Studio (Gradle sync needs normal internet
   access — nothing about this project is unusual, it's a standard two-module
   Gradle/AGP project).
2. Run the `app` configuration on a device or emulator (minSdk 26).
3. Or from a terminal with the Android SDK installed:
   ```bash
   ./gradlew :core:test              # geometry engine unit tests
   ./gradlew :app:assembleDebug      # build the APK
   ```

## What it does today

- Loads the bundled sample plan (`app/src/main/assets/sample_plans/circular_shelf_plan.json`,
  the same file as `outputs/circular_shelf_poc/plan.json`).
- Lists every box/cylinder dimension in the plan as a labeled slider
  (range: 0.4x–2.5x the original value).
- Rebuilds the mesh off the main thread on every change and redraws it in a
  touch-orbit OpenGL ES preview.
- Exports a binary STL to app storage and opens the Android share sheet.

## What it deliberately doesn't do yet

- **No photo import / measurement capture.** Per the earlier discussion this
  replaces: automatic photogrammetry from a phone photo (no depth sensor)
  isn't reliable enough to build blind. The next step is a capture screen
  where the user anchors one real dimension by hand (mirroring
  `measure_views.py --width-mm`), with ARCore depth used opportunistically on
  supported hardware. Not started — adding it now would be building UI this
  session can't verify on top of a measurement approach that's still a guess.
- **No arbitrary plan import (file picker / share-into).** Only the bundled
  sample loads today.
- **No bevels.** `model.bevel` in the plan JSON is ignored — sharp edges
  only. Blender's bevel modifier isn't something this BSP engine reproduces;
  low priority since it's cosmetic.

## Performance note

T-junction stitching in `core/mesh/Mesh.kt` (needed so a through-cut doesn't
leave cracks in the mesh — see the doc comment there) is brute-force
O(vertices²) per rebuild. Fine at the scale of the two worked-example plans
in this repo (a few hundred to low thousands of vertices); if a much larger
plan makes live slider dragging feel laggy, that function is the first place
to optimize (e.g. bucket points by a spatial hash before the pairwise scan).
