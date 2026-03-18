# splatica-orb-test

Research and validation workspace for finding a reproducible ORB-SLAM3
version/configuration that works for a stereo fisheye rig with IMU, then
verifying it on the user's dataset.

## Harness commands

```bash
make build
make smoke
make check
```

- `make build` generates the current dry-run smoke plan in `build/smoke-plan.md`.
- `make smoke` exercises the canonical dry-run launcher path and writes outputs to `logs/out/` and `reports/out/`.
- `make check` runs tests, build, and smoke as one aggregate validation command.

## Current Project Docs

- [Execution plan](docs/execution-plan.md)
- [Dataset normalization](docs/dataset-normalization.md)
- [Monocular baseline](docs/monocular-baseline.md)
- [Future rig plan](docs/future-rig-plan.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Production verification](docs/PRODUCTION_VERIFICATION.md)
- [Publication decision](docs/publication-decision.md)

## Publication Status

`splatica-orb-test` does not currently publish a live artifact or site.
`HEL-45` records the explicit no-deploy decision in
[docs/publication-decision.md](docs/publication-decision.md). The current
harness only produces local dry-run plans, logs, and reports. When a real
validation bundle or report exists, prefer a downloadable results bundle,
verify its published URL with
`make verify-production ARTIFACT_URL=https://<published-artifact-url>`, and
record that final location in both the PR summary and the Linear handoff or
completion comment.

## Current Focus

The repository is moving from intake into a reproducible engineering lane.
`HEL-41` captures the execution plan, `HEL-43` establishes the harness,
`HEL-46` defines the canonical stereo+IMU normalization lane, and `HEL-51`
adds the first real monocular baseline. Later issues will fill in the pinned
ORB-SLAM3 baseline, user-data validation, and any publication/deployment path.

## Stereo + IMU Normalization Lane

`HEL-46` adds the one supported raw-input and normalized-output contract for
stereo fisheye plus IMU sequences. The checked-in fixture manifest is
`manifests/stereo_imu_fixture_normalization.json`.

Validate the import path from a clean checkout with:

```bash
make normalize-fixture
```

That command normalizes the checked-in raw fixture into
`build/fixtures/stereo_imu_fixture/normalized/` and writes a saved report to
`reports/out/stereo_imu_fixture_normalization.md`.

## Monocular Fisheye Lane

`HEL-51` adds the first real run contract for a single Insta360 X3 lens without
IMU. The checked-in manifest is
`manifests/insta360_x3_lens10_monocular_baseline.json`.

The baseline flow is:

1. Fetch the pinned ORB-SLAM3 checkout with `./scripts/fetch_orbslam3_baseline.sh`.
2. Build the upstream checkout with `./scripts/build_orbslam3_baseline.sh`.
3. Place the private lens-10 calibration JSON and frame index CSV under
   `datasets/user/insta360_x3_lens10/`.
4. Generate settings plus the timestamp-named image folder with
   `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json --prepare-only`.
5. Execute the actual upstream `mono_tum_vi` runner with
   `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json`.

The repo still does not include the private calibration or user sequence
payload, so the checked-in automation defines the reproducible contract and
output layout rather than committing user-specific values.

## Repository layout

- `configs/`: calibration and ORB-SLAM3 settings bundles
- `datasets/`: shareable fixtures plus local-only user recordings
- `logs/out/`: generated logs
- `reports/out/`: generated validation reports and publishable artifacts
- `scripts/`: runnable harness entrypoints
- `src/splatica_orb_test/`: harness contract helpers
- `tests/`: automated tests
