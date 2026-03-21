# HEL-73 Private Aggressive Follow-up

Status: In Progress
Issue: HEL-73
Last Updated: 2026-03-21

## Goal

Turn the unresolved private blocker from
[final-validation-report.md](final-validation-report.md) into a direct repo
entrypoint that starts from the HEL-57 aggressive ORB path and either executes
the next lens-10 rerun or fails with a precise audited prerequisite boundary.

## Experiment Contract

- Changed variable: replay the HEL-57 aggressive ORB lens-10 baseline after
  rebuilding `mono_tum_vi` with AddressSanitizer enabled and Eigen static alignment
  disabled
- Hypothesis: the combined HEL-72 build toggles will either let the private
  aggressive baseline save trajectories or surface a narrower post-init
  boundary than the original `double free or corruption (out)` abort
- Success criterion: the aggressive private rerun writes non-empty trajectory
  artifacts or leaves a more specific runtime boundary than HEL-57
- Abort condition: required raw calibration/extrinsics sidecars are missing,
  the rebuild fails, or the rerun still aborts before trajectory save

## Repo Changes In This Pass

- `scripts/run_private_monocular_followup.py` now codifies the HEL-73 private
  rerun lane:
  - reuses an existing prepared lens-10 bundle when present
  - otherwise requires the raw source contract explicitly:
    - `00.mp4`
    - `10.mp4`
    - `insta360_x3_kb4_00_calib.txt`
    - `insta360_x3_kb4_10_calib.txt`
    - `insta360_x3_extr_rigs_calib.json`
  - fetches the pinned ORB-SLAM3 checkout
  - rebuilds `mono_tum_vi` with `ORB_SLAM3_ENABLE_ASAN=1` and
    `ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1`
  - delegates to `scripts/run_monocular_baseline.py` with:
    - `nFeatures=4000`
    - `iniThFAST=8`
    - `minThFAST=3`
- `make monocular-prereqs` now reports raw-source readiness separately from the
  prepared lens bundle and execution assets, so missing calibration/extrinsics
  sidecars are visible in the saved prerequisite report instead of being folded
  into a generic missing-input state

## Host Evidence From This Pass

The active HEL-73 worktree still does not contain:

- `datasets/user/insta360_x3_one_lens_baseline/raw/calibration/insta360_x3_kb4_00_calib.txt`
- `datasets/user/insta360_x3_one_lens_baseline/raw/calibration/insta360_x3_kb4_10_calib.txt`
- `datasets/user/insta360_x3_one_lens_baseline/raw/calibration/insta360_x3_extr_rigs_calib.json`
- the prepared `datasets/user/insta360_x3_one_lens_baseline/lenses/10/` bundle

Host search during this pass found only the raw videos:

- `/home/helionaut/.openclaw/workspace/downloads/insta360-b87308a3/00.mp4`
- `/home/helionaut/.openclaw/workspace/downloads/insta360-b87308a3/10.mp4`

That means the private follow-up is still blocked before the aggressive rerun could start,
but the blocker is now narrowed to the missing raw
calibration/extrinsics sidecars instead of another implicit worktree or
bootstrap dependency.

## Command

```bash
PYTHONPATH=src python3 scripts/run_private_monocular_followup.py \
  --video-00 /home/helionaut/.openclaw/workspace/downloads/insta360-b87308a3/00.mp4 \
  --video-10 /home/helionaut/.openclaw/workspace/downloads/insta360-b87308a3/10.mp4
```

## Auditable Artifacts

- Progress artifact: `.symphony/progress/HEL-73.json`
- Orchestration log: `logs/out/hel-73_private_monocular_followup.log`
- Status report: `reports/out/hel-73_private_monocular_followup.md`

## Result So Far

This pass does not yet produce a new private trajectory artifact, but it
narrows the remaining blocker with repo-owned evidence:

- the HEL-72 public surrogate lane remains the latest successful save-path
  proof
- the HEL-73 private rerun entrypoint now exists in the repo instead of only in
  issue prose
- the current host is specifically missing the raw calibration/extrinsics
  sidecars needed to rebuild the private lens-10 bundle, even though the raw
  `00.mp4` and `10.mp4` exports are present elsewhere on disk

## Next Step

Restore the missing raw calibration/extrinsics sidecars, then rerun
`scripts/run_private_monocular_followup.py` so the aggressive private lane can
either save trajectories or expose the next post-initialization boundary with
fresh auditable artifacts.
