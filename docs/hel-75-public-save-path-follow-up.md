# HEL-75 Public Save-Path Probe Follow-up

Status: Narrowed with auditable public save-path evidence
Issue: HEL-75
Last Updated: 2026-03-21

## Goal

Keep the HEL-74 aggressive private lane as the blocker baseline, but prove
whether the HEL-75 save-path diagnostics can actually write and immediately
reopen trajectory files on a known-good `mono_tum_vi` lane before blaming the
generic wrapper or working-directory contract.

## Experiment Contract

- Changed variable: keep the HEL-74 ASan plus no-static-alignment build, then
  run the public TUM-VI `room1_512_16` cam0 lane with
  `--output-tag hel75_save_probe_140 --max-frames 140` so the process exits
  shortly after the already-observed first-map boundary
- Hypothesis: the bounded public replay will leave trajectory files plus HEL-75
  post-close diagnostics if the save path is healthy on a known-good dataset
- Success criterion: the bounded public run writes dedicated trajectory
  artifacts or leaves explicit HEL-75 diagnostics that explain why the expected
  files are absent
- Abort condition: the bounded run fails to initialize by frame `140`, aborts
  before save, or exits without new save-path evidence

## Host Execution Summary

Executed from the `HEL-75` Symphony worktree on 2026-03-21.

- Reused the already-built ASan/no-static-alignment `mono_tum_vi` binary from
  the clean-room public TUM-VI orchestration lane
- Let the full public replay run long enough to confirm the lane still crossed
  initialization at frame `93` with `New Map created with 375 points`
- Started a dedicated bounded replay with a distinct output tag so the save
  probe would not overwrite the full-lane artifacts:
  - output tag: `hel75_save_probe_140`
  - max frames: `140`
  - trajectory working directory:
    `build/tum_vi_room1_512_16/monocular/trajectory_hel75_save_probe_140/`
- Stopped the older full public replay once it had already provided the
  initialization evidence so the bounded save probe could take the host and
  reach shutdown faster

## Auditable Artifacts

- Full-lane progress artifact: `.symphony/progress/HEL-75.json`
- Bounded save-probe progress artifact: `.symphony/progress/HEL-75-save-probe.json`
- Clean-room orchestration log:
  `logs/out/hel-75_tum_vi_save_diagnostics_orchestration.log`
- Bounded save-probe log:
  `logs/out/tum_vi_room1_512_16_cam0_hel75_save_probe_140.log`
- Bounded save-probe report:
  `reports/out/tum_vi_room1_512_16_cam0_hel75_save_probe_140.md`
- Saved frame trajectory:
  `build/tum_vi_room1_512_16/monocular/trajectory_hel75_save_probe_140/f_tum_vi_room1_512_16_cam0_hel75_save_probe_140.txt`
- Saved keyframe trajectory:
  `build/tum_vi_room1_512_16/monocular/trajectory_hel75_save_probe_140/kf_tum_vi_room1_512_16_cam0_hel75_save_probe_140.txt`

## What The Probe Proved

The bounded public lane crossed the same first-map boundary as the longer full
replay:

- frame `93`: `First KF:0; Map init KF:0`
- frame `93`: `New Map created with 375 points`

The save path then executed successfully at shutdown under the HEL-75
instrumentation:

- `HEL-75 diagnostic: trajectory save cwd=/home/helionaut/workspaces/HEL-75/repo/build/tum_vi_room1_512_16/monocular/trajectory_hel75_save_probe_140`
- `Saving trajectory to f_tum_vi_room1_512_16_cam0_hel75_save_probe_140.txt ...`
- `Map 0 has 8 KFs`
- `HEL-75 diagnostic: SaveTrajectoryEuRoC post_close open=1, bytes=5437, filename=f_tum_vi_room1_512_16_cam0_hel75_save_probe_140.txt`
- `Saving keyframe trajectory to kf_tum_vi_room1_512_16_cam0_hel75_save_probe_140.txt ...`
- `HEL-75 diagnostic: SaveKeyFrameTrajectoryEuRoC post_close open=1, bytes=924, filename=kf_tum_vi_room1_512_16_cam0_hel75_save_probe_140.txt`

The saved artifacts on disk match those post-close diagnostics:

- frame trajectory exists with `5437` bytes
- keyframe trajectory exists with `924` bytes

The raw process still returned exit code `1`, but the report shows that exit is
explained by LeakSanitizer rather than missing save output:

- `SUMMARY: AddressSanitizer: 7152947 byte(s) leaked in 16038 allocation(s).`

## Narrowed Blocker

The blocker is no longer "does the generic save path fail to write files?".

HEL-75 now proves that on the same patched ASan/no-static-alignment build:

- the monocular wrapper's trajectory working directory is correct on a public
  fisheye lane
- `SaveTrajectoryEuRoC` and `SaveKeyFrameTrajectoryEuRoC` can both write files
- the HEL-75 post-close diagnostics can immediately reopen those files and
  observe non-zero byte counts
- LeakSanitizer can still force a non-zero exit even when the save path itself
  succeeded

That means the HEL-74 private missing-file result is narrower and later than a
generic wrapper/path bug. The remaining difference is private-lane-specific:

- either the private aggressive lane reaches save with materially different map
  state than the public probe
- or the private lane's save call reports completion without leaving the same
  post-close bytes that the public probe now proves are possible

## Recommended Next Step

Replay the HEL-74 aggressive private lane on the host that has the private
exports, but keep the HEL-75 diagnostics enabled and compare its end-of-run
save evidence against this public proof:

1. record the private lane's reported save cwd and post-close byte counts for
   `f_insta360_x3_lens10_orb_aggressive_asan_no_static_alignment_hel74.txt`
2. confirm whether the private lane actually fails to reopen the file after
   close, or whether it writes a file and only LeakSanitizer keeps the exit
   non-zero
3. only after that comparison decide whether the remaining private blocker is a
   dataset-specific save omission, a later cleanup/removal side effect, or
   simply leak-policy noise after a successful save
