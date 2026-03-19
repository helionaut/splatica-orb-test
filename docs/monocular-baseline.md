# Monocular Baseline

Status: Draft
Issue: HEL-51
Last Updated: 2026-03-19

For the final rerun order and the current blocked or validated conclusion for
this lane, see [final-validation-report.md](final-validation-report.md).

## Goal

Run the first real ORB-SLAM3 lane against a single Insta360 X3 lens without
IMU so the project can validate calibration translation, preprocessing, and
baseline source selection before attempting the full back-to-back rig.

## Baseline Choice

- Upstream repo: `https://github.com/UZ-SLAMLab/ORB_SLAM3`
- Pinned branch: `master`
- Pinned commit: `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
- Executable path: `Examples/Monocular/mono_tum_vi`
- Vocabulary path: `Vocabulary/ORBvoc.txt`

This baseline was chosen because the official ORB-SLAM3 upstream still ships a
documented monocular fisheye path for TUM-VI without IMU. `HEL-48` checked the
current upstream `master` against the old `v1.0-release` tag and found that
`master` is only two documentation commits ahead, so selecting `master` keeps
the project on the explicit upstream line requested for later tuning work while
remaining code-equivalent to the old release tag. That makes it the smallest
change from a documented upstream lane while still matching the immediate need:
one fisheye lens, offline replay, and no inertial dependence.

## Private Input Contract

The repo does not commit the user's calibration or recordings. `HEL-52`
organizes the local-only bundle under:

```text
datasets/user/insta360_x3_one_lens_baseline/
  raw/
    video/{00.mp4,10.mp4}
    calibration/
      insta360_x3_kb4_00_calib.txt
      insta360_x3_kb4_10_calib.txt
      insta360_x3_extr_rigs_calib.json
  lenses/
    00/
      source_png/*.png
      frame_index.csv
      timestamps.txt
      monocular_calibration.json
      import_manifest.json
    10/
      source_png/*.png
      frame_index.csv
      timestamps.txt
      monocular_calibration.json
      import_manifest.json
  reports/
    ingest_report.md
```

The lens-10 baseline manifest consumes:

- `datasets/user/insta360_x3_one_lens_baseline/lenses/10/monocular_calibration.json`
- `datasets/user/insta360_x3_one_lens_baseline/lenses/10/frame_index.csv`
- PNG source frames referenced by that `frame_index.csv`

`monocular_calibration.json` must provide:

- `camera.label`
- `camera.model` set to `KannalaBrandt8` or a source `kannalabrandt4` variant
- `camera.image_width`
- `camera.image_height`
- `camera.fps`
- `camera.color_order`
- `camera.intrinsics.{fx,fy,cx,cy}`
- `camera.distortion.{k1,k2,k3,k4}`

Optional `orb` and `viewer` blocks can override the default upstream TUM-VI
extractor and viewer parameters.

`frame_index.csv` must use the exact header:

```text
timestamp_ns,source_path
```

Each row points at one PNG frame. The preparation step copies those frames into
`build/insta360_x3_lens10/monocular/images/` and renames them to
`<timestamp_ns>.png` so they match the upstream `mono_tum_vi` loader contract.

## Commands

Fetch the pinned baseline:

```bash
./scripts/fetch_orbslam3_baseline.sh
./scripts/bootstrap_local_cmake.sh
./scripts/bootstrap_local_eigen.sh
./scripts/bootstrap_local_opencv.sh
./scripts/bootstrap_local_boost.sh
./scripts/bootstrap_local_pangolin.sh
./scripts/build_orbslam3_baseline.sh
```

The build helper assumes `make` exists on the host. If `cmake` is not already
installed system-wide, the local bootstrap helper extracts a repo-local copy
under `build/local-tools/cmake-root/`, and the build helper will reuse it
automatically. If `Eigen3` is also absent, the local bootstrap helper extracts
`libeigen3-dev` into `build/local-tools/eigen-root/`, and the build helper adds
that prefix automatically through `CMAKE_PREFIX_PATH`. If OpenCV 4 is absent,
the local bootstrap helper extracts the Ubuntu OpenCV 4 dev/runtime package set
plus its transitive dependency closure into `build/local-tools/opencv-root/`,
and the build helper plus `make monocular-prereqs` will reuse that prefix
automatically. If Boost
serialization is absent, the local bootstrap helper extracts the required
headers/libs into `build/local-tools/boost-root/`, and the build helper plus
`make monocular-prereqs` will reuse that prefix automatically.
The wrapper now runs the ORB-SLAM3 component builds directly instead of
delegating to upstream `build.sh`, so it can disable optional Sophus
tests/examples that are not needed for `mono_tum_vi` and otherwise fail on
newer GCC toolchains because upstream enables `-Werror`. It also asks CMake for
the required `mono_tum_vi` target directly instead of blocking on unrelated
upstream example binaries. The build wrapper also patches the upstream
trajectory-save path so an empty-keyframe monocular run reports a clean failure
instead of segfaulting during shutdown.
The fetch helper already unpacks `Vocabulary/ORBvoc.txt` from the upstream
archive, so a missing extracted vocabulary file after fetch is now a concrete
baseline checkout problem rather than an expected pre-build state.
`./scripts/bootstrap_local_pangolin.sh` now bootstraps Pangolin `v0.8` into
`build/local-tools/pangolin-root/usr/local/` and also extracts the required
GL/GLEW/X11 development packages into
`build/local-tools/pangolin-root/sysroot/usr/`. The helper reuses the repo-local
`cmake` and `Eigen3` fallbacks when needed, disables optional Pangolin
examples/tools/backends that the ORB-SLAM3 viewer path does not need, and adds
`-include cstdint` so Pangolin still compiles under Ubuntu `noble`'s GCC 13
toolchain.

Check whether the lane is actually ready before the first private run:

```bash
make monocular-prereqs
```

That command writes `reports/out/insta360_x3_lens10_monocular_prereqs.md` and
returns non-zero until the private calibration, frame index, native build
packages, extracted vocabulary, and built `mono_tum_vi` binary all exist. As
of HEL-56, the same report now points directly at
`make bootstrap-local-pangolin` when Pangolin is still missing, and the
supported rerun order includes the repo-local Pangolin bootstrap alongside the
earlier `cmake`, `Eigen3`, OpenCV, and Boost serialization fallbacks.

Import the provided mp4 and raw calibration assets into the deterministic local
bundle:

```bash
make bootstrap-local-ffmpeg
./scripts/import_monocular_video_inputs.py \
  --video-00 /path/to/00.mp4 \
  --video-10 /path/to/10.mp4 \
  --calibration-00 /path/to/insta360_x3_kb4_00_calib.txt \
  --calibration-10 /path/to/insta360_x3_kb4_10_calib.txt \
  --extrinsics /path/to/insta360_x3_extr_rigs_calib.json
```

The importer copies the raw assets into `datasets/user/insta360_x3_one_lens_baseline/`,
extracts source PNGs for both lenses with `ffmpeg`, uses `ffprobe` timestamps
to generate `frame_index.csv` and `timestamps.txt`, derives
`monocular_calibration.json` for each lens from the raw `kb4` export plus the
probed mp4 metadata, and writes one `import_manifest.json` per lens plus a
bundle-level `reports/ingest_report.md`.

The importer defaults `camera.color_order` to `BGR` because ORB-SLAM3 reads the
extracted PNG files through OpenCV's default BGR image loader path.

Generate the settings YAML directly:

```bash
./scripts/render_monocular_settings.py \
  --calibration datasets/user/insta360_x3_one_lens_baseline/lenses/10/monocular_calibration.json \
  --output build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml
```

Normalize the frame list directly:

```bash
./scripts/prepare_monocular_sequence.py \
  --frame-index datasets/user/insta360_x3_one_lens_baseline/lenses/10/frame_index.csv \
  --image-dir build/insta360_x3_lens10/monocular/images \
  --timestamps-path build/insta360_x3_lens10/monocular/timestamps.txt
```

Run the full preparation path from the checked-in manifest:

```bash
./scripts/run_orbslam3_sequence.sh \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
  --prepare-only
```

Execute the real baseline once the upstream checkout exists:

```bash
./scripts/run_orbslam3_sequence.sh \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json
```

The execution wrapper now:

- injects repo-local OpenCV, Boost serialization, and Pangolin runtime library
  paths into `LD_LIBRARY_PATH` when those local prefixes exist
- auto-wraps the binary with `xvfb-run -a` when the host is headless
- runs ORB-SLAM3 from `build/insta360_x3_lens10/monocular/trajectory/` and
  passes only the basename `insta360_x3_lens10` so upstream writes
  `f_insta360_x3_lens10.txt` and `kf_insta360_x3_lens10.txt` in the configured
  output directory
- exits non-zero if the process returns without those trajectory artifacts

## Outputs

The monocular baseline writes:

- settings YAML: `build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml`
- prepared image folder: `build/insta360_x3_lens10/monocular/images/`
- timestamps file: `build/insta360_x3_lens10/monocular/timestamps.txt`
- trajectory stem: `build/insta360_x3_lens10/monocular/trajectory/insta360_x3_lens10`
- frame trajectory file: `build/insta360_x3_lens10/monocular/trajectory/f_insta360_x3_lens10.txt`
- keyframe trajectory file: `build/insta360_x3_lens10/monocular/trajectory/kf_insta360_x3_lens10.txt`
- log file: `logs/out/insta360_x3_lens10_monocular.log`
- report file: `reports/out/insta360_x3_lens10_monocular.md`

## Current Limitation

This ticket now organizes and derives the local one-lens input bundle from the
provided raw mp4 and calibration files, but the resulting data stays local-only
under `datasets/user/`. The repo can validate the import, preparation, and
run-contract paths without publishing the user recordings themselves. From a
fresh checkout, the lane still remains blocked until the local-only lens-10
inputs are imported. Pangolin is now handled through the repo-local bootstrap
path instead of an undocumented host-specific install. After the HEL-56
execution pass on a host with the imported lens-10 bundle plus repo-local
OpenCV, Boost, and Pangolin support, the remaining blocker is no longer native
setup: `reports/out/insta360_x3_lens10_monocular.md` and
`logs/out/insta360_x3_lens10_monocular.log` show the full run completed but the
atlas contained `0 KFs`, so no trajectory artifacts were written. The HEL-57
follow-up pass reran that lane on a host with the private exports, then tried
more aggressive ORB settings (`nFeatures: 4000`, `iniThFAST: 8`,
`minThFAST: 3`) with both the full frame list and an every-third-frame replay.
Those diagnostic reruns created a first keyframe and an initial map with 83-93
points, but both aborted with `double free or corruption (out)` before saving
any trajectory outputs. The current follow-up source of truth for that narrowed
blocker is [hel-57-monocular-follow-up.md](hel-57-monocular-follow-up.md).

See `docs/candidate-baseline-evaluation.md` for the HEL-48 candidate comparison
and the explicit rationale for keeping upstream as the selected baseline.
