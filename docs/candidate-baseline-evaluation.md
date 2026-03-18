# Candidate Baseline Evaluation

Status: Draft  
Issue: HEL-48  
Last Updated: 2026-03-18

## Scope

This memo records the HEL-48 baseline-selection pass for the monocular
Insta360 X3 lens-10 lane. The immediate goal is to choose one explicit
ORB-SLAM3 source baseline that later tuning work can build on without
reopening source selection.

The candidate set is intentionally small:

- official upstream `master`
- official upstream `v1.0-release`
- `MAVIS-SLAM/OpenMAVIS` as a credible fork for the future multi-camera
  question

The comparison manifests live in:

- `manifests/insta360_x3_lens10_monocular_baseline.json`
- `manifests/insta360_x3_lens10_upstream_v1_0_release_evaluation.json`
- `manifests/insta360_x3_lens10_openmavis_master_evaluation.json`

All three manifests point at the same private inputs:

- `datasets/user/insta360_x3_lens10/monocular_calibration.json`
- `datasets/user/insta360_x3_lens10/frame_index.csv`

## Environment Evidence

The local machine used for this pass does not currently provide the native
build stack required for a full ORB-SLAM3 compile:

- `cmake` is absent from `PATH`
- `pkg-config` cannot resolve `opencv4` or `opencv`
- `pkg-config` cannot resolve `pangolin`

That means candidate build attempts are blocked by local infrastructure before
the source trees can be compared on compiled binaries.

The same machine also does not contain the private lens-10 inputs expected by
the manifests above, so runtime validation on the target sequence is blocked
for every candidate before any `mono_tum_vi` launch can happen.

## Candidate Matrix

| Candidate | Repo / commit | Build result | Run result | Notable observations |
| --- | --- | --- | --- | --- |
| Selected baseline | `UZ-SLAMLab/ORB_SLAM3` @ `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4` | Blocked locally by missing `cmake`, OpenCV dev metadata, and Pangolin metadata | Blocked locally by missing `datasets/user/insta360_x3_lens10/monocular_calibration.json` and `datasets/user/insta360_x3_lens10/frame_index.csv` | Current upstream reference line. `master` is only two commits ahead of `v1.0-release`, and both commits update docs only (`README.md`, `Dependencies.md`). |
| Alternative commit | `UZ-SLAMLab/ORB_SLAM3` @ `0df83dde1c85c7ab91a0d47de7a29685d046f637` | Blocked by the same local infrastructure gap | Blocked by the same missing private lens-10 inputs | Still a valid upstream baseline, but not materially different from current `master` for this lane because the post-release delta is documentation-only. |
| Alternative fork | `MAVIS-SLAM/OpenMAVIS` @ `b13b1c20e84efa4bb63564e26308541af70d03f2` | Blocked by the same local infrastructure gap | Blocked by the same missing private lens-10 inputs | Adds multi-camera visual-inertial work, but the fork is framed around multiple partially overlapped camera systems and Hilti-style multi-inertial runs, not the current single-lens no-IMU baseline or a back-to-back non-overlapping rig. |

## Source-Level Findings

### Upstream master vs `v1.0-release`

`HEL-48` checked the current upstream `master` against `v1.0-release` and found
that `master` is ahead by only two commits:

- `851db08347849a94c51d3ebc3a36df8a114b800f` (`Update README.md`)
- `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4` (`Update Dependencies.md`)

No code changes were found in that upstream delta, so choosing `master` keeps
the project aligned with the explicit upstream reference branch without
changing the executable monocular TUM-VI lane relative to the old release tag.

### Non-overlapping rig support

The official upstream issue tracker still shows the back-to-back stereo problem
as unresolved:

- issue `#240` asks whether non-overlapping fisheye stereo is possible and
  reports failed initialization on a back-to-back pair
- the follow-up comment reports no working solution and points at the stereo
  initialization path as the likely reason

That lines up with the current CEO direction: do not treat the user’s current
back-to-back rig as a normal stereo baseline.

### Omni / dual-fisheye / equirectangular support

The upstream issue tracker also does not show a maintained official path for
dual-fisheye or omnidirectional input:

- issue `#534` asks about dual-fisheye / omni support
- the only practical follow-up in that thread falls back to using one side of
  the dual-fisheye camera, not a native omni or equirectangular pipeline

No stronger official upstream path was found during this pass.

### Why OpenMAVIS is not the chosen baseline

`OpenMAVIS` is the most relevant fork found for the future custom-rig question,
but it is still the wrong starting point for the immediate lens-10 objective:

- its README positions the fork around multiple partially overlapped camera
  systems and visual-inertial SLAM
- its documented evaluation path targets the Hilti Challenge multi-camera VI
  dataset
- it does not claim a direct fix for the current back-to-back non-overlapping
  rig, nor a native equirectangular ingestion path
- adopting it now would increase divergence from the official monocular fisheye
  path before the project has validated the simpler single-lens baseline

## Recommendation

Start later tuning work from the official upstream ORB-SLAM3 `master` line,
pinned explicitly to commit `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`.

That recommendation is intentionally narrow:

- monocular lens `10` first
- no IMU in the first validation pass
- do not use the current back-to-back rig as a stereo baseline
- revisit IMU integration only after monocular replay is stable
- treat any future non-overlapping rig or multi-camera fusion work as a
  separate engineering extension, not as baseline selection

## Remaining Blockers

Before the candidate manifests can produce real runtime comparisons, the local
environment still needs:

- native ORB-SLAM3 build prerequisites (`cmake`, OpenCV development package,
  Pangolin development package)
- the private lens-10 monocular inputs under `datasets/user/insta360_x3_lens10/`

Until those exist on the same machine, HEL-48 can lock the source baseline and
the normalized evaluation contract, but not a full side-by-side runtime report
from the real sequence.
