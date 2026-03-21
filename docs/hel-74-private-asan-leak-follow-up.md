# HEL-74 Private ASan Leak Follow-up

Status: Narrowed with auditable shutdown/save evidence
Issue: HEL-74
Last Updated: 2026-03-21

## Goal

Resume the private aggressive lens-10 monocular lane from
[HEL-57 monocular follow-up](hel-57-monocular-follow-up.md), keep the HEL-72
AddressSanitizer plus no-static-alignment build contract, and determine whether
the old post-initialization abort still blocks the real user sequence.

## Experiment Contract

- Changed variable: rebuild `mono_tum_vi` with `ORB_SLAM3_ENABLE_ASAN=1` and
  `ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1`, then rerun the HEL-57
  aggressive ORB settings on the private lens-10 bundle
- Hypothesis: the combined HEL-72 build toggles will move the private
  aggressive lane beyond the blind `double free or corruption (out)` abort and
  expose a sharper runtime boundary
- Success criterion: the private aggressive rerun writes trajectory artifacts or
  leaves a more specific post-init/shutdown failure than HEL-57
- Abort condition: the build fails, the rerun still dies before trajectory
  save, or the lane ends without new evidence

## Host Execution Summary

Executed from the `HEL-74` Symphony worktree on 2026-03-21.

- Re-imported the private lens-10 raw assets into
  `datasets/user/insta360_x3_one_lens_baseline/`
- Rebootstrapped the repo-local `ffmpeg`, `cmake`, `Eigen3`, OpenCV, Boost,
  and Pangolin prefixes in a clean HEL-74 worktree
- Rebuilt upstream `mono_tum_vi` at
  `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4` with AddressSanitizer enabled and
  Eigen static alignment disabled
- Replayed all 270 prepared frames with the HEL-57 aggressive ORB overrides:
  `nFeatures=4000`, `iniThFAST=8`, `minThFAST=3`

## Auditable Artifacts

- Progress artifact: `.symphony/progress/HEL-74.json`
- Build-attempt metadata:
  `.symphony/build-attempts/orbslam3-build-20260321T044439Z.json`
- Build-attempt log:
  `.symphony/build-attempts/orbslam3-build-20260321T044439Z.log`
- Orchestration log: `logs/out/hel-74_private_monocular_followup.log`
- Status report: `reports/out/hel-74_private_monocular_followup.md`
- Delegate log:
  `logs/out/insta360_x3_lens10_monocular_orb_aggressive_asan_no_static_alignment_hel74.log`
- Delegate report:
  `reports/out/insta360_x3_lens10_monocular_orb_aggressive_asan_no_static_alignment_hel74.md`

## What Changed Relative To HEL-57

HEL-57 proved that aggressive ORB tuning could create a first map, but both the
full-rate and stride-3 reruns aborted immediately after initialization with
`double free or corruption (out)`.

HEL-74 narrows that boundary materially:

- the ASan/no-static-alignment build finished successfully
- the private aggressive replay processed all `270` frames instead of dying near
  the first initialization
- the lane created two maps instead of one:
  - frame `77`: `New Map created with 93 points`
  - frame `252`: `New Map created with 71 points`
- each map was followed by a track-loss/reset sequence rather than a process abort:
  - frame `79`: `SYSTEM-> Reseting active map in monocular case`
  - frame `254`: `SYSTEM-> Reseting active map in monocular case`

## End-Of-Run Boundary

The run reached shutdown and attempted the save path:

- `Saving trajectory to f_insta360_x3_lens10_orb_aggressive_asan_no_static_alignment_hel74.txt ...`
- `HEL-63 diagnostic: SaveTrajectoryEuRoC completed`
- `Saving keyframe trajectory to kf_insta360_x3_lens10_orb_aggressive_asan_no_static_alignment_hel74.txt ...`
- `No keyframes were recorded; skipping keyframe trajectory save.`
- `HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed`

However, the expected trajectory files were still absent afterward under
`build/insta360_x3_lens10/monocular/trajectory_orb_aggressive_asan_no_static_alignment_hel74/`,
and LeakSanitizer forced a non-zero exit:

- `SUMMARY: AddressSanitizer: 598421471 byte(s) leaked in 2383336 allocation(s).`

Representative leak frames point into the same ORB-SLAM3 lifetime surfaces that
matter for monocular map creation and connection bookkeeping:

- `ORB_SLAM3::Tracking::CreateInitialMapMonocular()`
- `ORB_SLAM3::LocalMapping::ProcessNewKeyFrame()`
- `ORB_SLAM3::KeyFrame::UpdateConnections(bool)`
- `ORB_SLAM3::Atlas::AddCamera(ORB_SLAM3::GeometricCamera*)`

## Narrowed Blocker

The remaining blocker is no longer the HEL-57 post-init allocator abort.

It is now narrower and later:

- the private aggressive lane survives both initialization events
- the process reaches `SaveTrajectoryEuRoC`
- the expected frame trajectory is still missing afterward
- LeakSanitizer returns exit code `1` at shutdown because ORB-SLAM3 leaves large
  persistent heap allocations behind

That means the next follow-up should focus on the shutdown/save path and leak
policy interaction, not on first-map creation.

## Recommended Next Step

Keep the HEL-74 aggressive private lane as the diagnostic baseline and isolate
why the save call does not leave the expected frame trajectory artifact before
LeakSanitizer terminates the process:

1. determine whether ORB-SLAM3 is writing the frame trajectory to an unexpected
   path or skipping the actual file write despite reporting completion
2. distinguish genuine save-path failure from LeakSanitizer-only exit semantics
3. only then decide whether the aggressive ORB settings are safe to promote into
   the canonical manifest
