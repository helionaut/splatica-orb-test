# Product Requirements Document: ORB-SLAM3 validation for splatica-orb-test

Status: Draft
Issue: HEL-42
Last Updated: 2026-03-18
Source Of Truth: `docs/execution-plan.md`

## Objective

Turn the intake plan into an explicit success contract for the first project
slice: identify one reproducible ORB-SLAM3 baseline and settings bundle that
can process the user's stereo fisheye + IMU recordings, then document how to
rerun and judge that result.

## Target Operating Scenario

- The user has a custom stereo fisheye camera rig with an attached IMU.
- The immediate goal is offline validation on recorded sequences, not a live
  deployment or productized SLAM service.
- A successful outcome answers a practical question: which ORB-SLAM3 source
  baseline, commit, and configuration can ingest the user's data format and
  produce a repeatable validation run.
- The first pass should work against one smoke-test sequence and one
  representative sequence from the user's real operating environment when both
  are available.

## In Scope

- Choose one initial ORB-SLAM3 source baseline and pin the exact repo or fork
  plus commit SHA used for evaluation.
- Translate the user's stereo fisheye and IMU calibration into an ORB-SLAM3
  settings bundle or document why that translation is blocked.
- Run at least one validation attempt against the user's recorded dataset.
- Produce a validation report that states what worked, what failed, and what
  remains unresolved.

## Out Of Scope

- Real-time deployment, robotics integration, or any live runtime guarantees.
- Automatic calibration generation or sensor re-calibration.
- Broad bakeoff work across many forks, datasets, or algorithm families.
- Final publication or deployment decisions beyond the validation artifacts
  owned by this repo.

## Required User-Provided Inputs

Validation work can only be judged against the user's own rig if the following
inputs are supplied explicitly.

### 1. Recordings

- One replayable stereo recording with left and right image streams from the
  target rig.
- One representative IMU stream from the same capture session.
- Preferred: one short smoke-test sequence and one longer representative
  sequence.
- File layout details, naming conventions, and any pre-processing already
  applied before the data reaches this repo.

### 2. Camera Calibration

- Intrinsics for both fisheye cameras, including image size, camera model, and
  distortion coefficients.
- Left-to-right extrinsics for the stereo pair.
- Confirmation of whether the recordings are raw fisheye images or already
  rectified.

### 3. Camera-To-IMU Calibration

- Extrinsics between the camera frame and IMU frame.
- Axis conventions and frame definitions if they differ from ORB-SLAM3 example
  datasets.

### 4. Timing And Synchronization

- Timestamps for left frames, right frames, and IMU samples.
- Timestamp units and time base.
- Any known fixed offset, drift, dropped-sample behavior, or sync guarantees
  between cameras and IMU.
- Capture rates for both cameras and the IMU.

### 5. IMU Parameters

- Accelerometer and gyroscope units.
- Noise density and random-walk parameters used for visual-inertial tuning.
- Any known bias initialization or bias stability notes.

### 6. Acceptance Target

- Which sequence should count as the representative validation target.
- What the user considers acceptable tracking quality on that sequence.
- Whether any reference trajectory, map, or qualitative benchmark exists for
  comparison.

If camera-to-IMU extrinsics, timestamp behavior, IMU parameters, or the user's
acceptance target are missing, the repo may still support harness bring-up, but
it must not claim full stereo-inertial validation success.

## Success Criteria

The project needs two distinct pass levels so later experiments can be judged
without guessing.

### Technical Validation Pass

A run counts as a technical pass only if all of the following are true:

- The ORB-SLAM3 source choice is pinned to one repo or fork plus one commit
  SHA.
- Another engineer can build and rerun the attempt from a fresh checkout using
  documented commands and dependencies.
- The selected user sequence is ingested through a documented dataset layout or
  normalization step without ad hoc manual edits during the run.
- ORB-SLAM3 reaches a real processing run on the user's stereo fisheye + IMU
  data, produces non-empty output artifacts such as trajectory or log files,
  and does not terminate because of a crash, assertion, or manual restart.
- The validation report records whether initialization succeeded, when tracking
  was lost or recovered, and any sequence-specific limitations that prevent the
  run from being called stable.

### Dataset Acceptance Pass

A run counts as a dataset acceptance pass only if all of the following are
true:

- The technical validation pass is already satisfied.
- The user has supplied an explicit acceptance target for tracking quality,
  accuracy, or both.
- The validation report shows that the chosen baseline and config bundle met
  that target on the agreed representative sequence.

Without the user-defined acceptance target, the team may claim only a technical
validation pass, not a full success on the dataset.

## Required Handoff Artifacts

The repo handoff is complete only when it contains or references all of the
following artifacts:

- Baseline selection record: the chosen ORB-SLAM3 repo or fork, commit SHA,
  rationale for the choice, and any alternatives rejected during triage.
- Config bundle: the ORB-SLAM3 settings file, calibration translation notes,
  dataset path assumptions, and the exact run command used for validation.
- Validation report: dataset identifier, sequence used, input completeness,
  environment details, commands executed, log locations, observed behavior, and
  a pass or fail conclusion against the criteria above.
- Recommendation: a short statement that says what is ready for the next issue,
  what remains blocked, and whether additional calibration, timing, or fork
  work is required.

## Sequencing Against The Execution Plan

`HEL-42` defines the success contract only. It does not finish the engineering
harness, backlog decomposition, or publication path early.

1. `HEL-42` defines the operating scenario, required inputs, success criteria,
   and handoff artifacts.
2. `HEL-43` builds the reproducible environment, build path, and validation
   command lane around one baseline.
3. `HEL-44` decomposes implementation work after the PRD and harness settle.
4. `HEL-45` decides whether any publishable artifact is needed beyond the
   validation bundle.

## Open Questions And Blockers

- The user dataset has not yet been attached to this repo, so the exact replay
  format and normalization work remain unknown.
- The branch still needs the user's full stereo, fisheye, and camera-to-IMU
  calibration package to tell whether a settings-only translation is possible.
- Timestamp alignment and clock-offset behavior are still unknown; this is a
  likely blocker because timing failures can look like algorithm failures.
- IMU noise and bias parameters are still unknown; without them, visual-inertial
  tuning may be guesswork.
- The user's required validation quality threshold is still unspecified, so
  final dataset acceptance cannot be declared yet.
- It is still open whether upstream ORB-SLAM3 is sufficient or whether a
  maintained fork will be required once the first dataset run is attempted.
