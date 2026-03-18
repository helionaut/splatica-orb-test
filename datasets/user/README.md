# User datasets

Mount or copy real evaluation sequences here locally when they are available.

Do not commit user recordings or other large private data into the repository.
This directory is git-ignored except for this README so the repo can describe
private input contracts without publishing user data.

For the HEL-46 stereo+IMU normalization lane, use one raw directory per
sequence:

```text
datasets/user/<sequence>/raw/
  sequence.json
  left_frames.csv
  right_frames.csv
  imu_samples.csv
  source/
    left/*.png
    right/*.png
```

Run the canonical import command with a manifest that points at that `raw/`
directory:

```bash
./scripts/prepare_stereo_imu_sequence.py --manifest <manifest.json>
```

The only supported frame sources are timestamp-indexed PNG paths referenced
from `left_frames.csv` and `right_frames.csv`. Direct video files, JPG exports,
and ad hoc directory scans are intentionally unsupported in this lane so
failures stay explicit and repeatable.

For the `HEL-51`/`HEL-52` Insta360 X3 one-lens monocular baseline, place the
private inputs under:

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

Populate that layout with:

```bash
make bootstrap-local-ffmpeg
./scripts/import_monocular_video_inputs.py \
  --video-00 /path/to/00.mp4 \
  --video-10 /path/to/10.mp4 \
  --calibration-00 /path/to/insta360_x3_kb4_00_calib.txt \
  --calibration-10 /path/to/insta360_x3_kb4_10_calib.txt \
  --extrinsics /path/to/insta360_x3_extr_rigs_calib.json
```

The importer copies the raw assets into the repo-local layout, extracts PNGs,
generates `frame_index.csv` and `timestamps.txt`, derives
`monocular_calibration.json` for each lens, and writes a per-lens import
manifest plus a bundle-level markdown report. `frame_index.csv` always uses
the exact header `timestamp_ns,source_path`.
