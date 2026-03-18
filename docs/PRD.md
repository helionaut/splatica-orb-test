# Product Requirements Document: ORB-SLAM3 validation experiment contract

Status: Draft
Issue: HEL-53
Last Updated: 2026-03-18
Source Of Truth: `docs/execution-plan.md`, `README.md`, and the checked-in manifests

## Experiment Intent

This repository is not a browser prototype or a generic product brief. It is a
reproducibility workspace for answering one engineering question:

Can the team pin, prepare, run, and judge one ORB-SLAM3 baseline against the
provided fisheye recordings and related calibration assets without hidden
manual steps?

The intake intent from `docs/execution-plan.md` still applies: validate the
ORB-SLAM3 hypothesis on the user's asset family and leave behind a rerunnable
experiment contract. The repair in `HEL-53` is to make that contract match the
repo's real staged workflow instead of the earlier intake-only framing.

## Locked Project Decisions

- The primary deliverable is validation evidence, not an end-user application.
- The first accepted runtime lane is the lens-10 monocular fisheye baseline
  without IMU, because the current back-to-back rig and missing camera-to-IMU
  / IMU inputs do not justify claiming stereo-inertial support yet.
- Stereo fisheye plus IMU assets still matter now because they define the
  normalization contract and the future full-rig evidence requirements.
- Dry-run harness outputs, fixture normalization, and YAML generation are
  necessary setup evidence, but they are not by themselves a successful
  ORB-SLAM3 validation result.
- A future full-rig conclusion may be "blocked" or "use a different fusion
  path" if the non-overlapping rig cannot satisfy standard ORB-SLAM3 stereo
  assumptions.

## Real Inputs

The experiment contract now depends on three input classes.

### 1. Checked-In Shareable Inputs

These inputs are versioned in the repo and must stay reproducible from a clean
checkout.

- Stereo+IMU normalization fixture:
  `datasets/fixtures/stereo_imu_fixture/raw/`
- Shareable calibration subset:
  `configs/calibration/insta360_x3_shareable_rig.json`
- Normalization manifest:
  `manifests/stereo_imu_fixture_normalization.json`
- Calibration smoke manifest:
  `manifests/insta360_x3_shareable_calibration_smoke.json`
- Baseline selection and future-rig docs:
  `docs/candidate-baseline-evaluation.md` and `docs/future-rig-plan.md`

### 2. Local-Only User Inputs

These inputs are intentionally not committed, but the repo defines their exact
expected layout and preparation path.

- Raw lens videos:
  `datasets/user/insta360_x3_one_lens_baseline/raw/video/{00.mp4,10.mp4}`
- Raw calibration exports:
  `datasets/user/insta360_x3_one_lens_baseline/raw/calibration/`
- Derived per-lens bundle for the runnable baseline:
  `datasets/user/insta360_x3_one_lens_baseline/lenses/10/`
- Baseline manifest that consumes those derived files:
  `manifests/insta360_x3_lens10_monocular_baseline.json`

### 3. Still-Missing Inputs Required For Any Full Stereo+IMU Claim

The repo must keep these gaps explicit instead of guessing values.

- camera-to-IMU extrinsics
- IMU noise density, random walk, and frequency
- confirmed timestamp offset and drift behavior across cameras and IMU
- user-defined acceptance target for tracking quality on the representative run

Without those inputs, the project may claim harness readiness and monocular
baseline progress, but not full stereo+IMU validation success.

## Prepared Artifacts The Repo Must Produce

The repaired PRD needs to match the artifacts already implied by the harness
and downstream issues.

### Required Prepared Artifacts

