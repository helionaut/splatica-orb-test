# HEL-77 Private Save Comparison Follow-up

Status: Blocked with narrower late shutdown/save evidence
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
  on the private-export host, then compare the resulting save-path evidence
  directly against the HEL-75 public byte-count reference
- Hypothesis: once the host-side private exports and clean-workspace native
  prerequisites are bootstrapped, the HEL-77 lane will move beyond the old
  input/build blockers and expose the next concrete shutdown/save boundary
- Success criterion: the current pass leaves repo-owned HEL-77 evidence that
  either records private post-close trajectory bytes or narrows the remaining
  blocker beyond the earlier prerequisite-only explanation
- Abort condition: the host-side files still cannot be consumed, the delegated
  rerun leaves no auditable report, or the save-path evidence still disappears
  before comparison can happen

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
  - parse the delegated monocular report for initialization-map counts,
    active-map resets, AddressSanitizer summaries, and the "save completed but
    file still missing" signal
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

The clean-workspace prerequisite blocker has now been cleared on this host:

- `make bootstrap-local-cmake`
- `make bootstrap-local-eigen`
- `make bootstrap-local-opencv`
- `make bootstrap-local-boost`
- `make bootstrap-local-pangolin`
- `./scripts/build_orbslam3_baseline.sh`

Those steps produced the expected repo-local runtime assets:

- `third_party/orbslam3/upstream/lib/libORB_SLAM3.so`
- `third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi`
- `reports/out/insta360_x3_lens10_monocular_prereqs.md` with full execution
  readiness on this host

## Runtime Evidence

The rerun now reaches materially further into the private aggressive lane than
the earlier HEL-57 and first-pass HEL-77 evidence:

- Initialization maps created: `2` (`93` points, then `71` points)
- Active map resets observed: `2`
- Frame `77`: `New Map created with 93 points`
- Frame `78`: `SYSTEM-> Reseting active map in monocular case`
- Frame `252`: `New Map created with 71 points`
- Frame `254`: `SYSTEM-> Reseting active map in monocular case`
- `HEL-63 diagnostic: calling SaveTrajectoryEuRoC for f_insta360_x3_lens10_orb_aggressive_asan_no_static_alignment_hel77_save_compare.txt`
- `HEL-63 diagnostic: SaveTrajectoryEuRoC completed`
- `HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC for kf_insta360_x3_lens10_orb_aggressive_asan_no_static_alignment_hel77_save_compare.txt`
- `HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed`
- `Keyframe trajectory save skipped because no keyframes were recorded`
- `SUMMARY: AddressSanitizer: 598421903 byte(s) leaked in 2383340 allocation(s).`

The private save comparison still remains blocked, but it is now blocked later
than either the old clean-host prerequisite failure or the HEL-57
`double free or corruption (out)` shutdown:

- the frame-trajectory save call returns in the log
- the expected frame trajectory file is still missing afterward at
  `build/insta360_x3_lens10/monocular/trajectory_orb_aggressive_asan_no_static_alignment_hel77_save_compare/f_insta360_x3_lens10_orb_aggressive_asan_no_static_alignment_hel77_save_compare.txt`
- no frame or keyframe trajectory files are present in the private save cwd
- there are still no private post-close byte counts to compare against the
  HEL-75 public reference (`5437` frame bytes, `924` keyframe bytes)

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

HEL-77 still does not produce private post-close byte counts, but it narrows
the blocker materially:

- the current host now proves the private exports and sidecars are accessible
- the repo can now materialize the prepared lens-10 bundle directly from those
  host files
- the clean-workspace native dependency lane can be bootstrapped end-to-end and
  rebuild the ASan/no-static-alignment `mono_tum_vi` runner
- the aggressive private rerun now creates two short-lived maps, reaches both
  trajectory-save calls, and exits under LeakSanitizer instead of the earlier
  immediate `double free or corruption (out)` abort
- the remaining blocker is now the late shutdown/save path: the private run
  still leaves no trajectory artifact on disk after `SaveTrajectoryEuRoC`
  returns, so HEL-75-style post-close byte comparison is still unavailable

## Next Step

Instrument the late private shutdown/save path further before promoting any
tuned settings into the canonical manifest. The next follow-up should preserve
this HEL-77 lane and answer why `SaveTrajectoryEuRoC` returns without leaving a
visible frame artifact in the private save cwd, then recover the missing
post-close byte counts if the file is being unlinked or removed after close.
