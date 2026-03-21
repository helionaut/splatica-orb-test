# HEL-77 Private Save Comparison Follow-up

Status: Blocked with narrower clean-host prerequisite evidence
Issue: HEL-77
Last Updated: 2026-03-21

## Goal

Keep the HEL-74 aggressive private lane as the diagnostic baseline, rerun it on
the host that now exposes the private Insta360 exports, and compare its HEL-75
save cwd plus post-close byte counts before any tuned settings are promoted
into the canonical lens-10 manifest.

## Experiment Contract

- Changed variable: keep the HEL-74 aggressive private comparison lane, but
  auto-discover the known OpenClaw raw videos and inbound calibration sidecars
  so the host can reuse them without manual path translation
- Hypothesis: once the host-side private exports are surfaced and the repo-local
  media tooling is bootstrapped, the HEL-77 lane will move past the old
  missing-sidecar blocker and expose the next real build/runtime boundary
- Success criterion: the current pass leaves repo-owned HEL-77 evidence that
  either reaches private save-byte comparison or narrows the remaining blocker
  beyond the old HEL-76 host-input boundary
- Abort condition: the host-side files still cannot be consumed, the delegated
  rerun leaves no auditable report, or the build lane fails before any new
  evidence is recorded

## Repo Changes In This Pass

- Added `src/splatica_orb_test/private_host_inputs.py` so the private rerun
  helpers can auto-discover:
  - `/home/helionaut/.openclaw/workspace/downloads/insta360-*/{00.mp4,10.mp4}`
  - `/home/helionaut/.openclaw/media/inbound/*insta360_x3_{kb4_00,kb4_10,extr_rigs}_calib*`
- Updated `scripts/run_private_monocular_followup.py` to reuse those discovered
  OpenClaw host inputs when the repo-local raw bundle is absent.
- Updated `scripts/run_private_save_comparison_followup.py` to:
  - surface the discovered calibration/extrinsics paths in the saved status
    report
  - render the active issue identifier in the generated HEL-77 report/progress
    text instead of hard-coding HEL-76
  - write the delegated monocular orchestration log to
    `logs/out/hel-77_private_monocular_followup.log`
- Updated the focused tests that protect those private follow-up entrypoints.

## Host Evidence

The HEL-77 pass now proves this host has the private export inputs required to
start the aggressive lane:

- Raw videos discovered:
  - `/home/helionaut/.openclaw/workspace/downloads/insta360-b87308a3/00.mp4`
  - `/home/helionaut/.openclaw/workspace/downloads/insta360-b87308a3/10.mp4`
- Calibration/extrinsics sidecars discovered:
  - `/home/helionaut/.openclaw/media/inbound/insta360_x3_calib_insta360_x3_kb4_00_calib---eb6f64f5-dd5e-4a4e-9cca-834d8c572fe1.txt`
  - `/home/helionaut/.openclaw/media/inbound/insta360_x3_calib_insta360_x3_kb4_10_calib---819a56cb-1243-4ef0-86b7-4a1a5e8473f7.txt`
  - `/home/helionaut/.openclaw/media/inbound/insta360_x3_calib_insta360_x3_extr_rigs_calib---bc155887-5604-4885-950f-b70135e2abc2.json`
- `make bootstrap-local-ffmpeg` succeeded and created:
  - `build/local-tools/ffmpeg-root/bin/ffmpeg`
  - `build/local-tools/ffmpeg-root/bin/ffprobe`
- The importer successfully materialized the lens-10 prepared bundle:
  - `270` extracted frames under
    `datasets/user/insta360_x3_one_lens_baseline/lenses/10/source_png/`
  - `datasets/user/insta360_x3_one_lens_baseline/lenses/10/frame_index.csv`
  - `datasets/user/insta360_x3_one_lens_baseline/lenses/10/timestamps.txt`
  - `datasets/user/insta360_x3_one_lens_baseline/lenses/10/monocular_calibration.json`
  - `datasets/user/insta360_x3_one_lens_baseline/reports/ingest_report.md`
- The baseline fetch lane also succeeded:
  - `third_party/orbslam3/upstream/`
  - pinned upstream commit `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
  - extracted vocabulary
    `third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt`

The remaining blocker is now the repo-local native prerequisite lane, not the
private export lane:

- `scripts/build_orbslam3_baseline.sh` aborts immediately with:

  ```text
  Missing required build tool: cmake
  Install cmake on PATH or run ./scripts/bootstrap_local_cmake.sh first.
  ```

- The HEL-77 status report also confirms the clean workspace still lacks the
  repo-local or system copies of OpenCV, Eigen3, Boost serialization, and
  Pangolin, so the private save comparison still cannot reach the actual
  ORB-SLAM3 runtime yet.

## Commands

```bash
make bootstrap-local-ffmpeg
python3 scripts/run_private_save_comparison_followup.py \
  --progress-issue HEL-77 \
  --progress-artifact .symphony/progress/HEL-77.json \
  --delegate-progress-artifact .symphony/progress/HEL-77-private-run.json \
  --orchestration-log logs/out/hel-77_private_save_comparison_followup.log \
  --status-report reports/out/hel-77_private_save_comparison_followup.md \
  --delegate-status-report reports/out/hel-77_private_monocular_followup.md \
  --output-tag orb_aggressive_asan_no_static_alignment_hel77_save_compare
```

## Auditable Artifacts

- `.symphony/progress/HEL-77.json`
- `.symphony/progress/HEL-77-private-run.json`
- `logs/out/hel-77_private_save_comparison_followup.log`
- `logs/out/hel-77_private_monocular_followup.log`
- `reports/out/hel-77_private_save_comparison_followup.md`
- `reports/out/hel-77_private_monocular_followup.md`
- `datasets/user/insta360_x3_one_lens_baseline/reports/ingest_report.md`

## Result So Far

HEL-77 does not yet produce private save cwd or post-close byte counts, but it
does narrow the blocker materially:

- the current host now proves the private exports and sidecars are accessible
- the repo can now materialize the prepared lens-10 bundle directly from those
  host files
- the pinned ORB-SLAM3 upstream checkout and vocabulary are now present in the
  clean HEL-77 workspace
- the next missing prerequisite is explicit and reproducible: `cmake` first,
  followed by the rest of the native dependency lane required before the
  aggressive rerun can re-enter ORB-SLAM3 itself

## Next Step

Bootstrap the remaining repo-local native prerequisites in the documented order
(`cmake`, `Eigen3`, OpenCV, Boost serialization, Pangolin), then rerun the
same HEL-77 comparison command so the aggressive private lane can finally move
past the clean-room build boundary and back toward HEL-75-style save-byte
evidence.
