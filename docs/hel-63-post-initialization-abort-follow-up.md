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

## This Pass

The active `HEL-63` worktree did not contain the local-only lens-10 bundle
under `datasets/user/insta360_x3_one_lens_baseline/`, so this pass could not
re-execute the private aggressive-ORB lane directly from the current checkout.

Instead, this follow-up codified the next crash-isolation step in repo code:

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

## Expected Evidence

Each diagnostic rerun writes distinct artifacts keyed by `--output-tag`, so the
follow-up evidence no longer depends on overwritten canonical outputs:

- settings YAML under `build/insta360_x3_lens10/monocular/`
- prepared images/timestamps under `build/insta360_x3_lens10/monocular/`
- trajectory outputs under `build/insta360_x3_lens10/monocular/`
- log under `logs/out/`
- report under `reports/out/`

The patched upstream log now emits:

- `HEL-63 diagnostic: entering SLAM shutdown`
- `HEL-63 diagnostic: SLAM shutdown completed`
- `HEL-63 diagnostic: calling SaveTrajectoryEuRoC ...`
- `HEL-63 diagnostic: SaveTrajectoryEuRoC completed`
- `HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC ...`
- `HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed`

The first missing marker after map creation identifies the narrowed boundary for
the remaining abort.