- Pinned ORB-SLAM3 baseline identity:
  upstream `UZ-SLAMLab/ORB_SLAM3` at commit
  `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
- Reproducible manifests under `manifests/`
- Generated ORB-SLAM3 settings bundles under `configs/orbslam3/` or `build/`
- Prepared image/timestamp layouts under `build/`
- Logs under `logs/out/`
- Validation reports under `reports/out/`

### Minimum Evidence Files Called Out By The Current Repo

- `reports/out/stereo_imu_fixture_normalization.md`
- `reports/out/insta360_x3_shareable_calibration_smoke.md`
- `reports/out/insta360_x3_lens10_monocular_prereqs.md`
- `reports/out/insta360_x3_lens10_monocular.md`

If a downstream issue changes a command or output path, it must update this PRD
or the command's owning doc in the same change.

## Canonical Validation Flow

The repo now has a staged experiment lane. Later work should reference this
order instead of inventing new paths.

1. Confirm repo health with `make check`.
   This aggregates tests, build, smoke, calibration-smoke, and fixture
   normalization.
2. Validate the stereo+IMU data contract with `make normalize-fixture`.
   This proves the canonical raw-input and normalized-output layout from
   `HEL-46`.
3. Validate the shareable calibration path with `make calibration-smoke`.
   This proves the harness can regenerate deterministic monocular YAMLs while
   recording blockers for any future stereo+IMU bundle.
4. Fetch and build the selected upstream ORB-SLAM3 baseline with:
   `./scripts/fetch_orbslam3_baseline.sh` and
   `./scripts/build_orbslam3_baseline.sh`, using the documented local tool
   bootstraps as needed.
5. Import the provided local-only lens assets with
   `./scripts/import_monocular_video_inputs.py` so the repo owns a deterministic
   bundle under `datasets/user/insta360_x3_one_lens_baseline/`.
6. Fail fast on missing prerequisites with `make monocular-prereqs`.
   That command is the explicit readiness gate before any real ORB-SLAM3 run.
7. Generate the runnable prepared sequence with
   `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json --prepare-only`.
8. Execute the actual runtime lane with
   `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json`.
9. Record any tuning pass as a reproducible before/after comparison against the
   same baseline, manifest, and representative sequence.
10. Consolidate the final conclusion into one rerunnable report and
    recommendation for `HEL-49`.

## Success Criteria

The project now needs four distinct pass levels so later work cannot overclaim
progress.

### 1. Contract Readiness Pass

This pass is satisfied only if all of the following are true:

- the repo documents one canonical command path for normalization, calibration
  smoke, baseline preparation, and runtime validation
- the baseline repo, commit SHA, manifests, output paths, and expected reports
  are explicit
- another engineer can identify which inputs are shareable, which are local
  only, and which are still missing

### 2. Runnable Baseline Pass

This pass is satisfied only if all of the following are true:

- the selected ORB-SLAM3 baseline is fetched and built at the pinned commit
- the local-only lens-10 inputs are imported into the deterministic repo layout
- `make monocular-prereqs` succeeds without hidden manual fixes
- the preparation step emits the expected settings YAML, timestamp file, and
  prepared image directory

### 3. Runtime Validation Pass

This pass is satisfied only if all of the following are true:

- the real `mono_tum_vi` lane runs against the prepared lens-10 sequence
- the run produces non-empty runtime evidence such as log, report, and
  trajectory outputs
- the report records whether initialization succeeded, where tracking was lost
  or recovered, and what sequence-specific limits remain
- the result can be rerun from the documented commands on another checkout with
  the same private inputs and baseline pin

### 4. Experiment Decision Pass

This pass is satisfied only if all of the following are true:

- the starting configuration and any tuned configuration are tied to the same
  baseline SHA and representative input sequence
- every non-default parameter change is documented with a rationale
- the final report states one explicit conclusion:
  validated, partially validated, or blocked
- the final report names the next unresolved risk instead of leaving the
  outcome ambiguous

## Full Stereo+IMU Acceptance Boundary

The repo must not claim full success for the back-to-back fisheye + IMU rig
unless all of the following are true:

- the missing camera-to-IMU, IMU, and timing inputs are supplied explicitly
- the chosen path proves viable on the representative rig data
- the report explains whether the result came from standard ORB-SLAM3 support
  or from a future dual-monocular / fusion workaround
- the evidence is stronger than fixture normalization, calibration smoke, or a
  monocular-only run

Until then, the correct language is partial validation or blocked validation,
not end-to-end stereo-inertial success.

## Explicit Failure Conditions

The experiment is considered failed or still blocked if any of the following is
true:

- calibration or IMU values are inferred instead of sourced from real inputs
- the repo can only pass smoke or fixture commands but cannot launch the real
  baseline runner
- the run crashes, produces no output artifacts, or requires undocumented
  manual edits during execution
- the evidence does not identify the exact baseline commit, manifest, and
  sequence used
- the repo claims stereo+IMU validation from monocular-only evidence
- the final report does not state what worked, what failed, and what remains

## Downstream Contract For Remaining Issues

This repaired PRD is the contract that the remaining issue pack should follow.

- `HEL-43` owns the reproducible harness and aggregate validation gate.
- `HEL-46` owns the stereo+IMU raw and normalized data contract.
- `HEL-47` owns calibration translation plus explicit blocker reporting.
- `HEL-48` owns the baseline/fork decision and the pinned upstream commit.
- `HEL-50` owns the reproducible tuning loop and before/after evidence.
- `HEL-51` and `HEL-52` own the real monocular baseline lane plus the private
  input organization path.
- `HEL-49` must assemble the final validation report, rerun path, and
  validated/partial/blocked recommendation.

## Current Known Blockers

- The current rig is back-to-back rather than a normal overlapping stereo pair.
- The repo still lacks committed camera-to-IMU and full IMU parameter data.
- The runtime lane depends on local native ORB-SLAM3 prerequisites and private
  user inputs that are not present on every machine.
- The user-facing acceptance threshold for the representative run is still not
  recorded in the repo.
