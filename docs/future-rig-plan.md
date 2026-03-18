# Future Rig Plan

Status: Draft
Issue: HEL-51
Last Updated: 2026-03-18

## Why Monocular Comes First

The back-to-back rig should not be the first ORB-SLAM3 target. A single-lens
monocular lane retires the immediate unknowns one at a time:

- whether the lens-10 calibration maps cleanly into ORB-SLAM3's
  `KannalaBrandt8` settings format
- whether the frame timestamps and file layout can be normalized into the
  upstream `mono_tum_vi` contract
- whether one lens produces stable tracking without any IMU dependency

If the monocular lane fails, the team can debug calibration, image quality, and
timestamp handling directly instead of mixing those problems with multi-camera
fusion.

## Constraint On The Back-To-Back Rig

This next point is an engineering inference from the standard ORB-SLAM3 stereo
pipeline and stereo geometry, not a direct claim from a custom rig example in
upstream docs:

- ORB-SLAM3 stereo expects left and right cameras to share enough scene overlap
  to triangulate landmarks and maintain a coupled map.
- A non-overlapping back-to-back rig does not provide that shared image support
  in the normal forward motion case.
- Because of that, the back-to-back rig should not be treated as a drop-in
  replacement for the upstream stereo or stereo-fisheye examples.

## Recommended Phases After The Monocular Baseline

### Phase 1: Stabilize Each Lens Independently

- Reuse the monocular contract from `docs/monocular-baseline.md` for each lens.
- Produce one calibration JSON, one frame index CSV, one settings YAML, and one
  report per lens.
- Confirm each lens can initialize and track on its own before any fusion work.

### Phase 2: Add Rig Metadata Without Changing The Baseline Runner

- Record the static extrinsic transform between the front and back lens frames.
- Record any shared clock behavior or fixed timestamp offsets between the two
  lens exports.
- Store that rig metadata in a separate file instead of trying to overload the
  monocular ORB-SLAM3 settings bundle.

### Phase 3: Fuse Outside The Core Monocular Lane

- Start with two independent monocular trajectories plus the known rigid
  transform between lens frames.
- Evaluate offline pose alignment, relocalization, or pose-graph stitching on
  top of those trajectories.
- Add IMU only after the monocular image lanes and rig timing are trustworthy.

### Phase 4: Consider A Fork Only If The Simpler Path Breaks

- If the dual-monocular approach proves the cameras are usable but offline
  fusion is still inadequate, evaluate maintained forks or downstream tooling
  that explicitly support multi-camera or non-overlapping rigs.
- Do not pay that complexity cost before the monocular baseline works, because a
  fork cannot rescue bad calibration or bad timestamps.

## What "Ready For The Next Issue" Looks Like

The future rig support lane should not start until the repo can show all of the
following from the monocular baseline:

- one pinned upstream baseline and commit
- one reproducible calibration-to-settings conversion
- one reproducible frame normalization path
- one report that states whether lens-10 tracking initializes and where it
  fails or succeeds

Once those exist, the next issue can focus on dual-lens rig metadata and
trajectory fusion instead of first-principles monocular bring-up.
