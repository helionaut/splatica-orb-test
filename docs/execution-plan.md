# Execution Plan

## Mission

Find a reproducible ORB-SLAM3 baseline and settings bundle that can process the
user's stereo fisheye + IMU recordings, then document how to rerun and validate
that result.

## What "Working" Means

The target outcome is not just "ORB-SLAM3 compiled once." A successful first
project slice should leave behind:

- one documented ORB-SLAM3 source baseline and commit SHA
- one reproducible build/run path from a fresh checkout
- one settings bundle adapted to the user's rig and data format
- one validation report from the user's dataset with logs and observed behavior
- one recommendation that states what worked, what failed, and what remains

## Technical Starting Point

- The official [ORB-SLAM3 repository](https://github.com/UZ-SLAMLab/ORB_SLAM3)
  documents stereo, fisheye, and visual-inertial support, including TUM-VI
  fisheye examples with and without IMU.
- That upstream support lowers the algorithm risk, but it does not remove the
  integration risk for a custom stereo fisheye rig. The likely failure points
  are calibration quality, timestamp alignment, dataset formatting, dependency
  drift, and version or fork compatibility.

## Intake Scope

This intake ticket should clarify:

- the project goal and end-state artifacts
- the minimum inputs required from the user
- the order of downstream work
- which open questions must be resolved before meaningful implementation starts

This intake ticket should not try to finish the PRD, build harness, backlog, or
publication path early. Those each already have downstream issues.

## Required Inputs From The User

Before the validation work can succeed, the project will need:

- stereo recordings in a reproducible replay format
- fisheye camera intrinsics and left/right extrinsics
- camera-to-IMU extrinsics plus IMU noise/bias parameters
- timestamp conventions and any known clock-offset behavior
- frame rate, resolution, and any pre-processing already applied
- a definition of acceptable validation quality on the user's dataset

If any of those are missing, the first engineering work should treat that gap as
a blocker instead of guessing.

## Risks To Retire Early

- The user dataset may not match the file layout or timing assumptions expected
  by upstream ORB-SLAM3 examples.
- Calibration may exist, but not in a form that maps cleanly into ORB-SLAM3
  settings files.
- IMU/image timing drift may dominate failures that look like "bad SLAM."
- A settings-only fix may be insufficient; the best outcome may require picking
  a specific commit or maintained fork.
- The bootstrap-generated deployment track may not mean "ship an app." For this
  repo, deployment probably means publishing a static validation report or other
  reproducible results artifact.

## Downstream Issue Pack

### HEL-42: PRD and success criteria

Use `HEL-42` to lock the success contract:

- define the target user and exact operating scenario
- define pass/fail evidence for a "working" ORB-SLAM3 run
- define what artifacts the repo must produce at handoff time
- record the known unknowns from calibration, timing, and dataset shape

### HEL-43: Engineering harness

Use `HEL-43` to create the reproducible technical lane:

- one canonical environment setup and dependency story
- one build command and one aggregate validation command
- one smoke-run path for a small representative sequence
- clear locations for configs, calibration, datasets, logs, and tests

### HEL-44: Backlog decomposition

Use `HEL-44` after the PRD and harness settle. The likely implementation slices
are:

- dataset import and normalization
- calibration translation into ORB-SLAM3 settings
- candidate ORB-SLAM3 baseline evaluation
- configuration tuning on the user's rig
- final validation report and reproducibility cleanup

### HEL-45: Deployment setup

Do not assume this repo needs a live application deployment. `HEL-45` should
first decide whether the project needs a publishable artifact at all. If it
does, the likely target is a static report or results bundle rather than an
interactive app.

## First Next Actions For Symphony

1. Use `HEL-42` to turn the intake into an explicit success contract and list of
   required user-provided inputs.
2. Use `HEL-43` to build a minimal harness around one upstream ORB-SLAM3
   baseline, with room to compare alternative commits or forks later.
3. Once those two foundations exist, use `HEL-44` to split the evaluation work
   into small tickets with concrete acceptance criteria.
4. Revisit `HEL-45` only after there is a concrete artifact worth publishing.
