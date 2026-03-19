# HEL-57 Monocular Follow-up

Status: Final
Issue: HEL-57
Last Updated: 2026-03-19

## Goal

Take the unresolved monocular blocker from
[final-validation-report.md](final-validation-report.md) and execute the
documented lens-10 lane on a host that actually has the private Insta360
exports.

## Host Execution Summary

Executed from the `HEL-57` Symphony worktree on 2026-03-19.

- Imported the private lens-10 inputs into
  `datasets/user/insta360_x3_one_lens_baseline/`
- Bootstrapped the repo-local `ffmpeg`, `cmake`, `Eigen3`, OpenCV, Boost
  serialization, and Pangolin fallbacks
- Fetched and built the pinned ORB-SLAM3 baseline at
  `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
- Reached `make monocular-prereqs` full readiness on this host

This confirms the remaining blocker is no longer hidden host setup when the
private inputs are available.

## Evidence

Local-only artifacts from this pass:

- `datasets/user/insta360_x3_one_lens_baseline/reports/ingest_report.md`
- `reports/out/insta360_x3_lens10_monocular_prereqs.md`
- `reports/out/insta360_x3_lens10_monocular.md`
- `logs/out/insta360_x3_lens10_monocular.log`
- `reports/out/insta360_x3_lens10_monocular_orb_aggressive.md`
- `logs/out/insta360_x3_lens10_monocular_orb_aggressive.log`
- `reports/out/insta360_x3_lens10_monocular_orb_aggressive_stride3.md`
- `logs/out/insta360_x3_lens10_monocular_orb_aggressive_stride3.log`

## Default Manifest Result

Command:

```bash
./scripts/run_orbslam3_sequence.sh \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json
```

Observed result:

- The wrapper prepared 270 frames and launched the real `mono_tum_vi` binary
- The upstream process returned `0`
- The local wrapper returned `2` because no trajectory files were written
- The log reached shutdown with `Map 0 has 0 KFs`

Conclusion:

- The canonical manifest still fails before the run produces a savable track
- Native dependency setup is not the next blocker on a prepared host

## Diagnostic Reruns

Two follow-up experiments were run to distinguish between "bad host setup" and
"bad monocular tuning."

### Aggressive ORB extractor

Changes from the canonical manifest:

- `ORBextractor.nFeatures: 4000`
- `ORBextractor.iniThFAST: 8`
- `ORBextractor.minThFAST: 3`

Observed result:

- ORB-SLAM3 printed `First KF:0; Map init KF:0`
- ORB-SLAM3 printed `New Map created with 93 points`
- The process aborted with `double free or corruption (out)`
- No frame or keyframe trajectory artifacts were written

### Aggressive ORB extractor plus every-third-frame sampling

Changes from the aggressive ORB experiment:

- Reused the same aggressive ORB settings
- Replayed every third frame instead of all 270 frames, leaving 90 prepared
  images

Observed result:

- ORB-SLAM3 printed `First KF:0; Map init KF:0`
- ORB-SLAM3 printed `New Map created with 83 points`
- The process aborted with `double free or corruption (out)`
- No frame or keyframe trajectory artifacts were written

## Narrowed Blocker

This issue did not end with a successful saved trajectory, but it did narrow
the blocker substantially:

- The host can now execute the full documented import, bootstrap, build, and
  launch path end to end
- The default monocular settings still fail before the first keyframe
- More aggressive ORB settings plus a sparser replay cadence both cross the
  initialization barrier and create a first map
- The next blocker is therefore a post-initialization abort, not missing
  Pangolin/OpenCV/Boost/native setup

## Recommended Next Step

Start the next follow-up from the aggressive ORB path, not from native
dependency setup.

Focus on isolating where the `double free or corruption (out)` happens after
the first map is created:

- upstream viewer / shutdown path
- trajectory-save path after non-empty initialization
- another memory-lifetime bug exposed by the tuned monocular settings

If that abort is fixed or worked around, re-evaluate whether the aggressive ORB
settings should become the new canonical lens-10 baseline.
