# TUM-VI Monocular Sanity Run Report

Status: Final
Issue: HEL-67
Last Updated: 2026-03-20

## Verdict

- Public sanity verdict: `runtime_blocked`
- Why: the clean-room public run built the pinned upstream `mono_tum_vi`
  binary, prepared `2821` public `room1_512_16` `cam0` frames, initialized a
  new map with `375` points, and then aborted with
  `double free or corruption (out)` before either trajectory file was written.
- What this answers: the pinned upstream monocular fisheye lane is no longer a
  compile-only question on this host. It reaches real public TUM-VI runtime
  and still fails, so the lane is not healthy enough to treat as a known-good
  upstream baseline.

## Exactly What Ran

- Producing repo commit: `83ac733b3813ffc0063c842f72054e048ce0ec80`
- ORB-SLAM3 upstream commit: `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
- Clean-room runner: `scripts/run_clean_room_public_tum_vi_sanity.py`
- Manifest: `manifests/tum_vi_room1_512_16_cam0_sanity.json`
- Chosen public sequence: `dataset-room1_512_16`, camera `cam0`
- Why this sequence: the room sequences publish full motion-capture ground
  truth, the `512_16` EuRoC export is smaller than `1024_16` for a practical
  clean-room rerun, and `cam0` matches the single-camera upstream
  `mono_tum_vi` contract.
- Downloaded archive:
  `datasets/public/tum_vi/dataset-room1_512_16.tar`
- Extracted dataset root:
  `datasets/public/tum_vi/dataset-room1_512_16`
- Source metadata actually used from the archive:
  `datasets/public/tum_vi/dataset-room1_512_16/dso/cam0/camera.txt` and
  `datasets/public/tum_vi/dataset-room1_512_16/mav0/cam0/data.csv`
- Materialized calibration:
  `build/tum_vi_room1_512_16/materialized/cam0_calibration.json`
- Materialized frame index:
  `build/tum_vi_room1_512_16/materialized/cam0_frame_index.csv`
- Prepared image directory:
  `build/tum_vi_room1_512_16/monocular/images`
- Prepared timestamps:
  `build/tum_vi_room1_512_16/monocular/timestamps.txt`
- Runtime command:
  `/usr/bin/xvfb-run -a /home/helionaut/workspaces/HEL-67/third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi /home/helionaut/workspaces/HEL-67/third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt /home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/monocular/TUM-VI-room1-512-16-cam0.yaml /home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/monocular/images /home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/monocular/timestamps.txt tum_vi_room1_512_16_cam0`

## Binary Provenance

- Executable:
  `third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi`
- Executable SHA-256:
  `76e6c97296a7b9941ea51f9f6644ac442903d7e941e396d269c085f2effc38f4`
- Shared library:
  `third_party/orbslam3/upstream/lib/libORB_SLAM3.so`
- Shared library SHA-256:
  `39a9aa485752747cba3b21793a1b4c49ca4946abaf86cb956651b51c2133be71`
- Build metadata:
  `.symphony/build-attempts/orbslam3-build-latest.json`
- Build log:
  `.symphony/build-attempts/orbslam3-build-20260320T103009Z.log`
- Build dmesg snapshot:
  `.symphony/build-attempts/orbslam3-build-dmesg-20260320T103009Z.log`

## Summary Metrics

- Clean-room phase result: build passed, runtime failed
- Build exit code: `0`
- Runtime exit code: `134`
- Progress artifact final state: `status=failed`, `phase=10`, `completed=9/10`
- Prepared timestamps: `2821`
- Frame-index rows including header: `2822`
- Trajectory outputs produced: `0`
- First fatal runtime boundary: `New Map created with 375 points`
- Fatal runtime message: `double free or corruption (out)`
- Host debugger availability: none of `gdb`, `valgrind`, `lldb`, `catchsegv`,
  `eu-stack`, or `coredumpctl` were available, and `ulimit -c` was `0`

## Artifact Locations

Local generated evidence:

- `logs/out/tum_vi_room1_512_16_orchestration.log`
- `logs/out/tum_vi_room1_512_16_cam0.log`
- `reports/out/tum_vi_room1_512_16_cam0.md`
- `.symphony/progress/HEL-67.json`
- `.symphony/build-attempts/orbslam3-build-latest.json`
- `.symphony/build-attempts/orbslam3-build-20260320T103009Z.log`
- `.symphony/build-attempts/orbslam3-build-dmesg-20260320T103009Z.log`

Generated inputs retained from the run:

- `build/tum_vi_room1_512_16/materialized/cam0_calibration.json`
- `build/tum_vi_room1_512_16/materialized/cam0_frame_index.csv`
- `build/tum_vi_room1_512_16/monocular/TUM-VI-room1-512-16-cam0.yaml`
- `build/tum_vi_room1_512_16/monocular/images/`
- `build/tum_vi_room1_512_16/monocular/timestamps.txt`

Expected but missing because the runtime aborted:

- `build/tum_vi_room1_512_16/monocular/trajectory/f_tum_vi_room1_512_16_cam0.txt`
- `build/tum_vi_room1_512_16/monocular/trajectory/kf_tum_vi_room1_512_16_cam0.txt`
- `reports/out/tum_vi_room1_512_16_cam0_summary.json`
- `reports/out/tum_vi_room1_512_16_cam0_trajectory.svg`
- `reports/out/tum_vi_room1_512_16_cam0.html`

## Minimal Reproducible Runtime Blocker

The public runtime blocker is already narrower than the compile-only question:

1. Build the pinned upstream checkout with repo-local cmake, Eigen3, OpenCV,
   Boost serialization, and Pangolin prefixes.
2. Materialize the public `dataset-room1_512_16` `cam0` inputs into the repo's
   monocular calibration plus frame-index contract.
3. Run the exact `xvfb-run -a .../Examples/Monocular/mono_tum_vi ...` command
   listed above from `build/tum_vi_room1_512_16/monocular/trajectory`.
4. Observe the runtime log reach:
   `Creation of new map with id: 0`,
   `Creation of new map with last KF id: 0`,
   `New Map created with 375 points`,
   then abort with `double free or corruption (out)`.

This is materially beyond HEL-66's compile-only proof. It shows that the same
upstream monocular lane that compiles on this host still is not able to finish
a public TUM-VI sanity sequence or emit trajectories.

## Acceptance Criteria Check

- Real public run: met. The issue crossed into the actual `mono_tum_vi`
  runtime on the public TUM-VI `room1_512_16` `cam0` sequence.
- Exact dataset path and launch command: met. Both are recorded above and in
  `logs/out/tum_vi_room1_512_16_cam0.log`.
- Binary path and provenance summary: met. Paths, commit, hashes, and build
  metadata are recorded above.
- Logs and reports: met. The orchestration log and the runtime markdown/log
  artifacts were written.
- Trajectory outputs and visual proof: not met because the runtime aborted
  before trajectory generation. The missing paths are recorded explicitly.
- Minimal reproducible blocker if the run fails: met. The failure boundary is
  now a public runtime abort after map initialization, not dataset prep or
  compilation.
