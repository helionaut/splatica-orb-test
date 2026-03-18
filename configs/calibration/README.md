# Calibration inputs

Store shareable camera intrinsics, camera-to-camera extrinsics, camera-to-IMU
extrinsics, and IMU noise/bias parameters here once they are safe to publish.

Keep user-specific calibration exports out of git unless they are safe to share
and needed for a reproducible public fixture.

The checked-in shareable calibration subset for `HEL-47` is:

- `configs/calibration/insta360_x3_shareable_rig.json`

That bundle contains the two lens intrinsics plus the raw rig extrinsic quoted
in HEL-47, but it intentionally leaves the full stereo+IMU path blocked until
camera-to-IMU and IMU inputs exist. See `docs/calibration-translation.md` for
the exact mapping and blocker list.

Render the committed monocular settings files directly with:

```bash
./scripts/render_shareable_calibration_settings.py \
  --calibration configs/calibration/insta360_x3_shareable_rig.json \
  --lens 10 \
  --fps 30 \
  --color-order RGB \
  --output configs/orbslam3/insta360_x3_lens10_monocular.yaml
```

For the `HEL-51`/`HEL-52` monocular baseline, the private calibration contract is:

- local path: `datasets/user/insta360_x3_one_lens_baseline/lenses/10/monocular_calibration.json`
- camera model: `KannalaBrandt8` or the raw source `kannalabrandt4` export
- required camera keys: `label`, `model`, `image_width`, `image_height`,
  `fps`, `color_order`
- required nested keys: `intrinsics.{fx,fy,cx,cy}` and
  `distortion.{k1,k2,k3,k4}`
- optional override blocks: `orb` and `viewer`

The canonical way to create that JSON now is the HEL-52 import helper, which
copies the raw `00.mp4`/`10.mp4` videos plus the raw `kb4` calibration exports
into `datasets/user/insta360_x3_one_lens_baseline/` and derives the lens-ready
JSON automatically.

Render that JSON into a runnable ORB-SLAM3 settings file with:

```bash
./scripts/render_monocular_settings.py \
  --calibration datasets/user/insta360_x3_one_lens_baseline/lenses/10/monocular_calibration.json \
  --output build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml
```
