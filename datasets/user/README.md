# User datasets

Mount or copy real evaluation sequences here locally when they are available.

Do not commit user recordings or other large private data into the repository.
This directory is git-ignored except for this README so the repo can describe
private input contracts without publishing user data.

For the `HEL-51` Insta360 X3 lens-10 monocular baseline, place the private
inputs at:

- `datasets/user/insta360_x3_lens10/monocular_calibration.json`
- `datasets/user/insta360_x3_lens10/frame_index.csv`
- source PNG frames referenced by `frame_index.csv`

`frame_index.csv` must use the exact header `timestamp_ns,source_path`. Each
row should point at a PNG frame, either by an absolute path or by a path
relative to the CSV file itself. The preparation script copies those frames
into a deterministic output folder and renames them to `<timestamp_ns>.png` so
they match the upstream `mono_tum_vi` loader contract.
