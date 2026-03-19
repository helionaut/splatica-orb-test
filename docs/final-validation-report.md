# Final Validation Report

Status: Final
Issue: HEL-49
Last Updated: 2026-03-19

## Final Recommendation

- User rig verdict: `blocked`
- Checked-in repo rerun verdict: `validated`
- Next unresolved risk: the repo now defines the full post-HEL-52 private
  input contract under
  `datasets/user/insta360_x3_one_lens_baseline/`, but a real lens-10 user-rig
  run still requires either the private raw assets under `raw/` to be imported
  or an already prepared `lenses/10/` bundle to be present on the checkout.
  Once those inputs exist, the repo can now bootstrap Pangolin, build
  `Examples/Monocular/mono_tum_vi`, and execute the real monocular lane, but
  the imported lens-10 sequence currently produces zero keyframes and no saved
  trajectory artifacts.
- Next follow-up task: on a host that has the private Insta360 exports, run
  `./scripts/import_monocular_video_inputs.py` into
  `datasets/user/insta360_x3_one_lens_baseline/` if `lenses/10/` is still
  empty, rerun `make monocular-prereqs`, and then execute
  `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json`.
  If the resulting log still reports `Map 0 has 0 KFs`, investigate
  calibration, frame selection, or ORB extractor tuning rather than native
  dependency setup.

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

Private prepared-input contract for the actual user-data run:

- Raw source layout:
  `datasets/user/insta360_x3_one_lens_baseline/raw/video/{00.mp4,10.mp4}` and
  `datasets/user/insta360_x3_one_lens_baseline/raw/calibration/`
- Derived lens-10 bundle consumed by
  `manifests/insta360_x3_lens10_monocular_baseline.json`:
  `datasets/user/insta360_x3_one_lens_baseline/lenses/10/monocular_calibration.json`,
  `datasets/user/insta360_x3_one_lens_baseline/lenses/10/frame_index.csv`,
  `datasets/user/insta360_x3_one_lens_baseline/lenses/10/timestamps.txt`, and
  `datasets/user/insta360_x3_one_lens_baseline/lenses/10/import_manifest.json`
- PNG frame sources referenced by `frame_index.csv` under
  `datasets/user/insta360_x3_one_lens_baseline/lenses/10/source_png/`
- Bundle-level ingest evidence:
  `datasets/user/insta360_x3_one_lens_baseline/reports/ingest_report.md`

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

5. If the host does not already provide OpenCV 4, bootstrap the repo-local prefix:

   ```bash
   make bootstrap-local-opencv
   ```

   The repo-local bootstrap records the resolved package closure in
   `build/local-tools/opencv-root/bootstrap-manifest.txt` so the local OpenCV
   prefix carries the transitive libraries needed by the ORB-SLAM3 example
   link step.

6. If the host does not already provide Boost serialization, bootstrap the repo-local prefix:

   ```bash
   make bootstrap-local-boost
   ```

7. If the host does not already provide `ffmpeg`/`ffprobe`, bootstrap the repo-local media bundle and import the raw one-lens assets:

   ```bash
   make bootstrap-local-ffmpeg
   ./scripts/import_monocular_video_inputs.py \
     --video-00 /path/to/00.mp4 \
     --video-10 /path/to/10.mp4 \
     --calibration-00 /path/to/insta360_x3_kb4_00_calib.txt \
     --calibration-10 /path/to/insta360_x3_kb4_10_calib.txt \
     --extrinsics /path/to/insta360_x3_extr_rigs_calib.json \
     --lenses 10
   ```

   This importer is the post-HEL-52 boundary between raw private inputs and the
   deterministic prepared bundle. A successful import writes the derived
   `lenses/10/` files plus
   `datasets/user/insta360_x3_one_lens_baseline/reports/ingest_report.md`.

8. If the host does not already provide Pangolin, bootstrap the repo-local
   Pangolin prefix:

   ```bash
   make bootstrap-local-pangolin
   ```

