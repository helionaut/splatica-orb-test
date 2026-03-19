# HEL-63 Post-Initialization Abort Follow-up

Status: In Progress
Issue: HEL-63
Last Updated: 2026-03-20

## Goal

Turn the HEL-57 monocular blocker into a reproducible diagnostic lane that can
separate:

- shutdown never completed
- frame-trajectory save caused the abort
- keyframe-trajectory save caused the abort
- the crash happens before any save call begins
- the same abort reproduces on the public RGB-D sanity lane

## This Pass

The active `HEL-63` worktree did not contain the local-only lens-10 bundle
under `datasets/user/insta360_x3_one_lens_baseline/`, so this pass could not
re-execute the private aggressive-ORB lane directly from the current checkout.

Instead, this follow-up codified the next crash-isolation step in repo code
and captured a public repro on the clean-room TUM RGB-D lane:

- `scripts/run_monocular_baseline.py` now accepts:
  - `--output-tag`
  - `--frame-stride`
  - `--orb-n-features`
  - `--orb-ini-fast`
  - `--orb-min-fast`
  - `--skip-frame-trajectory-save`
  - `--skip-keyframe-trajectory-save`
- `scripts/patch_orbslam3_baseline.py` now patches upstream
  `Examples/Monocular/mono_tum_vi.cc` so the log prints save-phase boundaries
  and honors:
  - `ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE=1`
  - `ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE=1`
- `scripts/patch_orbslam3_baseline.py` now also patches upstream
  `Examples/RGB-D/rgbd_tum.cc` so the log prints per-frame `TrackRGBD`
  boundaries, shutdown/save markers, and honors:
  - `ORB_SLAM3_HEL63_MAX_FRAMES=<N>`
  - `ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE=1`
  - `ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE=1`
- `scripts/run_rgbd_tum_baseline.py` now accepts:
  - `--max-frames`
  - `--disable-viewer`
  - `--skip-frame-trajectory-save`
  - `--skip-keyframe-trajectory-save`

The public clean-room rerun on `manifests/tum_rgbd_fr1_xyz_sanity.json`
compiled and launched `rgbd_tum`, then reproduced the same post-map-creation
abort:

- `New Map created with 837 points`
- `double free or corruption (out)`

The saved `logs/out/tum_rgbd_fr1_xyz.log` did not reach
`HEL-63 diagnostic: entering SLAM shutdown`, which narrows the blocker further:
the public repro dies before `System::Shutdown()` or either trajectory-save
call begins.

A bounded rerun with the default viewer setting:

```bash
./scripts/run_rgbd_tum_baseline.py \
  --manifest manifests/tum_rgbd_fr1_xyz_sanity.json \
  --output-tag max20_default \
  --max-frames 20
```

left a sharper boundary in `logs/out/tum_rgbd_fr1_xyz_max20_default.log`:

- `HEL-63 diagnostic: frame 0 TrackRGBD completed`
- `HEL-63 diagnostic: frame 1 TrackRGBD start timestamp=...`
- `double free or corruption (out)`

That proves the public repro survives the first `TrackRGBD` call, creates the
first map, and then aborts during or immediately after the second `TrackRGBD`
call, still before shutdown/save begins.

A second bounded rerun with the viewer explicitly disabled:

```bash
./scripts/run_rgbd_tum_baseline.py \
  --manifest manifests/tum_rgbd_fr1_xyz_sanity.json \
  --output-tag max20_no_viewer \
  --max-frames 20 \
  --disable-viewer
```

left the same boundary in `logs/out/tum_rgbd_fr1_xyz_max20_no_viewer.log`:

- `HEL-63 diagnostic: rgbd_tum disable_viewer=1`
- `HEL-63 diagnostic: frame 0 TrackRGBD completed`
- `HEL-63 diagnostic: frame 1 TrackRGBD start timestamp=...`
- `double free or corruption (out)`

That rules Pangolin/viewer teardown out as the immediate cause on the public
lane. The remaining public blocker is now narrowed to tracking-time allocator
corruption during or immediately after the second `TrackRGBD` call, before
shutdown or any trajectory-save function is reached.

## Diagnostic Baseline Commands

Aggressive ORB baseline, full prepared frame list:

```bash
./scripts/run_monocular_baseline.py \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
  --output-tag orb_aggressive \
  --orb-n-features 4000 \
  --orb-ini-fast 8 \
  --orb-min-fast 3
```

Aggressive ORB plus stride-3 replay:

```bash
./scripts/run_monocular_baseline.py \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
  --output-tag orb_aggressive_stride3 \
  --orb-n-features 4000 \
  --orb-ini-fast 8 \
  --orb-min-fast 3 \
  --frame-stride 3
```

Isolation rerun that skips only keyframe save:

```bash
./scripts/run_monocular_baseline.py \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
  --output-tag orb_aggressive_skip_keyframes \
  --orb-n-features 4000 \
  --orb-ini-fast 8 \
  --orb-min-fast 3 \
  --skip-keyframe-trajectory-save
```

Isolation rerun that skips only frame save:

```bash
./scripts/run_monocular_baseline.py \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
  --output-tag orb_aggressive_skip_frames \
  --orb-n-features 4000 \
  --orb-ini-fast 8 \
  --orb-min-fast 3 \
  --skip-frame-trajectory-save
```

Public RGB-D bounded repro:

```bash
./scripts/run_rgbd_tum_baseline.py \
  --manifest manifests/tum_rgbd_fr1_xyz_sanity.json \
  --max-frames 20
```

Public RGB-D bounded repro with viewer disabled:

```bash
./scripts/run_rgbd_tum_baseline.py \
  --manifest manifests/tum_rgbd_fr1_xyz_sanity.json \
  --max-frames 20 \
  --disable-viewer
```

Public RGB-D bounded repro with shutdown/save isolation toggles:

```bash
./scripts/run_rgbd_tum_baseline.py \
  --manifest manifests/tum_rgbd_fr1_xyz_sanity.json \
  --max-frames 20 \
  --skip-frame-trajectory-save \
  --skip-keyframe-trajectory-save
```

## Expected Evidence

Each diagnostic rerun writes distinct artifacts keyed by `--output-tag`, so the
follow-up evidence no longer depends on overwritten canonical outputs:

- settings YAML under `build/insta360_x3_lens10/monocular/`
- prepared images/timestamps under `build/insta360_x3_lens10/monocular/`
- trajectory outputs under `build/insta360_x3_lens10/monocular/`
- log under `logs/out/`
- report under `reports/out/`

The patched upstream log now emits:

- `HEL-63 diagnostic: frame <n> TrackRGBD start timestamp=...`
- `HEL-63 diagnostic: frame <n> TrackRGBD completed`
- `HEL-63 diagnostic: entering SLAM shutdown`
- `HEL-63 diagnostic: SLAM shutdown completed`
- `HEL-63 diagnostic: calling SaveTrajectoryEuRoC ...`
- `HEL-63 diagnostic: SaveTrajectoryEuRoC completed`
- `HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC ...`
- `HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed`
- `HEL-63 diagnostic: calling SaveTrajectoryTUM ...`
- `HEL-63 diagnostic: SaveTrajectoryTUM completed`
- `HEL-63 diagnostic: calling SaveKeyFrameTrajectoryTUM ...`
- `HEL-63 diagnostic: SaveKeyFrameTrajectoryTUM completed`

The first missing marker after map creation identifies the narrowed boundary for
the remaining abort.
