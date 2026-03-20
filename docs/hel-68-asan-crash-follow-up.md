# HEL-68 ASan Crash Follow-up

Status: Narrowed with auditable ASan trace
Issue: HEL-68
Last Updated: 2026-03-20

## Goal

Take the unresolved post-initialization abort from
[final-validation-report.md](final-validation-report.md) and narrow it beyond
the HEL-67 public `mono_tum_vi` boundary.

## Why This Pass Uses The Public Lane

The active `HEL-68` worktree does not contain the private lens-10 bundle under
`datasets/user/insta360_x3_one_lens_baseline/`; it only has
`datasets/user/README.md`. That means the aggressive monocular reruns from
[hel-57-monocular-follow-up.md](hel-57-monocular-follow-up.md) cannot be
re-executed directly from this checkout until the private lens-10 bundle is
imported again.

Instead, this pass codifies a sanitizer-backed debug lane that starts from the
same checked-in public TUM-VI `room1_512_16` `cam0` reproducer used by HEL-67,
while still preserving the HEL-57 aggressive monocular commands as the private
follow-up entrypoint once the local-only data is present again.

## Experiment Contract

- Changed variable: rebuild ORB-SLAM3 with AddressSanitizer enabled and rerun
  the bounded public `mono_tum_vi` reproducer
- Hypothesis: a sanitizer-enabled `mono_tum_vi` build will turn the current
  `double free or corruption (out)` abort into a concrete allocator stack trace
  that identifies the crashing ORB-SLAM3 subsystem
- Success criterion: the rerun leaves a saved log with an AddressSanitizer
  report and enough symbolized frames to name the crashing code path
- Abort condition: the sanitizer build fails before producing `mono_tum_vi`, or
  the bounded repro still aborts without a stack trace

## Sanitizer Build Lane

The ORB-SLAM3 build wrapper now accepts sanitizer-oriented environment flags
instead of requiring a one-off manual CMake invocation:

```bash
ORB_SLAM3_BUILD_TARGET=mono_tum_vi \
ORB_SLAM3_ENABLE_ASAN=1 \
ORB_SLAM3_BUILD_TYPE=RelWithDebInfo \
ORB_SLAM3_BUILD_CHANGED_VARIABLE="enable AddressSanitizer for mono_tum_vi on the public TUM-VI HEL-67 lane" \
ORB_SLAM3_BUILD_HYPOTHESIS="ASan will resolve the allocator abort to a concrete stack trace" \
ORB_SLAM3_BUILD_SUCCESS_CRITERION="sanitized mono_tum_vi builds and emits a stack trace on the bounded public repro" \
./scripts/build_orbslam3_baseline.sh
```

`ORB_SLAM3_ENABLE_ASAN=1` appends `-fsanitize=address -fno-omit-frame-pointer -g -O1`
to the compile flags, adds `-fsanitize=address` to the linker flags, and
defaults the build to `RelWithDebInfo` when `ORB_SLAM3_BUILD_TYPE` is not set
explicitly.

On this host, the default ASan `-O1` build currently exhausts memory while
compiling `src/Optimizer.cc`; the saved `dmesg` evidence includes
`Out of memory: Killed process ... cc1plus`. The wrapper therefore also accepts
`ORB_SLAM3_ASAN_COMPILE_FLAGS` so HEL-68 can run one materially different
reduced-memory sanitizer build instead of repeating the same OOM-prone attempt:

```bash
ORB_SLAM3_BUILD_TARGET=mono_tum_vi \
ORB_SLAM3_ENABLE_ASAN=1 \
ORB_SLAM3_BUILD_TYPE=RelWithDebInfo \
ORB_SLAM3_ASAN_COMPILE_FLAGS=' -fsanitize=address -fno-omit-frame-pointer -g -O0' \
ORB_SLAM3_BUILD_CHANGED_VARIABLE="switch the public mono_tum_vi ASan compile from -O1 to -O0 after the Optimizer.cc cc1plus OOM kill" \
ORB_SLAM3_BUILD_HYPOTHESIS="dropping the sanitizer compile optimization level to -O0 will keep Optimizer.cc below the host memory ceiling while preserving a symbolized runtime trace" \
ORB_SLAM3_BUILD_SUCCESS_CRITERION="sanitized mono_tum_vi builds and emits a stack trace on the bounded public repro" \
./scripts/build_orbslam3_baseline.sh
```

## Public Reproducer Command

Once the sanitized build exists, rerun the same public TUM-VI lane from HEL-67
with an explicit frame cap so the changed variable is bounded and auditable:

```bash
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1:symbolize=1 \
./scripts/run_monocular_baseline.py \
  --manifest manifests/tum_vi_room1_512_16_cam0_sanity.json \
  --output-tag asan_max20 \
  --max-frames 20
```

`--max-frames 20` sets `ORB_SLAM3_HEL68_MAX_FRAMES=20` for the patched
`mono_tum_vi` entrypoint so the runtime log records:

- `HEL-68 diagnostic: mono_tum_vi max frames=20`
- `HEL-68 diagnostic: frame <n> TrackMonocular start timestamp=...`
- `HEL-68 diagnostic: frame <n> TrackMonocular completed`
- `HEL-68 diagnostic: stopping after <N> frames due to ORB_SLAM3_HEL68_MAX_FRAMES`

If the ASan run still reaches shutdown without a stack trace, the next bounded
changed variable is to add save-phase isolation explicitly:

```bash
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1:symbolize=1 \
./scripts/run_monocular_baseline.py \
  --manifest manifests/tum_vi_room1_512_16_cam0_sanity.json \
  --output-tag asan_max20_skip_save \
  --max-frames 20 \
  --skip-frame-trajectory-save \
  --skip-keyframe-trajectory-save
```

