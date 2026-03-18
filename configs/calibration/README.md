# Calibration inputs

Store shareable camera intrinsics, camera-to-camera extrinsics, camera-to-IMU
extrinsics, and IMU noise/bias parameters here once they are safe to publish.

Keep user-specific calibration exports out of git unless they are safe to share
and needed for a reproducible public fixture.

For the `HEL-51` monocular baseline, the private calibration contract is:

- local path: `datasets/user/insta360_x3_lens10/monocular_calibration.json`
- camera model: `KannalaBrandt8`
- required camera keys: `label`, `model`, `image_width`, `image_height`,
  `fps`, `color_order`
- required nested keys: `intrinsics.{fx,fy,cx,cy}` and
  `distortion.{k1,k2,k3,k4}`
- optional override blocks: `orb` and `viewer`

Render that JSON into a runnable ORB-SLAM3 settings file with:

```bash
./scripts/render_monocular_settings.py \
  --calibration datasets/user/insta360_x3_lens10/monocular_calibration.json \
  --output build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml
```
