# TUM RGB-D Sanity Run Report

Status: Final
Issue: HEL-64
Last Updated: 2026-03-20

## Published Verdict

- Published report verdict: `not_useful`
- Why: the clean-room public run reached ORB-SLAM3 execution, created an
  initial map with `837` points on frame `0`, then aborted on frame `1` with
  `double free or corruption (out)` before either TUM trajectory file was
  written.
- What this answers: the repo now has a CEO-readable report bundle that makes
  the outcome inspectable. It also makes clear that the current public TUM lane
  is not yet a trustworthy known-good baseline.

## Exactly What Ran

- Producing repo commit: `70f1990d869f7a5b26080a9f614b00fd00f2649f`
- ORB-SLAM3 upstream commit: `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
- Manifest: `manifests/tum_rgbd_fr1_xyz_sanity.json`
- Launch wrapper: `scripts/run_clean_room_rgbd_sanity.py`
- Runtime command:
  `/usr/bin/xvfb-run -a .../Examples/RGB-D/rgbd_tum .../Vocabulary/ORBvoc.txt .../Examples/RGB-D/TUM1.yaml .../datasets/public/tum_rgbd/rgbd_dataset_freiburg1_xyz .../Examples/RGB-D/associations/fr1_xyz.txt`
- Dataset: `datasets/public/tum_rgbd/rgbd_dataset_freiburg1_xyz`
- Association file: `third_party/orbslam3/upstream/Examples/RGB-D/associations/fr1_xyz.txt`
- Associations loaded: `792`
- Diagnostic toggles: viewer enabled, no frame cap, no trajectory-save skips

## Summary Metrics

- Raw process exit code: `134`
- Final report exit code: `2`
- Camera trajectory points: `0`
- Keyframe trajectory points: `0`
- Camera / association coverage: `0.0%`
- Keyframe / association coverage: `0.0%`
- Camera path length: `0.000 m`
- Camera displacement: `0.000 m`
- Camera timestamp span: `0.000 s`

## Artifact Locations

Canonical published bundle:

- `reports/published/tum_rgbd_fr1_xyz_sanity/index.html`
- `reports/published/tum_rgbd_fr1_xyz_sanity/artifact-manifest.json`
- `reports/published/tum_rgbd_fr1_xyz_sanity/reports/out/tum_rgbd_fr1_xyz.md`
- `reports/published/tum_rgbd_fr1_xyz_sanity/reports/out/tum_rgbd_fr1_xyz_summary.json`
- `reports/published/tum_rgbd_fr1_xyz_sanity/reports/out/tum_rgbd_fr1_xyz_trajectory.svg`
- `reports/published/tum_rgbd_fr1_xyz_sanity/reports/out/tum_rgbd_fr1_xyz.html`
- `reports/published/tum_rgbd_fr1_xyz_sanity/logs/out/tum_rgbd_fr1_xyz.log`

Local generated evidence from the run:

- `reports/out/tum_rgbd_fr1_xyz.md`
- `reports/out/tum_rgbd_fr1_xyz_summary.json`
- `reports/out/tum_rgbd_fr1_xyz_trajectory.svg`
- `reports/out/tum_rgbd_fr1_xyz.html`
- `logs/out/tum_rgbd_fr1_xyz.log`

Expected but missing in this run:

- `build/tum_rgbd_fr1_xyz/trajectory/CameraTrajectory.txt`
- `build/tum_rgbd_fr1_xyz/trajectory/KeyFrameTrajectory.txt`

## Acceptance Criteria Check

- Trajectory visualization: met. The published bundle includes the trajectory
  SVG plus the published index page. The plot correctly shows that no
  trajectory points were available.
- Run metadata and config: met. The report records repo commit, upstream
  commit, manifest, launch wrapper, runtime command, dataset, association file,
  and diagnostic toggles.
- Summary metrics: met. The bundle records association count, exit codes,
  trajectory point counts, coverage ratios, and motion-range metrics.
- Explicit artifact locations: met. The report names both the canonical
  published bundle paths and the local generated artifact paths, plus the
  trajectory files that were expected but missing.
- Known-good baseline answer: met. The published verdict is explicit: the
  current public TUM RGB-D sanity lane is not yet useful as a known-good
  baseline because it aborts before saving trajectories.

## Review Notes

- The published index at
  `reports/published/tum_rgbd_fr1_xyz_sanity/index.html` is the primary review
  surface. It includes the sample frames, trajectory plot, verdict, metrics,
  and direct links into the copied report/log/summary artifacts.
- The secondary copied visual report at
  `reports/published/tum_rgbd_fr1_xyz_sanity/reports/out/tum_rgbd_fr1_xyz.html`
  preserves the exact local runner output for audit history.
