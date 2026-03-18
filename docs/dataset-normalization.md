# Dataset Normalization

Status: Draft
Issue: HEL-46
Last Updated: 2026-03-18

## Goal

Define one repeatable import and normalization contract for stereo fisheye plus
IMU recordings so later tickets can consume a deterministic layout without
manual renaming or hidden cleanup steps.

## Supported Raw Input Layout

The only supported raw input layout is:

```text
<raw_root>/
  sequence.json
  left_frames.csv
  right_frames.csv
  imu_samples.csv
  source/
    left/*.png
    right/*.png
```

`sequence.json` must be a JSON object with at least:

- `sequence_id`
- `timestamp_unit` set to `ns`
- `rig.left_camera`
- `rig.right_camera`
- `rig.imu`

`left_frames.csv` and `right_frames.csv` must both use the exact header:

```text
timestamp_ns,source_path
```

The two stereo indexes must have the same number of rows and the same
timestamps in the same order. `source_path` may be absolute or relative to the
CSV file, but only `.png` frames are supported.

`imu_samples.csv` must use the exact header:

```text
timestamp_ns,angular_velocity_x,angular_velocity_y,angular_velocity_z,linear_acceleration_x,linear_acceleration_y,linear_acceleration_z
```

IMU timestamps must be strictly increasing and must cover the full stereo frame
interval.

## Normalized Output Layout

The normalization command rewrites the sequence into:

```text
<normalized_root>/
  sequence.json
  stereo/
    left/<timestamp_ns>.png
    right/<timestamp_ns>.png
    timestamps.csv
  imu/
    data.csv
```

`sequence.json` carries the original sequence metadata plus:

- `raw_layout`
- `normalized_layout`
- `counts`
- `timestamp_range_ns`
- `imu_coverage_ns`

`stereo/timestamps.csv` uses the exact header:

```text
timestamp_ns,left_path,right_path
```

## Command

Use the checked-in fixture manifest to validate the path from a clean checkout:

```bash
make normalize-fixture
```

That target runs:

```bash
./scripts/prepare_stereo_imu_sequence.py \
  --manifest manifests/stereo_imu_fixture_normalization.json
```

The generated report is written to
`reports/out/stereo_imu_fixture_normalization.md`.

## Explicit Failures

The normalization lane fails fast with actionable errors for:

- missing `sequence.json`, `left_frames.csv`, `right_frames.csv`, or `imu_samples.csv`
- malformed frame or IMU timestamps
- out-of-order timestamps
- stereo timestamp gaps between the left and right cameras
- IMU coverage that does not span the stereo interval
- unsupported non-PNG frame patterns
