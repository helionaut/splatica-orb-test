# HEL-69 Worktree Containment Follow-up

Status: Narrowed with auditable checkout-containment blocker
Issue: HEL-69
Last Updated: 2026-03-20

## Goal

Resume the HEL-57 aggressive private monocular lane from the active `HEL-69`
worktree and leave behind a trustworthy private ASan rerun, not another
artifact trail that silently depends on older workspaces.

## Why This Pass Stopped Before Another Private Rerun

The first `HEL-69` bootstrap review showed imported private lens-10 inputs,
prepared aggressive ORB images, and a runnable-looking `mono_tum_vi`. The new
linkage guard added in this pass proved that the runner was not actually local
to `HEL-69`:

- `make monocular-prereqs` now writes
  `reports/out/insta360_x3_lens10_monocular_prereqs.md`
- That report marks `Runner libORB_SLAM3 linkage: **missing**`
- `ldd third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi` resolves
  `libORB_SLAM3.so` to
  `/home/helionaut/workspaces/HEL-68-restacked/third_party/orbslam3/upstream/lib/libORB_SLAM3.so`

That meant the supposedly active checkout was already reusing another issue's
runtime outputs before any fresh `HEL-69` command was launched.

## Repo Changes From This Pass

- `scripts/build_orbslam3_baseline.sh` now adds an explicit
  `CMAKE_BUILD_RPATH` for the active checkout's ORB-SLAM3 libraries plus the
  resolved repo-local toolchain directories, so a real in-place rebuild has a
  chance to stay self-contained
- `src/splatica_orb_test/monocular_prereqs.py` now rejects:
  - a baseline checkout whose real path resolves outside the active repo
  - a `mono_tum_vi` runner whose `libORB_SLAM3.so` resolves outside the active
    ORB-SLAM3 checkout
- Tests were added in:
  - `tests/test_monocular_prereqs.py`
  - `tests/test_operator_scripts.py`

## Observed Build Containment Failure

After the new guard failed the stale runner, this pass attempted one materially
different build:

```bash
ORB_SLAM3_BUILD_TARGET=mono_tum_vi \
ORB_SLAM3_ENABLE_ASAN=1 \
ORB_SLAM3_BUILD_TYPE=RelWithDebInfo \
ORB_SLAM3_ASAN_COMPILE_FLAGS=' -fsanitize=address -fno-omit-frame-pointer -g -O0' \
ORB_SLAM3_PROGRESS_ARTIFACT=.symphony/progress/HEL-69.json \
ORB_SLAM3_PROGRESS_ISSUE_ID=HEL-69 \
./scripts/build_orbslam3_baseline.sh
```

The guarded build produced these auditable artifacts before it was stopped:

- Progress artifact: `.symphony/progress/HEL-69.json`
- Build attempt JSON:
  `.symphony/build-attempts/orbslam3-build-20260320T145253Z.json`
- Build attempt log:
  `.symphony/build-attempts/orbslam3-build-20260320T145253Z.log`

The build was intentionally interrupted because the log proved the compile was
still not local to `HEL-69`:

- `third_party/orbslam3/upstream` in `HEL-69` is a symlink to
  `/home/helionaut/workspaces/HEL-68-repo/third_party/orbslam3/upstream`
- `build/local-tools/{eigen,opencv,boost,pangolin}-root` are symlinks to
  `/home/helionaut/workspaces/HEL-61-exec-20260319T231736Z/build/local-tools/`
- The root ORB-SLAM3 build log records:
  - `gmake[1]: Entering directory '/home/helionaut/workspaces/HEL-68-repo/third_party/orbslam3/upstream/build'`
  - compiler include paths under `HEL-68-restacked` and `HEL-61-exec-20260319T231736Z`

Continuing that compile would have produced another false-positive "fresh"
binary whose provenance still depended on older workspaces.

## Narrowed Blocker

HEL-69 did not finish a trustworthy private rerun in this pass, but the
remaining blocker is now narrower and more actionable than the earlier generic
post-initialization crash note:

- The active `HEL-69` worktree is not yet self-contained enough to claim a new
  private ASan rerun
- The hidden dependency is broader than the old runner RUNPATH alone:
  - ORB-SLAM3 checkout path is symlinked to `HEL-68-repo`
  - repo-local tool prefixes are symlinked to `HEL-61-exec-20260319T231736Z`
  - the attempted rebuild therefore started mutating and compiling in older
    workspaces
- Any new private crash or success artifact would be untrustworthy until those
  containment problems are fixed or explicitly productized as a supported
  shared-cache mechanism

## Recommended Next Step

Before the next private aggressive ASan rerun:

1. Materialize `third_party/orbslam3/upstream/` inside the active worktree
   instead of symlinking it to another issue checkout
2. Materialize or explicitly support the local tool prefixes used by the build
   so `build/local-tools/` no longer silently points at older workspaces
3. Re-run `make monocular-prereqs` and confirm both new containment checks pass
4. Only then re-launch the HEL-57 aggressive private ASan lane with
   `.symphony/progress/HEL-69.json` enabled

Once that checkout-containment blocker is removed, the next valid private run
should be able to answer the original question from HEL-57/HEL-68 cleanly:
whether the private aggressive lane reproduces the same
`CreateInitialMapMonocular` / `EdgeSE3ProjectXYZ::linearizeOplus()` boundary or
finally runs through to saved trajectory artifacts.
