# HEL-71 Eigen Static-Alignment Follow-up

Status: Narrowed with auditable public rerun
Issue: HEL-71
Last Updated: 2026-03-21

## Goal

Start from the
[HEL-57 monocular follow-up](hel-57-monocular-follow-up.md), keep the aggressive
ORB/post-initialization crash as the active blocker, and test whether disabling
Eigen static alignment changes the remaining first-map abort boundary before any
private lens-10 tuning is promoted into the canonical manifest.

## Why This Pass Uses The Public Lane

The active `HEL-71` checkout still contains `datasets/user/README.md` instead
of the private lens-10 bundle under
`datasets/user/insta360_x3_one_lens_baseline/`. That means the HEL-57
aggressive private rerun cannot be replayed directly from this workspace.

This pass therefore codifies the next changed variable in repo scripts and
validates it first on the clean-room public TUM-VI `room1_512_16` `cam0`
reproducer that already shares the same first-map crash boundary from HEL-67
and HEL-68.

## Experiment Contract

- Changed variable: build the public `mono_tum_vi` lane with
  `ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1`
- Hypothesis: disabling Eigen static alignment will move the public
  post-initialization failure beyond the HEL-70 assertion family or expose a
  sharper remaining bug
- Success criterion: the rerun leaves auditable HEL-71 artifacts and either
  survives first-map creation or narrows the crash beyond the old boundary
- Abort condition: the build fails before `mono_tum_vi` exists, or the rerun
  still dies at the same effective first-map boundary without new evidence

## What Changed In Repo Code

- `scripts/build_orbslam3_baseline.sh` now accepts
  `ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1`
- That toggle appends:
  - `-DEIGEN_MAX_STATIC_ALIGN_BYTES=0`
  - `-DEIGEN_DONT_ALIGN_STATICALLY`
- The build wrapper now carries this changed variable into:
  - `.symphony/build-attempts/orbslam3-build-*.json`
  - `.symphony/progress/HEL-71.json`
- `scripts/run_clean_room_public_tum_vi_sanity.py` now honors externally
  supplied build experiment fields so HEL-71 artifacts record the actual lane

## Command

```bash
env \
  ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1 \
  ORB_SLAM3_BUILD_PARALLELISM=1 \
  ORB_SLAM3_BUILD_EXPERIMENT='hel-71-eigen-static-alignment-public-tum-vi' \
  ORB_SLAM3_BUILD_CHANGED_VARIABLE='disable Eigen static alignment for the public mono_tum_vi post-initialization reproducer' \
  ORB_SLAM3_BUILD_HYPOTHESIS='disabling Eigen static alignment will move the public post-init failure beyond the HEL-70 assertion boundary or expose a sharper remaining bug' \
  ORB_SLAM3_BUILD_SUCCESS_CRITERION='mono_tum_vi builds and the public TUM-VI rerun either survives first-map creation or leaves a narrower failure boundary with auditable artifacts' \
  PYTHONPATH=src \
  python3 scripts/run_clean_room_public_tum_vi_sanity.py \
    --manifest manifests/tum_vi_room1_512_16_cam0_sanity.json \
    --progress-artifact .symphony/progress/HEL-71.json \
    --orchestration-log logs/out/hel-71_tum_vi_no_static_alignment_orchestration.log
```

## Observed Result

The build side of the experiment succeeded:

- Build attempt JSON:
  `.symphony/build-attempts/orbslam3-build-20260320T225148Z.json`
- Build attempt log:
  `.symphony/build-attempts/orbslam3-build-20260320T225148Z.log`
- Progress artifact: `.symphony/progress/HEL-71.json`
- Build outcome:
  - `disable_eigen_static_alignment: true`
  - `cmake_cxx_flags: -std=gnu++14 -DEIGEN_MAX_STATIC_ALIGN_BYTES=0 -DEIGEN_DONT_ALIGN_STATICALLY`
  - executable exists:
    `third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi`
  - shared library exists:
    `third_party/orbslam3/upstream/lib/libORB_SLAM3.so`

The runtime side still failed:

- Orchestration log:
  `logs/out/hel-71_tum_vi_no_static_alignment_orchestration.log`
- Public run log: `logs/out/tum_vi_room1_512_16_cam0.log`
- Public run report: `reports/out/tum_vi_room1_512_16_cam0.md`
- Exit code: `139`
- Prepared frames: `2821`
- Trajectory artifacts: missing

The new public boundary is:

- `HEL-68 diagnostic: frame 92 TrackMonocular completed`
- `HEL-68 diagnostic: frame 93 TrackMonocular start timestamp=...`
- `First KF:0; Map init KF:0`
- `New Map created with 375 points`
- `Segmentation fault (core dumped)`

The run still does **not** reach:

- `HEL-63 diagnostic: entering SLAM shutdown`
- `HEL-63 diagnostic: calling SaveTrajectoryEuRoC ...`
- `HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC ...`

## Narrowed Blocker

HEL-71 does not unblock the lane, but it does narrow the remaining risk:

- disabling Eigen static alignment is **not** sufficient to clear the
  post-initialization crash on the public `mono_tum_vi` reproducer
- the public boundary remains frame `93`, immediately after first-map creation
  with `375` points
- the build now succeeds cleanly with the alignment toggle, so the remaining
  blocker is runtime behavior during or immediately after first-map creation,
  not inability to compile that lane with unaligned fixed-size Eigen storage

This is concrete evidence against promoting the alignment toggle into the
canonical manifest as a standalone fix.

## Recommended Next Step

Keep the HEL-57 aggressive monocular lane as the private baseline, but treat
HEL-71 as proof that Eigen static-alignment policy alone does not resolve the
crash.

The next materially different diagnostic should combine this build toggle with
symbolized runtime evidence on the public lane, for example:

- rerun the public `mono_tum_vi` reproducer with both
  `ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1` and `ORB_SLAM3_ENABLE_ASAN=1`
- or capture an equivalent symbolized backtrace on the private aggressive lane
  once the lens-10 bundle is available again
