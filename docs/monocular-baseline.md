# Monocular Baseline

Status: Draft
Issue: HEL-51
Last Updated: 2026-03-18

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
./scripts/build_orbslam3_baseline.sh
```

The build helper assumes `make` exists on the host. If `cmake` is not already
installed system-wide, the local bootstrap helper extracts a repo-local copy
under `build/local-tools/cmake-root/`, and the build helper will reuse it
automatically. If `Eigen3` is also absent, the local bootstrap helper extracts
`libeigen3-dev` into `build/local-tools/eigen-root/`, and the build helper adds
that prefix automatically through `CMAKE_PREFIX_PATH`. If OpenCV 4 is absent,
the local bootstrap helper extracts the Ubuntu OpenCV 4 dev/runtime package set
into `build/local-tools/opencv-root/`, and the build helper plus
`make monocular-prereqs` will reuse that prefix automatically. If Boost
serialization is absent, the local bootstrap helper extracts the required
headers/libs into `build/local-tools/boost-root/`, and the build helper plus
`make monocular-prereqs` will reuse that prefix automatically.
The wrapper now runs the ORB-SLAM3 component builds directly instead of
delegating to upstream `build.sh`, so it can disable optional Sophus
tests/examples that are not needed for `mono_tum_vi` and otherwise fail on
newer GCC toolchains because upstream enables `-Werror`.
The fetch helper already unpacks `Vocabulary/ORBvoc.txt` from the upstream
archive, so a missing extracted vocabulary file after fetch is now a concrete
baseline checkout problem rather than an expected pre-build state.
Pangolin still has to be provided either system-wide or through a manual local
install under `build/local-tools/pangolin-root/usr/local/`, because Ubuntu
`noble` does not currently ship a `libpangolin-dev` package.

Check whether the lane is actually ready before the first private run:

```bash
make monocular-prereqs
```

That command writes `reports/out/insta360_x3_lens10_monocular_prereqs.md` and
returns non-zero until the private calibration, frame index, native build
packages, extracted vocabulary, and built `mono_tum_vi` binary all exist. As
of HEL-54, the same report now checks repo-local OpenCV and Boost serialization
prefixes in addition to the earlier `cmake` and `Eigen3` fallbacks.

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

## Outputs

The monocular baseline writes:

- settings YAML: `build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml`
- prepared image folder: `build/insta360_x3_lens10/monocular/images/`
- timestamps file: `build/insta360_x3_lens10/monocular/timestamps.txt`
- trajectory stem: `build/insta360_x3_lens10/monocular/trajectory/insta360_x3_lens10`
- log file: `logs/out/insta360_x3_lens10_monocular.log`
- report file: `reports/out/insta360_x3_lens10_monocular.md`

## Current Limitation

This ticket now organizes and derives the local one-lens input bundle from the
provided raw mp4 and calibration files, but the resulting data stays local-only
under `datasets/user/`. The repo can validate the import, preparation, and
run-contract paths without publishing the user recordings themselves. On the
HEL-54 host, the remaining native blocker after the repo-local `cmake`,
`Eigen3`, OpenCV, and Boost serialization bootstraps is Pangolin provisioning.

See `docs/candidate-baseline-evaluation.md` for the HEL-48 candidate comparison
and the explicit rationale for keeping upstream as the selected baseline.