9. Build the selected ORB-SLAM3 baseline:

   ```bash
   ./scripts/build_orbslam3_baseline.sh
   ```

   The wrapper builds the pinned baseline components plus the required
   `mono_tum_vi` target instead of the whole upstream example tree, and applies
   a local guard so empty-keyframe runs skip trajectory-save segfaults and
   leave a clean log/report trail.

10. Check whether the private monocular lane is actually runnable:

   ```bash
   make monocular-prereqs
   ```

   This writes `reports/out/insta360_x3_lens10_monocular_prereqs.md` and
   returns non-zero until the host and local-only lens-10 inputs are ready.

11. Once `make monocular-prereqs` reports full readiness, prepare the timestamped
   image folder and settings bundle:

   ```bash
   ./scripts/run_orbslam3_sequence.sh \
     --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
     --prepare-only
   ```

12. Execute the selected baseline:

   ```bash
   ./scripts/run_orbslam3_sequence.sh \
     --manifest manifests/insta360_x3_lens10_monocular_baseline.json
   ```

   The wrapper now runs ORB-SLAM3 from the configured trajectory output
   directory, passes the basename `insta360_x3_lens10` to upstream, and exits
   non-zero when the process returns without `f_insta360_x3_lens10.txt` and
   `kf_insta360_x3_lens10.txt`.

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
- `build/insta360_x3_lens10/monocular/trajectory/f_insta360_x3_lens10.txt`
- `build/insta360_x3_lens10/monocular/trajectory/kf_insta360_x3_lens10.txt`
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
- `make bootstrap-local-ffmpeg`
  - Result: passed
  - Observed: bootstrapped repo-local `ffmpeg` and `ffprobe` under
    `build/local-tools/ffmpeg-root/`
- `./scripts/import_monocular_video_inputs.py --lenses 10`
  - Result: passed
  - Observed: copied raw assets into
    `datasets/user/insta360_x3_one_lens_baseline/`, extracted 270 lens-10 PNGs,
    and generated `monocular_calibration.json`, `frame_index.csv`,
    `timestamps.txt`, and `import_manifest.json` under
    `datasets/user/insta360_x3_one_lens_baseline/lenses/10/`
- `make monocular-prereqs`
  - Result: failed as expected and wrote
    `reports/out/insta360_x3_lens10_monocular_prereqs.md`
  - Observed: `Ready for --prepare-only: true`
- `make bootstrap-local-opencv`
  - Result: passed
  - Observed: bootstrapped repo-local OpenCV under
    `build/local-tools/opencv-root/usr/`
- `make bootstrap-local-boost`
  - Result: passed
  - Observed: bootstrapped repo-local Boost serialization under
    `build/local-tools/boost-root/usr/`
- `./scripts/build_orbslam3_baseline.sh`
  - Result: failed as expected on this host
  - Observed: completed `Thirdparty/DBoW2`, `Thirdparty/g2o`, and
    `Thirdparty/Sophus`, then stopped at top-level ORB-SLAM3 configure because
    `find_package(Pangolin REQUIRED)` could not resolve `PangolinConfig.cmake`
- `apt-cache search '^libpangolin'`
  - Result: returned no package on Ubuntu `noble`

Revalidated from the current `main` checkout on 2026-03-18 after HEL-54 landed
(`1b51f7c786572a99e314c022a5cb511b0e6f88df`):

- `make test`
  - Result: passed
- `make check`
  - Result: passed
- `./scripts/fetch_orbslam3_baseline.sh`
  - Result: passed
  - Observed: confirmed `third_party/orbslam3/upstream/` at
    `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4` with
    `Vocabulary/ORBvoc.txt` present
- `make monocular-prereqs`
  - Result: failed as expected and refreshed
    `reports/out/insta360_x3_lens10_monocular_prereqs.md`
  - Observed: a fresh checkout still lacks the local-only one-lens input
    bundle under `datasets/user/insta360_x3_one_lens_baseline/raw/` and
    `datasets/user/insta360_x3_one_lens_baseline/lenses/10/`, plus native
    `cmake`, `Eigen3`, OpenCV, Boost serialization, Pangolin, and the built
    `mono_tum_vi` runner

