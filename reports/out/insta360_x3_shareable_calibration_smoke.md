# Calibration config smoke report

## Result

- Calibration bundle: `configs/calibration/insta360_x3_shareable_rig.json`
- Source camera model: `kannalabrandt4`
- Source reference: `HEL-47 CEO update comment 2026-03-18T11:54:18Z`

## Generated settings bundles

- Lens `10` -> `configs/orbslam3/insta360_x3_lens10_monocular.yaml` with `Camera.fps=30.0` and `Camera.RGB=1 (RGB)`
- Lens `00` -> `configs/orbslam3/insta360_x3_lens00_monocular.yaml` with `Camera.fps=30.0` and `Camera.RGB=1 (RGB)`

## Raw rig extrinsics

- Reference camera: `10`
- Relative camera: `00`
- Translation (meters): `[0.000397764928582, 0.0013309520708354, -0.0180757563058398]`
- Quaternion xyzw: `[0.0005638487906206125, -0.0035558060950914524, 0.9999931401001314, 0.0008706722886403689]`

## Explicit blockers

- rig.layout is not overlapping_stereo, so the first pass should not emit a standard ORB-SLAM3 stereo pair settings bundle.
- Missing camera_to_imu needed for IMU.T_b_c1.
- Missing imu.noise_gyro needed for IMU.NoiseGyro.
- Missing imu.noise_acc needed for IMU.NoiseAcc.
- Missing imu.gyro_walk needed for IMU.GyroWalk.
- Missing imu.acc_walk needed for IMU.AccWalk.
- Missing imu.frequency_hz needed for IMU.Frequency.
- Missing source.source_file_names for provenance; the current repo only has the values quoted in HEL-47 comments.

## Notes

Harness-integrated config smoke for the shareable Insta360 X3 calibration subset. It writes two monocular YAMLs, validates the required scalar ORB-SLAM3 fields, and records the remaining blockers for any future stereo+IMU settings bundle.
