# HEL-76 Private Save Comparison Follow-up

Status: Blocked with codified comparison evidence
Issue: HEL-76
Last Updated: 2026-03-21

## Goal

Keep the HEL-74 aggressive private lane as the diagnostic baseline, but turn
the HEL-75 public save probe into a direct repo execution lane that compares
private save cwd and post-close byte counts before any tuned settings are
promoted into the canonical manifest.

## Experiment Contract

- Changed variable: wrap the existing HEL-74 aggressive private rerun in a new
  HEL-76 comparison entrypoint that records the HEL-75 public save-byte proof
  and auto-discovers the known raw video download location when present
- Hypothesis: the repo should either produce a private save-byte comparison on
  a prepared host or leave a narrower blocked report that names the exact
  source inputs still missing before the comparison can start
- Success criterion: the current pass leaves a repo-owned HEL-76 report with
  the HEL-75 reference numbers plus the current private-lane evidence
- Abort condition: the private sidecars are still missing, the delegated rerun
  leaves no auditable report, or the comparison cannot recover the relevant
  save diagnostics

## Repo Changes In This Pass

- `scripts/run_private_save_comparison_followup.py` now codifies the HEL-76
  entrypoint:
  - reuses `scripts/run_private_monocular_followup.py` for the HEL-74 runtime
    contract
  - records the HEL-75 public save-path reference directly in the repo:
    - save cwd:
      `build/tum_vi_room1_512_16/monocular/trajectory_hel75_save_probe_140`
    - frame post-close bytes: `5437`
    - keyframe post-close bytes: `924`
  - auto-discovers the known raw video bundle under
    `/home/helionaut/.openclaw/workspace/downloads/insta360-*/{00.mp4,10.mp4}`
    when present, so the current host can fail at the precise missing-sidecar
    boundary instead of an implicit missing-video boundary
  - writes its own progress artifact and comparison report:
    - `.symphony/progress/HEL-76.json`
    - `reports/out/hel-76_private_save_comparison_followup.md`
- `Makefile` now exposes the comparison lane as:

  ```bash
  make monocular-save-compare-followup
  ```

## Host Evidence From This Pass

Running the HEL-76 entrypoint on this host still finds only the raw private
videos:

- `/home/helionaut/.openclaw/workspace/downloads/insta360-b87308a3/00.mp4`
- `/home/helionaut/.openclaw/workspace/downloads/insta360-b87308a3/10.mp4`

The current host evidence still does not include:

- `datasets/user/insta360_x3_one_lens_baseline/raw/calibration/insta360_x3_kb4_00_calib.txt`
- `datasets/user/insta360_x3_one_lens_baseline/raw/calibration/insta360_x3_kb4_10_calib.txt`
- `datasets/user/insta360_x3_one_lens_baseline/raw/calibration/insta360_x3_extr_rigs_calib.json`
- the prepared `datasets/user/insta360_x3_one_lens_baseline/lenses/10/` bundle

That means the current pass still cannot rerun the HEL-74 aggressive lane to
completion, but the blocked report is now narrower and directly tied to the
requested HEL-75 comparison contract.

## Command

```bash
make monocular-save-compare-followup
```

## Auditable Artifacts

- Progress artifact: `.symphony/progress/HEL-76.json`
- Comparison orchestration log:
  `logs/out/hel-76_private_save_comparison_followup.log`
- Comparison status report:
  `reports/out/hel-76_private_save_comparison_followup.md`
- Delegated private follow-up report:
  `reports/out/hel-76_private_monocular_followup.md`

## Result So Far

This pass does not yet produce a new private trajectory artifact, but it does
codify the exact next execution lane in the repo and leaves auditable evidence
for why the comparison is still blocked on this host:

- the HEL-75 public save-byte proof is now a checked-in reference for the next
  private rerun
- the current host still exposes only the raw private videos, not the required
  calibration/extrinsics sidecars
- the next engineer can rerun a single repo-owned command instead of rebuilding
  the HEL-74 and HEL-75 comparison contract from issue history

## Next Step

Restore the missing calibration/extrinsics sidecars or the prepared lens-10
bundle, then rerun `make monocular-save-compare-followup` so the HEL-74 private
lane can be compared directly against the HEL-75 save cwd and post-close byte
counts.
