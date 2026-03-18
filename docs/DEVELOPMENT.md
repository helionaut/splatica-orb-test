# Development

## Golden path

1. Read the current project scope in `README.md`, `docs/execution-plan.md`, and `docs/PRD.md` when product requirements change.
2. Generate the current dry-run build artifact with `make build`.
3. Exercise the smoke-run path with `make smoke`.
4. Exercise the dataset normalization path with `make normalize-fixture`.
5. Run the aggregate validation gate with `make check`.

## Commands

- `make build`: render the current smoke plan into `build/smoke-plan.md`.
- `make smoke`: run the dry-run ORB-SLAM3 lane and write smoke outputs under `logs/out/` and `reports/out/`.
- `make normalize-fixture`: normalize the checked-in stereo+IMU fixture into `build/fixtures/stereo_imu_fixture/normalized/` and write a report to `reports/out/stereo_imu_fixture_normalization.md`.
- `make test`: run the repository tests.
- `make check`: run tests, build, smoke, and fixture normalization together.
- `./scripts/fetch_orbslam3_baseline.sh`: clone the pinned ORB-SLAM3 upstream baseline into `third_party/orbslam3/upstream`.
- `./scripts/build_orbslam3_baseline.sh`: run upstream `build.sh` inside the pinned checkout so `Examples/Monocular/mono_tum_vi` exists. This requires local build tools such as `cmake` and `make`.
- `./scripts/prepare_stereo_imu_sequence.py --manifest manifests/stereo_imu_fixture_normalization.json`: normalize one raw stereo+IMU sequence into the canonical output layout defined in `docs/dataset-normalization.md`.
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
