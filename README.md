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
`HEL-41` captures the execution plan, `HEL-43` establishes the harness in this
branch, and later issues will fill in the pinned ORB-SLAM3 baseline, real
fixtures, backlog split, and any publication/deployment path.

## Repository layout

- `configs/`: calibration and ORB-SLAM3 settings bundles
- `datasets/`: shareable fixtures plus local-only user recordings
- `logs/out/`: generated logs
- `reports/out/`: generated validation reports and publishable artifacts
- `scripts/`: runnable harness entrypoints
- `src/splatica_orb_test/`: harness contract helpers
- `tests/`: automated tests
