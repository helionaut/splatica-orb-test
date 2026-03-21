# HEL-72 ASan Plus No-Static-Alignment Follow-up

Status: In Progress
Issue: HEL-72
Last Updated: 2026-03-21

## Goal

Take the unresolved post-initialization blocker from
[final-validation-report.md](final-validation-report.md), start from the
[HEL-57 monocular follow-up](hel-57-monocular-follow-up.md) diagnostic intent,
and isolate the next blocker before promoting any tuned monocular settings into
the canonical lens-10 manifest.

## Why This Pass Uses The Public Lane

This checkout cannot replay the private aggressive lens-10 baseline directly.

- `datasets/user/README.md` is present, but the imported
  `datasets/user/insta360_x3_one_lens_baseline/` bundle is not
- Host search found only raw `00.mp4` and `10.mp4`
- The calibration/extrinsics sidecars required to rebuild the private bundle
  were not present, so the missing prerequisite is the full private import
  contract, not only the video exports

That made the next auditable surrogate lane the public `mono_tum_vi`
reproducer that already shared the same first-map crash boundary from HEL-67,
HEL-68, and HEL-71.

## Experiment Contract

- Changed variable: combine `ORB_SLAM3_ENABLE_ASAN=1` with
  `ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1` on the public
  `mono_tum_vi` reproducer
- Hypothesis: the combined sanitizer plus no-static-alignment lane will turn
  the remaining first-map segfault into a symbolized runtime boundary or
  survive further than HEL-71
- Success criterion: the rerun leaves auditable HEL-72 artifacts and either
  produces a concrete AddressSanitizer stack trace or moves the crash beyond
  the old frame-93 first-map boundary
- Abort condition: the build fails before `mono_tum_vi` exists, or the rerun
  still crashes without symbolized evidence

## Repo Changes

- `scripts/run_clean_room_public_tum_vi_sanity.py` now forwards:
  - `ORB_SLAM3_BUILD_TYPE`
  - `ORB_SLAM3_ENABLE_ASAN`
  - `ORB_SLAM3_ASAN_COMPILE_FLAGS`
  into the build phase instead of forcing HEL-72 to use an out-of-band shell
  invocation
- `scripts/monitor_monocular_progress.py` plus
  `src/splatica_orb_test/monocular_runtime_progress.py` now tail the existing
  `HEL-68 diagnostic` runtime log and emit frame-based JSON or JSONL progress
  snapshots for long-running monocular replays that started before the
  phase-10 heartbeat fix landed
- Operator-script coverage now checks that forwarding behavior

## Command

```bash
env \
  ORB_SLAM3_ENABLE_ASAN=1 \
  ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1 \
  ORB_SLAM3_BUILD_PARALLELISM=1 \
  ORB_SLAM3_BUILD_TYPE=RelWithDebInfo \
  ORB_SLAM3_ASAN_COMPILE_FLAGS=' -fsanitize=address -fno-omit-frame-pointer -g -O0' \
  ORB_SLAM3_BUILD_EXPERIMENT='hel-72-asan-static-alignment-public-tum-vi' \
  ORB_SLAM3_BUILD_CHANGED_VARIABLE='combine AddressSanitizer with disabled Eigen static alignment on the public mono_tum_vi reproducer' \
  ORB_SLAM3_BUILD_HYPOTHESIS='the combined sanitizer plus no-static-alignment lane will turn the remaining first-map segfault into a symbolized runtime boundary or survive further than HEL-71' \
  ORB_SLAM3_BUILD_SUCCESS_CRITERION='mono_tum_vi builds and the public rerun leaves auditable HEL-72 artifacts with either a concrete ASan trace or a later runtime boundary' \
  ASAN_OPTIONS='detect_leaks=0:halt_on_error=1:abort_on_error=1:symbolize=1' \
  PYTHONPATH=src \
  python3 scripts/run_clean_room_public_tum_vi_sanity.py \
    --manifest manifests/tum_vi_room1_512_16_cam0_sanity.json \
    --progress-artifact .symphony/progress/HEL-72.json \
    --orchestration-log logs/out/hel-72_tum_vi_asan_no_static_alignment_orchestration.log
```

## Current Checkpoint Evidence

The clean-room pass has already left auditable setup/build evidence:

- Progress artifact: `.symphony/progress/HEL-72.json`
- Live frame overlay artifact: `.symphony/progress/HEL-72.jsonl`
- Orchestration log:
  `logs/out/hel-72_tum_vi_asan_no_static_alignment_orchestration.log`
- Build attempt JSON:
  `.symphony/build-attempts/orbslam3-build-20260320T233606Z.json`
- Build attempt log:
  `.symphony/build-attempts/orbslam3-build-20260320T233606Z.log`
- Runtime log: `logs/out/tum_vi_room1_512_16_cam0.log`

The build side succeeded with the combined changed variable:

- `enable_asan: true`
- `disable_eigen_static_alignment: true`
- `build_type: RelWithDebInfo`
- `cmake_cxx_flags: -std=gnu++14 -DEIGEN_MAX_STATIC_ALIGN_BYTES=0 -DEIGEN_DONT_ALIGN_STATICALLY -fsanitize=address -fno-omit-frame-pointer -g -O0`
- `third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi` exists
- `third_party/orbslam3/upstream/lib/libORB_SLAM3.so` exists

The runtime side has already crossed the old HEL-71 boundary:

- The log still shows first-map creation at frame `93`:
  - `First KF:0; Map init KF:0`
  - `New Map created with 375 points`
- Unlike HEL-71, the combined lane then continued:
  - `HEL-68 diagnostic: frame 93 TrackMonocular completed`
  - later checkpoints include `frame 111`, `frame 173`, `frame 268`,
    `frame 515`, and `frame 638` in the same run
- The JSONL live overlay now records the advancing frame boundary directly:
  - `.symphony/progress/HEL-72.jsonl` reached `completed: 638`
  - `progress_percent: 23`
  - `trajectory_files: []`
- A later instability window no longer crashes immediately:
  - repeated `Fail to track local map!` messages appeared through roughly
    frames `746-796`
  - the same run then rolled over into `Creation of new map with id: 1`
  - ORB-SLAM3 stored map `0`, reinitialized with `last KF id: 69`, and
    reported `New Map created with 157 points` at frame `799`
  - the raw log later continued through frame `809` and beyond instead of
    aborting at that second-map boundary
- No AddressSanitizer abort has appeared at the old first-map boundary

## Narrowed Blocker So Far

HEL-72 has not yet finished the full public replay at this checkpoint, so it
does not prove successful trajectory save yet.

It does prove a materially narrower and more actionable state than HEL-71:

- the combined ASan plus no-static-alignment lane clears the old frame-93
  first-map crash boundary
- the same lane now also survives a later tracking-loss and second-map
  reinitialization boundary on the public replay
- the remaining risk is now a later-runtime or save-phase outcome, not the
  immediate post-initialization segfault seen in HEL-71
- the private aggressive lens-10 rerun is still blocked in this checkout by
  missing calibration/extrinsics sidecars, not by an implicit undocumented host
  dependency

## Next Step

Let the active HEL-72 full replay finish and then classify the final outcome:

- successful public trajectory/report artifacts, or
- a later concrete runtime boundary with log evidence

Once the private calibration sidecars are available again, replay the HEL-57
aggressive lens-10 baseline with the same build toggle combination before any
tuned monocular settings are promoted into the canonical manifest.
