# Development

For the current operator entrypoint, rerun order, and final repo or user-rig
verdict, start with [final-validation-report.md](final-validation-report.md).
This file remains the command reference.

## Golden path

1. Read the current project scope in `README.md`, `docs/execution-plan.md`, and `docs/PRD.md` when product requirements change.
2. Generate the current dry-run build artifact with `make build`.
3. Exercise the smoke-run path with `make smoke`.
4. Exercise the checked-in calibration translation path with `make calibration-smoke`.
5. Exercise the dataset normalization path with `make normalize-fixture`.
6. Run the aggregate validation gate with `make check`.

## Commands

- `make build`: render the current smoke plan into `build/smoke-plan.md`.
- `make smoke`: run the dry-run ORB-SLAM3 lane and write smoke outputs under `logs/out/` and `reports/out/`.
- `make calibration-smoke`: regenerate and validate the checked-in shareable calibration settings bundle plus saved smoke log/report.
- `make bootstrap-local-cmake`: extract Ubuntu `cmake` packages plus their runtime libraries into `build/local-tools/cmake-root/` so the repo can run the upstream build helper without system-wide install privileges.
- `make bootstrap-local-eigen`: extract the Ubuntu `libeigen3-dev` package into `build/local-tools/eigen-root/` so the repo can satisfy `Eigen3` without a system-wide install.
- `make monocular-prereqs`: check whether the private lens-10 inputs, fetched baseline checkout, extracted vocabulary, built executable, and native packages are ready for the real monocular run. The command writes `reports/out/insta360_x3_lens10_monocular_prereqs.md` and exits non-zero while blockers remain.
- `make normalize-fixture`: normalize the checked-in stereo+IMU fixture into `build/fixtures/stereo_imu_fixture/normalized/` and write a report to `reports/out/stereo_imu_fixture_normalization.md`.
- `make test`: run the repository tests.
- `make check`: run tests, build, smoke, calibration-smoke, and fixture normalization together.
- `./scripts/fetch_orbslam3_baseline.sh`: clone the pinned ORB-SLAM3 upstream baseline into `third_party/orbslam3/upstream` and unpack `Vocabulary/ORBvoc.txt` from the upstream archive so the runtime vocabulary path exists before the full native build.
- `./scripts/bootstrap_local_cmake.sh`: extract a repo-local `cmake` toolchain from Ubuntu packages into `build/local-tools/cmake-root/`. `./scripts/build_orbslam3_baseline.sh` will use that fallback automatically if `cmake` is not available on `PATH`.
- `./scripts/bootstrap_local_eigen.sh`: extract a repo-local `Eigen3` prefix from Ubuntu packages into `build/local-tools/eigen-root/`. `./scripts/build_orbslam3_baseline.sh` will add that prefix to `CMAKE_PREFIX_PATH` automatically if present.
- `./scripts/extract_orbslam3_vocabulary.py --checkout-dir third_party/orbslam3/upstream`: unpack `Vocabulary/ORBvoc.txt` directly if a checkout already exists but the vocabulary text file has not been materialized yet.
- `./scripts/build_orbslam3_baseline.sh`: run the pinned ORB-SLAM3 native build sequence so `Examples/Monocular/mono_tum_vi` exists. The wrapper keeps the upstream component order, automatically reuses repo-local `cmake` and `Eigen3` fallbacks, and disables optional `Thirdparty/Sophus` tests/examples because they are not required for `mono_tum_vi` and fail under newer GCC releases when upstream `-Werror` is enabled. This still requires local build tools such as `make`, plus CMake-discoverable OpenCV and Pangolin.
- `./scripts/check_monocular_baseline_prereqs.py --manifest manifests/insta360_x3_lens10_monocular_baseline.json --report reports/out/insta360_x3_lens10_monocular_prereqs.md`: generate a saved readiness report for the private lens-10 monocular lane and fail fast if the environment still cannot execute the real baseline.
- `./scripts/prepare_stereo_imu_sequence.py --manifest manifests/stereo_imu_fixture_normalization.json`: normalize one raw stereo+IMU sequence into the canonical output layout defined in `docs/dataset-normalization.md`.
- `./scripts/render_shareable_calibration_settings.py --calibration configs/calibration/insta360_x3_shareable_rig.json --lens 10 --fps 30 --color-order RGB --output configs/orbslam3/insta360_x3_lens10_monocular.yaml`: render one committed shareable monocular settings file directly.
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_shareable_calibration_smoke.json`: regenerate both committed shareable monocular YAMLs and save the config-smoke evidence.
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json --prepare-only`: turn the private monocular calibration plus frame index into a runnable settings file and timestamp-named image folder.
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json`: execute the real upstream `mono_tum_vi` runner once the baseline checkout and private inputs exist.
- `make verify-production ARTIFACT_URL=https://<published-artifact-url>`: verify a published report or results bundle once deployment exists.

## Test-first rule

Behavior changes should begin with a failing test in `tests/`, or land with the implementation in the same change if the behavior is new. Keep tests mirrored against the code and docs they protect so it is obvious where future expectations belong.

## Repository layout

- `configs/calibration/`: camera and IMU calibration inputs.
- `configs/orbslam3/`: ORB-SLAM3 settings bundles.
- `datasets/fixtures/`: small shareable smoke fixtures.
- `datasets/user/`: local-only user datasets and larger recordings.
- `docs/`: design, scope, and operator docs.
- `logs/out/`: generated logs from dry-runs and future real runs.
- `reports/out/`: generated validation reports and publishable results artifacts.
- `scripts/`: runnable entrypoints and verification helpers.
- `src/splatica_orb_test/`: Python helpers that define the harness contract.
- `tests/`: automated tests for harness behavior and expectations.
- `third_party/orbslam3/`: the future pinned upstream ORB-SLAM3 checkout or vendored baseline.