Executed on 2026-03-19 from the HEL-56 worktree on a host that already had the
private lens-10 bundle plus repo-local Pangolin/OpenCV/Boost support available:

- `make test`
  - Result: passed
- `./scripts/build_orbslam3_baseline.sh`
  - Result: passed
  - Observed: built `Examples/Monocular/mono_tum_vi` with the repo-local
    Pangolin, OpenCV, Boost, and `cmake` fallbacks, plus a local ORB-SLAM3
    patch that turns empty-keyframe shutdown crashes into logged no-op saves
- `make monocular-prereqs`
  - Result: passed
  - Observed: refreshed
    `reports/out/insta360_x3_lens10_monocular_prereqs.md` with
    `Ready for --prepare-only: true` and `Ready for full execution: true`
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json`
  - Result: failed with auditable evidence and refreshed
    `logs/out/insta360_x3_lens10_monocular.log` plus
    `reports/out/insta360_x3_lens10_monocular.md`
  - Observed: the wrapper launched the real `mono_tum_vi` binary under
    `xvfb-run -a`, ORB-SLAM3 loaded the generated YAML and 270 prepared frames,
    the atlas reached shutdown with `Map 0 has 0 KFs`, and the process wrote no
    frame/keyframe trajectory files. The wrapper therefore returned exit code
    `2` even though the upstream process returned `0`.

## What Worked

- The repo has one pinned ORB-SLAM3 baseline, one checked-in monocular
  manifest, one shareable calibration bundle, and one checked-in stereo+IMU
  normalization contract.
- `HEL-52` replaced the old ad hoc private-user lane with one deterministic
  one-lens bundle rooted at `datasets/user/insta360_x3_one_lens_baseline/`,
  including raw private inputs under `raw/`, derived runnable lens bundles
  under `lenses/`, per-lens `import_manifest.json`, and a bundle-level
  `reports/ingest_report.md`.
- `make check` is the canonical fresh-checkout validation gate for the
  checked-in repo state.
- `scripts/fetch_orbslam3_baseline.sh` is the one supported way to materialize
  the upstream baseline checkout at the selected commit and extract
  `Vocabulary/ORBvoc.txt` before the native build.
- `make monocular-prereqs` is the one supported way to prove whether the real
  monocular run can proceed; it saves the missing/ready state into a report
  instead of leaving that knowledge implicit.
- The repo now has one documented native bootstrap lane for Pangolin,
  OpenCV, Boost serialization, and the ORB-SLAM3 runtime environment. On the
  HEL-56 host that lane built `mono_tum_vi`, made `make monocular-prereqs`
  report full readiness, and executed the real user-rig command without hidden
  manual steps.
- The real monocular wrapper now leaves behind an auditable report even when
  ORB-SLAM3 fails to produce a savable trajectory. It records the working
  directory, expected `f_*.txt` and `kf_*.txt` outputs, raw process exit code,
  and the synthetic failure when those artifacts are missing.

## What Failed Or Remains Blocked

- A fresh checkout that does not have the private raw exports under
  `datasets/user/insta360_x3_one_lens_baseline/raw/` or an already prepared
  `datasets/user/insta360_x3_one_lens_baseline/lenses/10/` bundle still cannot
  claim a successful user-rig run. The repo now documents that contract
  explicitly; it just does not publish the user files themselves.
- On the HEL-56 host, native setup is no longer the next blocker. After the raw
  import plus repo-local `cmake`, `Eigen3`, OpenCV, Boost serialization, and
  Pangolin bootstraps, the lane builds and launches `mono_tum_vi`, but the
  imported lens-10 user sequence still fails to initialize a track. The final
  log shows `Map 0 has 0 KFs`, and both expected trajectory outputs remain
  absent.
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

If another engineer needs the current recommended path, use the canonical rerun
sequence in this document and ignore the historical comparison manifests unless
they are intentionally re-opening baseline selection.
