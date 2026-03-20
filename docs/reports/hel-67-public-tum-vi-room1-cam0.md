# Public TUM-VI `mono_tum_vi` Sanity Report

Status: Final
Issue: HEL-67
Last Updated: 2026-03-20

## Summary

The upstream ORB-SLAM3 monocular fisheye lane does not complete a real public
TUM-VI sanity run on this host. A fresh clean-room replay of the official
`dataset-room1_512_16` EuRoC export for `cam0` reached map initialization,
created a first map with 375 points, and then aborted with
`double free or corruption (out)` before any trajectory save path ran.

This issue is therefore no longer blocked on compile-only setup. The minimal
reproducible public runtime blocker is a phase-10 abort inside
`Examples/Monocular/mono_tum_vi` after first-map creation and before any frame
or keyframe trajectory files are written.

## Dataset Choice

- Public archive URL:
  `https://vision.in.tum.de/tumvi/exported/euroc/512_16/dataset-room1_512_16.tar`
- Local archive path:
  `/home/helionaut/workspaces/HEL-67/datasets/public/tum_vi/dataset-room1_512_16.tar`
- Archive SHA-256:
  `20354392eab5cc82c9770ed29cf0130c5acce0db54a257571499008fb34c398f`
- Extracted dataset root:
  `/home/helionaut/workspaces/HEL-67/datasets/public/tum_vi/dataset-room1_512_16`
- Camera lane:
  `mav0/cam0`
- Materialized frame index:
  `/home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/materialized/cam0_frame_index.csv`
- Materialized frame count:
  `2821`
- First materialized frame:
  `1520530308199447626,/home/helionaut/workspaces/HEL-67/datasets/public/tum_vi/dataset-room1_512_16/mav0/cam0/data/1520530308199447626.png`
- Last materialized frame:
  `1520530449203911100,/home/helionaut/workspaces/HEL-67/datasets/public/tum_vi/dataset-room1_512_16/mav0/cam0/data/1520530449203911100.png`

`room1_512_16` was chosen because it is a standard public TUM-VI room sequence
with full motion-capture ground truth, and `cam0` matches the single-camera
`mono_tum_vi` entrypoint contract.

## Binary Provenance

- Repo workspace:
  `/home/helionaut/workspaces/HEL-67`
- Repo commit:
  `83ac733b3813ffc0063c842f72054e048ce0ec80`
- Upstream ORB-SLAM3 commit:
  `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
- Executable:
  `/home/helionaut/workspaces/HEL-67/third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi`
- Executable SHA-256:
  `76e6c97296a7b9941ea51f9f6644ac442903d7e941e396d269c085f2effc38f4`
- Shared library:
  `/home/helionaut/workspaces/HEL-67/third_party/orbslam3/upstream/lib/libORB_SLAM3.so`
- Shared library SHA-256:
  `39a9aa485752747cba3b21793a1b4c49ca4946abaf86cb956651b51c2133be71`
- Build attempt metadata:
  `/home/helionaut/workspaces/HEL-67/.symphony/build-attempts/orbslam3-build-latest.json`
- Build log:
  `/home/helionaut/workspaces/HEL-67/.symphony/build-attempts/orbslam3-build-20260320T103009Z.log`

Provenance caveat: this HEL-67 run was launched with
`ORB_SLAM3_APPEND_MARCH_NATIVE=OFF`, but the actual compile and link commands in
the build log still included `-march=native`. The checked-in patcher now strips
that hard-coded upstream release-flag mutation for future runs, but the binary
used in this report was compiled before that fix was applied.

## Exact Launch Command

Clean-room orchestration:

```bash
python3 /mnt/c/!codex/scripts/run_with_progress_guard.py \
  --artifact .symphony/progress/HEL-67.json \
  --grace-seconds 300 \
  --stale-seconds 600 \
  --eta-seconds 5400 \
  -- ./scripts/run_clean_room_public_tum_vi_sanity.sh \
  manifests/tum_vi_room1_512_16_cam0_sanity.json
```

Runtime command emitted by the runner:

```bash
/usr/bin/xvfb-run -a \
  /home/helionaut/workspaces/HEL-67/third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi \
  /home/helionaut/workspaces/HEL-67/third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt \
  /home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/monocular/TUM-VI-room1-512-16-cam0.yaml \
  /home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/monocular/images \
  /home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/monocular/timestamps.txt \
  tum_vi_room1_512_16_cam0
```

## Result

- Progress artifact:
  `/home/helionaut/workspaces/HEL-67/.symphony/progress/HEL-67.json`
- Final status:
  `failed`
- Failed phase:
  `10/10`
- Runtime exit code `134`
- Runtime log:
  `/home/helionaut/workspaces/HEL-67/logs/out/tum_vi_room1_512_16_cam0.log`
- Orchestration log:
  `/home/helionaut/workspaces/HEL-67/logs/out/tum_vi_room1_512_16_orchestration.log`
- Runner report:
  `/home/helionaut/workspaces/HEL-67/reports/out/tum_vi_room1_512_16_cam0.md`
- Expected frame trajectory:
  `/home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/monocular/trajectory/f_tum_vi_room1_512_16_cam0.txt`
- Expected keyframe trajectory:
  `/home/helionaut/workspaces/HEL-67/build/tum_vi_room1_512_16/monocular/trajectory/kf_tum_vi_room1_512_16_cam0.txt`

No frame or keyframe trajectory files were produced, so there are no visual
trajectory proof artifacts for this pass.

## Minimal Reproducible Failure Boundary

The public runtime log ends at this boundary:

```text
Initialization of Atlas from scratch
Creation of new map with id: 0
Creation of new map with last KF id: 0
Seq. Name: tum_vi_room1_512_16_cam0
There are 1 cameras in the atlas
Camera 0 is fisheye
First KF:0; Map init KF:0
New Map created with 375 points
double free or corruption (out)
Aborted (core dumped)
```

That is the current minimal reproducible blocker for the public upstream
monocular lane on this host.

## Debugging Notes

- `ulimit -c` was `0`, so no local core file was retained.
- `coredumpctl` was unavailable in this environment.
- The build wrapper also printed a stale `Kernel OOM evidence detected` note,
  but the saved dmesg tail for this pass only showed WSL relay noise and memory
  pressure cache flushes, not a matching OOM kill for the successful build.

## Verdict

The upstream public `mono_tum_vi` sanity lane is not healthy on this host as of
2026-03-20. It compiles and launches, but the first real public replay aborts
with a deterministic heap-corruption boundary immediately after first-map
creation and before any trajectory output is saved.
