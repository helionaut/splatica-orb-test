# splatica-orb-test

Research and validation workspace for finding a reproducible ORB-SLAM3
version/configuration that works for a stereo fisheye rig with IMU, then
verifying it on the user's dataset.

## Harness commands

```bash
make build
make smoke
make calibration-smoke
make fetch-tum-rgbd
make fetch-tum-vi
make rgbd-sanity
make tum-vi-sanity
make check
```

- `make build` generates the current dry-run smoke plan in `build/smoke-plan.md`.
- `make smoke` exercises the canonical dry-run launcher path and writes outputs to `logs/out/` and `reports/out/`.
- `make calibration-smoke` generates and validates the checked-in shareable calibration settings bundles for the first monocular baseline.
- `make fetch-tum-rgbd` downloads and extracts the public TUM RGB-D `fr1/xyz` dataset into `datasets/public/`.
- `make fetch-tum-vi` downloads and extracts the public TUM-VI `room1_512_16` dataset into `datasets/public/`.
- `make rgbd-sanity` runs the clean-room public RGB-D sanity lane against upstream `rgbd_tum`.
- `make tum-vi-sanity` runs the clean-room public TUM-VI monocular sanity lane against upstream `mono_tum_vi`.
- `make check` runs tests, build, smoke, calibration-smoke, and normalization as one aggregate validation command.

## Current Project Docs

- [Execution plan](docs/execution-plan.md)
- [Final validation report](docs/final-validation-report.md)
- [TUM RGB-D sanity run report](docs/tum-rgbd-sanity-report.md)
- [HEL-67 public TUM-VI sanity report](docs/reports/hel-67-public-tum-vi-room1-cam0.md)
- [HEL-63 post-initialization abort follow-up](docs/hel-63-post-initialization-abort-follow-up.md)
- [HEL-68 ASan crash follow-up](docs/hel-68-asan-crash-follow-up.md)
- [HEL-69 worktree containment follow-up](docs/hel-69-worktree-containment-follow-up.md)
- [HEL-71 Eigen static-alignment follow-up](docs/hel-71-eigen-static-alignment-follow-up.md)
- [HEL-72 ASan plus no-static-alignment follow-up](docs/hel-72-asan-static-alignment-follow-up.md)
- [HEL-73 private aggressive follow-up](docs/hel-73-private-aggressive-follow-up.md)
- [HEL-74 private ASan leak follow-up](docs/hel-74-private-asan-leak-follow-up.md)
- [HEL-75 public save-path probe follow-up](docs/hel-75-public-save-path-follow-up.md)
- [HEL-76 private save comparison follow-up](docs/hel-76-private-save-comparison-follow-up.md)
- [HEL-77 private save comparison follow-up](docs/hel-77-private-save-comparison-follow-up.md)
- [Dataset normalization](docs/dataset-normalization.md)
- [Calibration translation](docs/calibration-translation.md)
- [Monocular baseline](docs/monocular-baseline.md)
- [Future rig plan](docs/future-rig-plan.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Production verification](docs/PRODUCTION_VERIFICATION.md)
- [Publication decision](docs/publication-decision.md)

## Publication Status

`HEL-64` promotes the first concrete publishable artifact for this repo: the
public TUM RGB-D sanity-run report bundle under
`reports/published/tum_rgbd_fr1_xyz_sanity/`. The deploy target is now a
static GitHub Pages publication of that bundle, while the versioned repo copy
remains the audit source of truth. Use
`make verify-production ARTIFACT_URL=https://<published-artifact-url>` against
the published Pages root after deployment, and record the final URL in the PR
summary plus the Linear handoff/completion comment.

## Current Status

