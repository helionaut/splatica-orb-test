# Development

## Golden path

1. Read the current project scope in `README.md`, `docs/execution-plan.md`, and `docs/PRD.md` when product requirements change.
2. Generate the current dry-run build artifact with `make build`.
3. Exercise the smoke-run path with `make smoke`.
4. Run the aggregate validation gate with `make check`.

## Commands

- `make build`: render the current smoke plan into `build/smoke-plan.md`.
- `make smoke`: run the dry-run ORB-SLAM3 lane and write smoke outputs under `logs/out/` and `reports/out/`.
- `make test`: run the repository tests.
- `make check`: run tests, build, and smoke together.
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
