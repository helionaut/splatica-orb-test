# HEL-70 Eigen Alignment Follow-up

Status: Narrowed with auditable private-host rerun
Issue: HEL-70
Last Updated: 2026-03-21

## Goal

Start from [HEL-57 monocular follow-up](hel-57-monocular-follow-up.md), reuse
the aggressive ORB lane as the private-host diagnostic baseline, and determine
whether the HEL-68 `OptimizableTypes.cpp` Jacobian lifetime fix changes the
post-initialization abort boundary.

## What Changed In This Pass

- Reused the existing HEL-70 worktree edits that:
  - patch `src/OptimizableTypes.cpp` to force `.eval()` on
    `EdgeSE3ProjectXYZ::linearizeOplus()`
  - add runtime progress artifacts for the native bootstrap/build/run lanes
- Rebuilt ORB-SLAM3 until the worktree again had:
  - `third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi`
  - `third_party/orbslam3/upstream/lib/libORB_SLAM3.so`
- Revalidated the private lens-10 lane with:

```bash
make monocular-prereqs
```

  which now reports `Ready for full execution: true`
- Relaunched the HEL-57 aggressive monocular rerun from this rebuilt lane:

```bash
./scripts/run_monocular_baseline.py \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
  --output-tag orb_aggressive \
  --orb-n-features 4000 \
  --orb-ini-fast 8 \
  --orb-min-fast 3
```

## Observed Result

The rerun still does not produce saved trajectories, but it narrows the blocker
further than the old `double free or corruption (out)` message from HEL-57.

- Report: `reports/out/insta360_x3_lens10_monocular_orb_aggressive.md`
- Log: `logs/out/insta360_x3_lens10_monocular_orb_aggressive.log`
- Progress artifact: `.symphony/progress/HEL-70.json`
- Exit code: `134`
- Prepared frames: `270`
- Frame counter at failure: `77`
- Prepared image directory:
  `build/insta360_x3_lens10/monocular/images_orb_aggressive`
- Trajectory directory:
  `build/insta360_x3_lens10/monocular/trajectory_orb_aggressive/`

Key log boundary:

- `First KF:0; Map init KF:0`
- `New Map created with 93 points`
- `mono_tum_vi: .../Eigen/src/Core/DenseStorage.h:128: ... plain_array<... Size = 4 ...>::plain_array(): Assertion ... eigen_unaligned_array_assert_workaround_gcc47(array) ... failed.`
- `Aborted (core dumped)`

The rerun log does **not** reach any of these patched shutdown/save markers:

- `HEL-63 diagnostic: entering SLAM shutdown`
- `HEL-63 diagnostic: calling SaveTrajectoryEuRoC ...`
- `HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC ...`

That means the HEL-68 Jacobian lifetime fix changes the failure mode from a
generic allocator abort to a concrete Eigen alignment assertion, but the crash
still happens immediately after first-map creation and before shutdown or any
trajectory-save call begins.

## Narrowed Blocker

The remaining blocker is now:

- private-host aggressive monocular lane
- after first-map creation (`93` points)
- during or immediately after frame `77` `TrackMonocular`
- before shutdown/save
- concrete failure family: Eigen fixed-size alignment assertion in
  `Eigen/src/Core/DenseStorage.h`

This is narrower than HEL-57 because the next pass no longer has to start from
the undifferentiated `double free or corruption (out)` boundary.

## Next Recommended Step

Keep the HEL-57 aggressive lane as the baseline, but focus the next attempt on
the first-map code path that now survives long enough to hit the Eigen
alignment assert. The next materially different diagnostic should capture a
native backtrace for the assertion or patch the relevant fixed-size Eigen
holders/containers involved in post-initialization bundle adjustment.