The current repo-level conclusion is captured in
[docs/final-validation-report.md](docs/final-validation-report.md). The
checked-in rerun path is validated through `make check`. A real user-rig run
still remains blocked until the local-only lens-10 inputs are imported into the
current checkout. Pangolin is now part of the documented repo-local bootstrap
flow through `make bootstrap-local-pangolin`, which extracts the required
GL/GLEW/X11 development sysroot and installs a CMake-discoverable Pangolin
prefix under `build/local-tools/pangolin-root/usr/local/`. The repo-local
OpenCV bootstrap now also records its resolved dependency closure so the local
prefix carries the transitive Qt/TBB/media libraries needed by the ORB-SLAM3
example link step. On a host with the imported lens-10 bundle and the repo-local
native toolchain in place, the baseline now executes end-to-end, but the current
user sequence still produces zero keyframes and no saved trajectory artifacts.
The latest follow-up in
[docs/hel-71-eigen-static-alignment-follow-up.md](docs/hel-71-eigen-static-alignment-follow-up.md)
shows that a clean-room public rerun with
`ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1` still crashes at frame `93`
immediately after `New Map created with 375 points`, now as a plain
segmentation fault. That means Eigen static-alignment policy alone is not yet a
safe fix to promote into the canonical lane before the next private rerun. The
current HEL-72 checkpoint in
[docs/hel-72-asan-static-alignment-follow-up.md](docs/hel-72-asan-static-alignment-follow-up.md)
shows the combined public rerun with `ORB_SLAM3_ENABLE_ASAN=1` plus
`ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1` surviving past first-map creation
and continuing well beyond the old frame-93 crash boundary, while the private
aggressive lens-10 baseline remains blocked in this checkout because only the
raw `00.mp4` and `10.mp4` exports are present, not the calibration/extrinsics
sidecars needed to rebuild `datasets/user/insta360_x3_one_lens_baseline/`.
The current HEL-73 follow-up in
[docs/hel-73-private-aggressive-follow-up.md](docs/hel-73-private-aggressive-follow-up.md)
turns that blocker into a dedicated repo entrypoint,
`scripts/run_private_monocular_followup.py`, which now fails fast with an
auditable report and `.symphony/progress/HEL-73.json` until the missing
calibration/extrinsics sidecars are restored.
The current HEL-74 follow-up in
[docs/hel-74-private-asan-leak-follow-up.md](docs/hel-74-private-asan-leak-follow-up.md)
shows that once those sidecars are restored, the private aggressive lane can
run all 270 frames, initialize twice, and reach `SaveTrajectoryEuRoC`, but the
expected frame trajectory is still missing and LeakSanitizer returns non-zero at
shutdown because ORB-SLAM3 leaves large persistent allocations behind.
The current HEL-75 follow-up in
[docs/hel-75-public-save-path-follow-up.md](docs/hel-75-public-save-path-follow-up.md)
shows that the same ASan/no-static-alignment build can still save both frame
and keyframe trajectories on a bounded public monocular fisheye lane, so the
remaining blocker is now private-lane-specific rather than a generic save-path
or working-directory failure. The current HEL-76 follow-up in
[docs/hel-76-private-save-comparison-follow-up.md](docs/hel-76-private-save-comparison-follow-up.md)
turns that conclusion into a dedicated comparison entrypoint,
`scripts/run_private_save_comparison_followup.py`, which reuses the HEL-74
aggressive private lane, records the HEL-75 public save-byte reference in the
repo, auto-discovers the known OpenClaw host paths for the raw videos and
calibration/extrinsics sidecars when the repo-local bundle is absent, and
leaves a blocked report when the current host still lacks the private inputs
needed to rerun the comparison.
The current HEL-77 follow-up in
[docs/hel-77-private-save-comparison-follow-up.md](docs/hel-77-private-save-comparison-follow-up.md)
shows that this host does expose the private exports and sidecars, and that the
repo can materialize the lens-10 bundle plus fetch the pinned ORB-SLAM3
checkout, but the clean workspace is still blocked at `cmake` and the remaining
native dependency lane before any private save-byte comparison can run.

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

## Shareable Calibration Translation Lane

`HEL-47` adds a checked-in calibration bundle at
`configs/calibration/insta360_x3_shareable_rig.json`, committed monocular YAMLs
for lens `10/` and lens `00/`, and a harness-integrated config smoke path at
`manifests/insta360_x3_shareable_calibration_smoke.json`.

Validate that lane from a clean checkout with:

```bash
make calibration-smoke
```

That command regenerates:

- `configs/orbslam3/insta360_x3_lens10_monocular.yaml`
- `configs/orbslam3/insta360_x3_lens00_monocular.yaml`
- `logs/out/insta360_x3_shareable_calibration_smoke.log`
- `reports/out/insta360_x3_shareable_calibration_smoke.md`

The saved report also records the unresolved blockers for any future
stereo+IMU ORB-SLAM3 bundle.

## Monocular Fisheye Lane

`HEL-51` adds the first real run contract for a single Insta360 X3 lens without
IMU. The checked-in manifest is
`manifests/insta360_x3_lens10_monocular_baseline.json`.

`HEL-48` keeps that lane on the official upstream ORB-SLAM3 `master` line,
currently pinned to commit `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`. The
candidate comparison and recommendation memo live in
`docs/candidate-baseline-evaluation.md`.

The baseline flow is:

1. Fetch the pinned ORB-SLAM3 checkout with `./scripts/fetch_orbslam3_baseline.sh`.
   That helper also unpacks `Vocabulary/ORBvoc.txt` from the upstream archive
   so the runtime vocabulary path exists before the full native build.
2. If the host does not provide `cmake`, bootstrap a repo-local copy with
   `make bootstrap-local-cmake`.
3. If the host does not provide `Eigen3`, bootstrap a repo-local prefix with
   `make bootstrap-local-eigen`.
4. If the host does not provide OpenCV 4, bootstrap a repo-local prefix with
   `make bootstrap-local-opencv`.
5. If the host does not provide Boost serialization, bootstrap a repo-local
   prefix with `make bootstrap-local-boost`.
6. If the host does not provide `ffmpeg`/`ffprobe`, bootstrap the pinned
   repo-local media bundle with `make bootstrap-local-ffmpeg`.
7. If the host does not provide Pangolin, bootstrap the repo-local Pangolin
   prefix plus its GL/GLEW/X11 development sysroot with
   `make bootstrap-local-pangolin`.
