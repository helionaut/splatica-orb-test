# Calibration Translation

Status: Draft
Issue: HEL-47
Last Updated: 2026-03-18

## Goal

Translate the shareable subset of the user's stereo fisheye calibration into
ORB-SLAM3 settings artifacts that the harness can load without hand-editing,
while keeping unsupported or missing inputs explicit.

## Checked-In Inputs

The shareable bundle lives at
`configs/calibration/insta360_x3_shareable_rig.json`.

It currently includes:

- lens `10/` intrinsics and four Kannala-Brandt distortion coefficients
- lens `00/` intrinsics and four Kannala-Brandt distortion coefficients
- image size `2880x2880`
- one raw rig extrinsic from reference lens `10/` to relative lens `00/`

It currently does not include:

- source calibration file names
- camera-to-IMU extrinsics
- IMU noise terms
- IMU frequency
- user-confirmed frame rate
- user-confirmed image color order

## ORB-SLAM3 Source Mapping

### Monocular fisheye baseline

For the first runnable baseline, the harness renders one monocular ORB-SLAM3
YAML per lens.

- Source model: `kannalabrandt4`
- ORB-SLAM3 camera type: `KannalaBrandt8`
- Direct scalar mapping:
  - `fx` -> `Camera1.fx`
  - `fy` -> `Camera1.fy`
  - `cx` -> `Camera1.cx`
  - `cy` -> `Camera1.cy`
  - `k1` -> `Camera1.k1`
  - `k2` -> `Camera1.k2`
  - `k3` -> `Camera1.k3`
  - `k4` -> `Camera1.k4`
- Shared image size:
  - `image_width` -> `Camera.width`
  - `image_height` -> `Camera.height`

This is grounded in the official ORB-SLAM3 `v1.0-release` monocular and
stereo-inertial TUM-VI examples, which both label the fisheye model as
`KannalaBrandt8` and use the four scalar distortion fields `k1` through `k4`.

## Smoke-Only Overrides

The checked-in config smoke manifest is
`manifests/insta360_x3_shareable_calibration_smoke.json`.

That smoke path intentionally supplies two values that are not present in the
shareable calibration source:

- `Camera.fps = 30.0`
- `Camera.RGB = 1` (`RGB`)

Those values exist only to let the harness write and validate a deterministic
monocular settings bundle in this repo. They are not claimed as user-provided
calibration facts. Confirm them against the real export path before any
user-data baseline run.

## Raw Rig Extrinsics

The raw rig metadata is stored exactly as provided:

- reference lens: `10/`
- relative lens: `00/`
- translation in meters:
  `[0.000397764928582, 0.0013309520708354, -0.0180757563058398]`
- quaternion in `xyzw` order:
  `[0.0005638487906206125, -0.0035558060950914524, 0.9999931401001314, 0.0008706722886403689]`

The first pass does not render `Stereo.T_c1_c2` from that value yet.

Reasons:

- the rig is described as approximately back-to-back, not as a standard
  overlapping stereo pair
- the issue comments do not include the original file-level frame convention or
  source file names needed to confirm the exact transform direction
- the first accepted baseline for this repo is monocular per lens, not
  overlapping stereo

## Camera-To-IMU And IMU Mapping

When those inputs become available, the intended ORB-SLAM3 fields are:

- camera-to-IMU extrinsics -> `IMU.T_b_c1`
- gyroscope noise density -> `IMU.NoiseGyro`
- accelerometer noise density -> `IMU.NoiseAcc`
- gyroscope random walk -> `IMU.GyroWalk`
- accelerometer random walk -> `IMU.AccWalk`
- IMU sample rate -> `IMU.Frequency`

No such values are visible in HEL-47 yet, so the translator fails fast instead
of inventing them.

## Baseline Caveats

- The current shareable calibration is enough for per-lens monocular YAML
  generation, not for a trustworthy stereo+IMU ORB-SLAM3 baseline.
- The upstream ORB-SLAM3 stereo-inertial parser expects an overlapping stereo
  pair. A back-to-back rig should not be treated as a drop-in replacement in
  the first implementation pass.
- The environment used for this issue does not include OpenCV or the ORB-SLAM3
  toolchain, so the saved smoke evidence validates the generated scalar
  settings bundle through the repo harness rather than a full upstream binary
  execution.
