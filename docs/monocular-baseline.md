# Monocular Baseline

Status: Draft
Issue: HEL-51
Last Updated: 2026-03-18

## Goal

Run the first real ORB-SLAM3 lane against a single Insta360 X3 lens without
IMU so the project can validate calibration translation, preprocessing, and
baseline source selection before attempting the full back-to-back rig.

## Baseline Choice

- Upstream repo: `https://github.com/UZ-SLAMLab/ORB_SLAM3`
- Pinned release: `v1.0-release`
- Pinned commit: `0df83dde1c85c7ab91a0d47de7a29685d046f637`
- Executable path: `Examples/Monocular/mono_tum_vi`
- Vocabulary path: `Vocabulary/ORBvoc.txt`

This baseline was chosen because the official ORB-SLAM3 release already ships a
monocular fisheye path for TUM-VI without IMU. That makes it the smallest
change from a documented upstream lane while still matching the immediate need:
one fisheye lens, offline replay, and no inertial dependence.

## Private Input Contract

The repo does not commit the user's calibration or recordings. The local-only
input contract is:

- `datasets/user/insta360_x3_lens10/monocular_calibration.json`
- `datasets/user/insta360_x3_lens10/frame_index.csv`
- PNG source frames referenced by `frame_index.csv`

`monocular_calibration.json` must provide:

- `camera.label`
- `camera.model` set to `KannalaBrandt8`
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
./scripts/build_orbslam3_baseline.sh
```

The build helper assumes local build tools such as `cmake` and `make` are
installed before upstream compilation starts.

Generate the settings YAML directly:

```bash
./scripts/render_monocular_settings.py \
  --calibration datasets/user/insta360_x3_lens10/monocular_calibration.json \
  --output build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml
```

Normalize the frame list directly:

```bash
./scripts/prepare_monocular_sequence.py \
  --frame-index datasets/user/insta360_x3_lens10/frame_index.csv \
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

This ticket adds the runnable contract and automation, but not the private
lens-10 calibration JSON or frame index CSV themselves. Until those local-only
inputs are present, the repo can validate only the generation and preparation
path, not a full user-data run.
