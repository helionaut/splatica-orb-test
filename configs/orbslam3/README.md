# ORB-SLAM3 settings bundles

Place ORB-SLAM3 settings files here.

- `smoke-placeholder.yaml` is a non-runnable placeholder used only by the dry-run harness.
- Future calibrated settings bundles should live alongside it with names tied to the rig or dataset they target.

`HEL-51` keeps private lens-10 settings out of git because they are generated
from the user's private calibration JSON. The canonical generated output path
is:

- `build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml`

Use the checked-in manifest
`manifests/insta360_x3_lens10_monocular_baseline.json` or the direct render
script in `configs/calibration/README.md` to regenerate that file.