8. Build the upstream checkout with `./scripts/build_orbslam3_baseline.sh`.
   That wrapper reproduces the upstream native build steps but disables the
   optional `Thirdparty/Sophus` tests/examples, which are not required for
   `mono_tum_vi` and otherwise fail on newer GCC toolchains because upstream
   enables `-Werror`. It now asks CMake for the required `mono_tum_vi` target
   directly instead of blocking on unrelated upstream example binaries.
9. Run `make monocular-prereqs` to confirm that the private lens-10 inputs,
   native build toolchain, and baseline assets are all ready. That command
   writes a saved report to
   `reports/out/insta360_x3_lens10_monocular_prereqs.md` and returns non-zero
   until the lane is actually runnable.
10. Import the provided one-lens raw assets into
   `datasets/user/insta360_x3_one_lens_baseline/` with:
   `./scripts/import_monocular_video_inputs.py --video-00 /path/to/00.mp4 --video-10 /path/to/10.mp4 --calibration-00 /path/to/insta360_x3_kb4_00_calib.txt --calibration-10 /path/to/insta360_x3_kb4_10_calib.txt --extrinsics /path/to/insta360_x3_extr_rigs_calib.json`.
   That helper copies the raw files into a deterministic repo-local layout,
   extracts source PNGs, and generates the per-lens `monocular_calibration.json`,
   `frame_index.csv`, `timestamps.txt`, and `import_manifest.json` files needed
   for the baseline lane.
11. Generate settings plus the timestamp-named image folder with
   `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json --prepare-only`.
12. Execute the actual upstream `mono_tum_vi` runner with
   `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json`.
   The wrapper now auto-injects repo-local OpenCV, Boost, and Pangolin runtime
   library paths, uses `xvfb-run -a` on headless hosts, runs from the trajectory
   output directory so ORB-SLAM3 writes `f_<stem>.txt` and `kf_<stem>.txt`
   correctly, and returns non-zero when the run finishes without trajectory
   artifacts.

The repo still does not include the private calibration or user sequence
payload, so the checked-in automation defines the reproducible contract and
output layout rather than committing user-specific values.

## Public RGB-D Sanity Lane

`HEL-61` adds a clean-room upstream sanity path against the public TUM RGB-D
`fr1/xyz` dataset. The checked-in manifest is
`manifests/tum_rgbd_fr1_xyz_sanity.json`.

Run the full public lane with:

```bash
make rgbd-sanity
```

That command:

1. fetches a fresh upstream ORB-SLAM3 checkout at the pinned commit
2. bootstraps repo-local `cmake`, `Eigen3`, OpenCV, Boost serialization, and
   Pangolin prefixes
3. downloads and extracts the TUM RGB-D `fr1/xyz` archive into
   `datasets/public/tum_rgbd/`
4. builds the upstream `rgbd_tum` target from scratch
5. runs the public sequence with upstream `TUM1.yaml` and the upstream
   `fr1_xyz.txt` association file
6. writes trajectories, logs, a markdown report, an SVG trajectory plot, and a
   visual HTML report under `build/`, `logs/out/`, and `reports/out/`
7. promotes the inspectable published bundle with `make publish-rgbd-sanity`
   under `reports/published/tum_rgbd_fr1_xyz_sanity/`

For the final rerun order, auditable artifacts, and the reference-only
historical paths that are no longer the canonical entrypoint, use
[docs/final-validation-report.md](docs/final-validation-report.md). For the
actual public-run verdict and published artifact paths, use
[docs/tum-rgbd-sanity-report.md](docs/tum-rgbd-sanity-report.md).

## Public TUM-VI Monocular Sanity Lane

`HEL-67` extends the same clean-room baseline proof into the public TUM-VI
`room1_512_16` monocular fisheye lane. The checked-in manifest is
`manifests/tum_vi_room1_512_16_cam0_sanity.json`.

Run the full public lane with:

```bash
make tum-vi-sanity
```

That command:

1. fetches a fresh upstream ORB-SLAM3 checkout at the pinned commit
2. bootstraps repo-local `cmake`, `Eigen3`, OpenCV, Boost serialization, and
   Pangolin prefixes
3. downloads and extracts the public TUM-VI `room1_512_16` archive into
   `datasets/public/tum_vi/`
4. materializes `cam0` into the repo's monocular calibration and frame-index
   contract from `dso/cam0/camera.txt` and `mav0/cam0/data.csv`
5. builds the upstream `mono_tum_vi` target from scratch
6. runs the public sequence under `xvfb-run -a`
7. writes the orchestration log, runtime log, and markdown report under
   `logs/out/`, `reports/out/`, and `.symphony/`

For the final public-run verdict and the exact runtime blocker that remains on
this host, use
[docs/reports/hel-67-public-tum-vi-room1-cam0.md](docs/reports/hel-67-public-tum-vi-room1-cam0.md).

## Repository layout

- `configs/`: calibration and ORB-SLAM3 settings bundles
- `datasets/`: shareable fixtures plus local-only user recordings
- `logs/out/`: generated logs
- `reports/out/`: generated validation reports and publishable artifacts
- `scripts/`: runnable harness entrypoints
- `src/splatica_orb_test/`: harness contract helpers
- `tests/`: automated tests
