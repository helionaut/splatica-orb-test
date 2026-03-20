# mono_tum_vi Build Provenance

Status: Draft
Issue: HEL-66
Last Updated: 2026-03-20

## Summary

`mono_tum_vi` built successfully on 2026-03-20 from the repository checkout at:

- Repo workspace: `/home/helionaut/workspaces/HEL-66`
- Repo commit: `39303d5f02f1c9e1f94499757a71551943c609ed`
- Upstream checkout: `/home/helionaut/workspaces/HEL-66/third_party/orbslam3/upstream`
- Upstream commit: `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`

The produced artifacts are:

- Executable: `/home/helionaut/workspaces/HEL-66/third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi`
- Executable SHA-256: `78a07f84e9b802544c3c008327f0201d2fbc7bfeeb2cf961cf1b6a8c20d94144`
- Shared library: `/home/helionaut/workspaces/HEL-66/third_party/orbslam3/upstream/lib/libORB_SLAM3.so`
- Shared library SHA-256: `989aef1a8e957020a6f589040d44c443489d401a65fe3714ffaf7c4ae9a6f6d0`

## Outcome

- Build result: passed
- Build finished at: `2026-03-20T06:30:36Z`
- Clean build without intervention: no
- New repository code or build-config changes required in this HEL-66 pass: no
- Existing fetched-upstream mutations applied by the checked-in wrapper: yes

The compile-only proof did not succeed from a fresh host environment. The
successful pass required these repo-supported environment bootstraps in order:

1. `./scripts/bootstrap_local_cmake.sh`
2. `./scripts/bootstrap_local_opencv.sh`
3. `./scripts/bootstrap_local_boost.sh`
4. `./scripts/bootstrap_local_eigen.sh`

The build did not need any new edits to the repository during HEL-66, but the
existing `./scripts/build_orbslam3_baseline.sh` flow still patches the fetched
upstream checkout before compiling. During the successful pass it reported:

- patched `third_party/orbslam3/upstream/src/System.cc`
- patched `third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi.cc`
- patched `third_party/orbslam3/upstream/Examples/RGB-D/rgbd_tum.cc`

The resulting patch-target hashes recorded by the wrapper were:

- `CMakeLists.txt`: `4ec721c72dc3304d8e0090202d7ccf0201ecd34630ffc8fe45b597d59c7e09e3`
- `src/System.cc`: `383323900266b0ece430f37692fd203966e83819c1f25fad6abb7bc71ac98e6c`
- `Examples/Monocular/mono_tum_vi.cc`: `d9cb138fe71f1611ffab2d77319db4e9cd105f909a24646ab251d7168975082d`

## Dependency Provenance

The successful build used these local prefixes from the current workspace:

- `cmake`: `/home/helionaut/workspaces/HEL-66/build/local-tools/cmake-root/usr/bin/cmake`
- `OpenCV_DIR`: `/home/helionaut/workspaces/HEL-66/build/local-tools/opencv-root/usr/lib/x86_64-linux-gnu/cmake/opencv4`
- `Eigen3_DIR`: `/home/helionaut/workspaces/HEL-66/build/local-tools/eigen-root/usr/share/eigen3/cmake`
- Boost serialization headers/libs: `/home/helionaut/workspaces/HEL-66/build/local-tools/boost-root/usr`

It also resolved Pangolin from outside the current workspace:

- `Pangolin_DIR`: `/home/helionaut/workspaces/HEL-61-exec-20260319T195741Z/build/local-tools/pangolin-build`

That external Pangolin path also appeared in the final compile and link lines
recorded in the build log. The final link step linked against
`libpango_*`/`libtinyobj.so` from that `HEL-61` workspace and against the
associated GL/GLEW sysroot under:

- `/home/helionaut/workspaces/HEL-61-exec-20260319T195741Z/build/local-tools/pangolin-root/sysroot/usr/lib/x86_64-linux-gnu`

## Build Flags and Logs

The wrapper metadata for the successful pass recorded:

- build target: `mono_tum_vi`
- experiment label: `orbslam3-mono_tum_vi-portable-build`
- declared release flags: `-std=gnu++14`
- build parallelism: `1`

The actual compile and link commands recorded in the build log still included
`-march=native`, so the produced binary is not a purely portable artifact even
though the wrapper metadata labels the attempt as a portable build.

Primary artifacts from the successful pass:

- build attempt metadata: `.symphony/build-attempts/orbslam3-build-latest.json`
- build log: `.symphony/build-attempts/orbslam3-build-20260320T061558Z.log`
- dmesg snapshot: `.symphony/build-attempts/orbslam3-build-dmesg-20260320T061558Z.log`

## Attempt Timeline

The successful build came after these deterministic blockers were addressed:

1. Initial build attempt failed immediately because `cmake` was missing.
2. After local `cmake`, `Thirdparty/DBoW2` configure failed because OpenCV was
   missing.
3. After local OpenCV, `Thirdparty/DBoW2` compile failed because Boost
   serialization headers were missing.
4. After local Boost serialization, `Thirdparty/g2o` configure failed because
   `Eigen3Config.cmake` was missing.
5. After local Eigen, the wrapper built `DBoW2`, `g2o`, configured `Sophus`,
   patched the upstream checkout, and built `mono_tum_vi`.

## Notes

The build log printed `Kernel OOM evidence detected`, but the saved dmesg
snapshot only contains older `oom-kill` lines from 2026-03-19, not from the
successful 2026-03-20 pass. Treat that stdout note as stale ambient kernel
history, not as evidence that this successful build was killed or retried.