Once the bounded save-enabled and save-skipped runs both prove that the first
`20` public frames are healthy, remove the frame cap but keep the save toggles
disabled so the next run can isolate a later runtime failure without the
trajectory-save path as a confounder:

```bash
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1:symbolize=1 \
./scripts/run_monocular_baseline.py \
  --manifest manifests/tum_vi_room1_512_16_cam0_sanity.json \
  --output-tag asan_full_skip_save_r1 \
  --skip-frame-trajectory-save \
  --skip-keyframe-trajectory-save
```

## Observed Result

The reduced-memory sanitized build exists and has reproducible provenance:

- Build attempt JSON: `.symphony/build-attempts/orbslam3-build-20260320T130529Z.json`
- Build attempt log: `.symphony/build-attempts/orbslam3-build-20260320T130529Z.log`
- Build target: `mono_tum_vi`
- Build type: `RelWithDebInfo`
- Sanitizer compile flags: `-std=gnu++14 -fsanitize=address -fno-omit-frame-pointer -g -O0`
- Executable SHA-256:
  `fd9f85102a33b1e6abccebed300813746774e1ed559f68fc6fa73bfa5d147d25`
- Shared library SHA-256:
  `1f08473e38376853a033ad75957f2a8948d5b54e57ded75ab1d869c9a636eeb8`

The public TUM-VI repro now has three auditable checkpoints:

1. `asan_max20`
   - Command: the bounded `--max-frames 20` save-enabled run above
   - Report: `reports/out/tum_vi_room1_512_16_cam0_asan_max20.md`
   - Log: `logs/out/tum_vi_room1_512_16_cam0_asan_max20.log`
   - Outcome: raw ORB-SLAM3 exit code `0`; processed frames `0..19`; reached
     shutdown plus both save calls; reported `There are 1 maps in the atlas`
     and `Map 0 has 0 KFs`; no ASan failure occurred
2. `asan_max20_skip_save_r1`
   - Command: the bounded `--max-frames 20` save-skipped run above
   - Report: `reports/out/tum_vi_room1_512_16_cam0_asan_max20_skip_save_r1.md`
   - Log: `logs/out/tum_vi_room1_512_16_cam0_asan_max20_skip_save_r1.log`
   - Outcome: exit code `0`; processed frames `0..19`; reached shutdown; log
     shows `save toggles frame=1, keyframe=1` and explicit skips for both save
     calls; no ASan failure occurred
3. `asan_full_skip_save_r1`
   - Command: the full save-skipped run above
   - Report: `reports/out/tum_vi_room1_512_16_cam0_asan_full_skip_save_r1.md`
   - Log: `logs/out/tum_vi_room1_512_16_cam0_asan_full_skip_save_r1.log`
   - Progress artifact: `.symphony/progress/HEL-68.json`
   - Outcome: exit code `134`; processed frames `0..92`; frame `93` entered
     `TrackMonocular`, logged `First KF:0; Map init KF:0`, then
     `New Map created with 375 points` immediately before the ASan abort

The save-skipped full replay finally narrows the runtime blocker beyond the old
allocator message. The actionable ORB-SLAM3 boundary is:

```text
ERROR: AddressSanitizer: stack-use-after-scope
ORB_SLAM3::EdgeSE3ProjectXYZ::linearizeOplus()
  at third_party/orbslam3/upstream/src/OptimizableTypes.cpp:152
g2o::BaseBinaryEdge<...>::linearizeOplus(...)
g2o::BlockSolver<...>::buildSystem()
g2o::SparseOptimizer::optimize(...)
ORB_SLAM3::Optimizer::BundleAdjustment(...)
ORB_SLAM3::Optimizer::GlobalBundleAdjustemnt(...)
ORB_SLAM3::Tracking::CreateInitialMapMonocular()
ORB_SLAM3::System::TrackMonocular(...)
main at third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi.cc:168
```

The ASan report also points the invalid read back to the same stack frame:

- `AddressSanitizer: stack-use-after-scope`
- `Address 0x... is located in stack of thread T0`
- `#0 ORB_SLAM3::EdgeSE3ProjectXYZ::linearizeOplus()`
- `Memory access ... is inside this variable`

## Narrowed Failure Boundary

HEL-68 is no longer blocked on the generic
`double free or corruption (out)` message from HEL-67.

The public runtime abort is now narrowed to:

- subsystem: monocular initial-map global bundle adjustment
- concrete failing function:
  `ORB_SLAM3::EdgeSE3ProjectXYZ::linearizeOplus()`
- source file: `third_party/orbslam3/upstream/src/OptimizableTypes.cpp:152`
- trigger point: frame `93` of the public
  `dataset-room1_512_16` `cam0` lane, immediately after first-keyframe / new-map
  creation with `375` points
- ruled-out boundary: the first `20` frames, bounded shutdown, and the
  trajectory-save path itself

That is specific enough for the next pass to focus on the Eigen/g2o Jacobian
computation in `OptimizableTypes.cpp` instead of repeating another blind public
runtime replay.

## Private Follow-up Entry Point

When the private lens-10 bundle is available again, resume from the HEL-57
aggressive monocular baseline:

```bash
./scripts/run_monocular_baseline.py \
  --manifest manifests/insta360_x3_lens10_monocular_baseline.json \
  --output-tag orb_aggressive \
  --orb-n-features 4000 \
  --orb-ini-fast 8 \
  --orb-min-fast 3
```

The sanitizer build lane above is intended to narrow the allocator boundary on
the exact HEL-67 public repro first so that the next private rerun does not
have to start from another blind `double free or corruption (out)` abort.
