# Final Validation Report

Status: Final
Issue: HEL-49
Last Updated: 2026-03-18

## Final Recommendation

- User rig verdict: `blocked`
- Checked-in repo rerun verdict: `validated`
- Next unresolved risk: the selected lens-10 monocular lane still cannot run on
  the user's rig until `datasets/user/insta360_x3_lens10/monocular_calibration.json`
  and `datasets/user/insta360_x3_lens10/frame_index.csv` are supplied on a host
  that can build ORB-SLAM3 with CMake-discoverable OpenCV and Pangolin.

The repo now has one documented rerun path for the selected baseline and one
final conclusion. Another engineer should start here instead of rediscovering
the lane from old issue branches or generated reports.

## Selected Baseline And Config Bundle

- ORB-SLAM3 source baseline: `https://github.com/UZ-SLAMLab/ORB_SLAM3`
- Pinned branch: `master`
- Pinned commit: `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
- Canonical manifest: `manifests/insta360_x3_lens10_monocular_baseline.json`
- Launch wrapper: `scripts/run_orbslam3_sequence.sh`
- Generated monocular settings path:
  `build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml`
- Baseline output report path: `reports/out/insta360_x3_lens10_monocular.md`
- Baseline output log path: `logs/out/insta360_x3_lens10_monocular.log`

Supporting checked-in inputs and contracts:

- Shareable calibration bundle:
  `configs/calibration/insta360_x3_shareable_rig.json`
- Checked-in monocular YAML references:
  `configs/orbslam3/insta360_x3_lens10_monocular.yaml` and
  `configs/orbslam3/insta360_x3_lens00_monocular.yaml`
- Shareable stereo+IMU normalization manifest:
  `manifests/stereo_imu_fixture_normalization.json`
- Selected monocular baseline rationale:
  [candidate-baseline-evaluation.md](candidate-baseline-evaluation.md)

Private, local-only inputs still required for the actual user-data run:

- `datasets/user/insta360_x3_lens10/monocular_calibration.json`
- `datasets/user/insta360_x3_lens10/frame_index.csv`
- PNG frames referenced by `frame_index.csv`

## Canonical Rerun Path

Start from a fresh checkout of this repo. Run the steps in this order.

1. Validate the checked-in reproducibility lane:

   ```bash
   make check
   ```

   This proves the versioned repo state still reproduces:

   - the dry-run harness plan and smoke report
   - the shareable calibration translation smoke report
   - the checked-in stereo+IMU fixture normalization report

2. Fetch the pinned ORB-SLAM3 checkout and extract the upstream vocabulary:

   ```bash
   ./scripts/fetch_orbslam3_baseline.sh
   ```

3. If the host does not already provide `cmake`, bootstrap the repo-local copy:

   ```bash
   make bootstrap-local-cmake
   ```

4. If the host does not already provide `Eigen3`, bootstrap the repo-local prefix:

   ```bash
   make bootstrap-local-eigen
   ```

5. Build the selected ORB-SLAM3 baseline:

   ```bash
   ./scripts/build_orbslam3_baseline.sh
   ```

6. Check whether the private monocular lane is actually runnable:

   ```bash
   make monocular-prereqs
   ```

   This writes `reports/out/insta360_x3_lens10_monocular_prereqs.md` and
   returns non-zero until the host and local-only lens-10 inputs are ready.

7. Once `make monocular-prereqs` reports full readiness, prepare the timestamped
   image folder and settings bundle:

   ```bash
   ./scripts/run_orbslam3_sequence.sh \
     --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
     --prepare-only
   ```

8. Execute the selected baseline:

   ```bash
   ./scripts/run_orbslam3_sequence.sh \
     --manifest manifests/insta360_x3_lens10_monocular_baseline.json
   ```

There are no hidden manual rename or cleanup steps in the supported lane. The
private run depends only on the documented input files, the pinned upstream
checkout, and the native build dependencies called out above.

## Auditable Artifacts

Checked-in or regenerated evidence for the validated repo lane:

- `build/smoke-plan.md`
- `logs/out/fixture-dry-run.log`
- `reports/out/fixture-dry-run.md`
- `logs/out/insta360_x3_shareable_calibration_smoke.log`
- `reports/out/insta360_x3_shareable_calibration_smoke.md`
- `build/fixtures/stereo_imu_fixture/normalized/`
- `reports/out/stereo_imu_fixture_normalization.md`

Artifacts for the selected monocular baseline lane once the host is ready:

- `third_party/orbslam3/upstream/`
- `reports/out/insta360_x3_lens10_monocular_prereqs.md`
- `build/insta360_x3_lens10/monocular/images/`
- `build/insta360_x3_lens10/monocular/timestamps.txt`
- `build/insta360_x3_lens10/monocular/trajectory/insta360_x3_lens10*`
- `logs/out/insta360_x3_lens10_monocular.log`
- `reports/out/insta360_x3_lens10_monocular.md`

## Fresh Validation Evidence

Fresh rerun pass executed on 2026-03-18 from a new `HEL-49` worktree created at
`origin/main`, before any hidden local setup was assumed.

- `make test`
  - Result: passed
- `make check`
  - Result: passed
  - Regenerated: `build/smoke-plan.md`,
    `logs/out/fixture-dry-run.log`, `reports/out/fixture-dry-run.md`,
    `logs/out/insta360_x3_shareable_calibration_smoke.log`,
    `reports/out/insta360_x3_shareable_calibration_smoke.md`,
    `build/fixtures/stereo_imu_fixture/normalized/`,
    `reports/out/stereo_imu_fixture_normalization.md`
- `./scripts/fetch_orbslam3_baseline.sh`
  - Result: passed
  - Observed: checked out `third_party/orbslam3/upstream/` at
    `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4` and extracted
    `Vocabulary/ORBvoc.txt`
- `make bootstrap-local-cmake`
  - Result: passed
  - Observed: bootstrapped repo-local `cmake` under
    `build/local-tools/cmake-root/usr/`
- `make bootstrap-local-eigen`
  - Result: passed
  - Observed: bootstrapped repo-local `Eigen3` under
    `build/local-tools/eigen-root/usr/`
- `./scripts/build_orbslam3_baseline.sh`
  - Result: failed as expected on this host
  - Observed blocker: `Thirdparty/DBoW2` configuration stopped with
    `OpenCV > 3.0 not found.`
- `make monocular-prereqs`
  - Result: failed as expected and wrote
    `reports/out/insta360_x3_lens10_monocular_prereqs.md`
  - Observed blockers: missing private `monocular_calibration.json`,
    missing private `frame_index.csv`, missing OpenCV, missing Pangolin, and
    missing built `Examples/Monocular/mono_tum_vi`

## What Worked

- The repo has one pinned ORB-SLAM3 baseline, one checked-in monocular
  manifest, one shareable calibration bundle, and one checked-in stereo+IMU
  normalization contract.
- `make check` is the canonical fresh-checkout validation gate for the
  checked-in repo state.
- `scripts/fetch_orbslam3_baseline.sh` is the one supported way to materialize
  the upstream baseline checkout at the selected commit and extract
  `Vocabulary/ORBvoc.txt` before the native build.
- `make monocular-prereqs` is the one supported way to prove whether the real
  monocular run can proceed; it saves the missing/ready state into a report
  instead of leaving that knowledge implicit.

## What Failed Or Remains Blocked

- The repo still cannot claim a successful user-rig run, because the private
  lens-10 calibration JSON, frame index CSV, and referenced PNG frames are not
  versioned in this repo.
- The host must expose CMake-discoverable OpenCV and Pangolin development
  packages before `./scripts/build_orbslam3_baseline.sh` can produce the real
  `Examples/Monocular/mono_tum_vi` executable.
- Full stereo+IMU validation remains blocked beyond this monocular lane because
  the shareable calibration subset still lacks `camera_to_imu`, IMU noise, IMU
  walk, IMU frequency, and overlapping-stereo geometry required for a credible
  ORB-SLAM3 stereo-inertial settings bundle.
- The user's acceptance target for dataset quality is still unspecified, so
  even a successful future run would count only as a technical validation pass
  until that target is defined.

## Reference-Only Paths

The following files stay in the repo as audit history, not as alternate rerun
lanes:

- `manifests/smoke-run.json`: legacy harness dry-run path for the HEL-43 smoke
  scaffold.
- `manifests/insta360_x3_lens10_upstream_v1_0_release_evaluation.json`:
  HEL-48 comparison manifest for the older upstream tag.
- `manifests/insta360_x3_lens10_openmavis_master_evaluation.json`:
  HEL-48 comparison manifest for the OpenMAVIS fork.

If another engineer needs the current recommended path, use the eight-step
sequence in this document and ignore the historical comparison manifests unless
they are intentionally re-opening baseline selection.
