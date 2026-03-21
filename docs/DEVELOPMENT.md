# Development

For the current operator entrypoint, rerun order, and final repo or user-rig
verdict, start with [final-validation-report.md](final-validation-report.md).
This file remains the command reference.

## Golden path

1. Read the current project scope in `README.md`, `docs/execution-plan.md`, and `docs/PRD.md` when product requirements change.
2. Generate the current dry-run build artifact with `make build`.
3. Exercise the smoke-run path with `make smoke`.
4. Exercise the checked-in calibration translation path with `make calibration-smoke`.
5. Exercise the public RGB-D sanity lane with `make rgbd-sanity` when you need a clean-room upstream proof.
6. Exercise the public TUM-VI monocular sanity lane with `make tum-vi-sanity` when you need a real upstream `mono_tum_vi` proof on a public fisheye sequence.
7. Exercise the dataset normalization path with `make normalize-fixture`.
8. Run the aggregate validation gate with `make check`.

## Commands

- `make build`: render the current smoke plan into `build/smoke-plan.md`.
- `make smoke`: run the dry-run ORB-SLAM3 lane and write smoke outputs under `logs/out/` and `reports/out/`.
- `make calibration-smoke`: regenerate and validate the checked-in shareable calibration settings bundle plus saved smoke log/report.
- `make fetch-tum-rgbd`: download and extract the public TUM RGB-D `fr1/xyz` archive into `datasets/public/tum_rgbd/`.
- `make fetch-tum-vi`: download and extract the public TUM-VI `room1_512_16` EuRoC export into `datasets/public/tum_vi/`.
- `make rgbd-sanity`: fetch the pinned ORB-SLAM3 baseline, bootstrap repo-local native dependencies, download the public TUM RGB-D `fr1/xyz` sequence, build the upstream `rgbd_tum` target, and run the clean-room sanity lane end-to-end.
- `make tum-vi-sanity`: fetch the pinned ORB-SLAM3 baseline, bootstrap repo-local native dependencies, download the public TUM-VI `room1_512_16` EuRoC export, materialize `cam0` into the repo's monocular calibration-plus-frame-index contract, build `mono_tum_vi`, and run the public sanity lane end-to-end.
- `make bootstrap-local-cmake`: extract Ubuntu `cmake` packages plus their runtime libraries into `build/local-tools/cmake-root/` so the repo can run the upstream build helper without system-wide install privileges.
- `make bootstrap-local-eigen`: extract the Ubuntu `libeigen3-dev` package into `build/local-tools/eigen-root/` so the repo can satisfy `Eigen3` without a system-wide install.
- `make bootstrap-local-opencv`: extract the Ubuntu OpenCV 4 dev/runtime package set plus its transitive dependency closure into `build/local-tools/opencv-root/` so the repo can satisfy `find_package(OpenCV 4.4)` and the final ORB-SLAM3 example link step without a system-wide install.
- `make bootstrap-local-boost`: extract the Ubuntu Boost serialization headers/libs into `build/local-tools/boost-root/` so ORB-SLAM3 can compile and link `-lboost_serialization` without a system-wide install.
- `make bootstrap-local-ffmpeg`: download and unpack a pinned repo-local `ffmpeg`/`ffprobe` bundle into `build/local-tools/ffmpeg-root/` so the monocular input-import lane can probe mp4 metadata and extract PNGs without a host install.
- `make bootstrap-local-pangolin`: clone Pangolin `v0.8`, extract the required GL/GLEW/X11 development package closure into `build/local-tools/pangolin-root/sysroot/`, and install a repo-local `PangolinConfig.cmake` under `build/local-tools/pangolin-root/usr/local/`.
- `make monocular-prereqs`: check whether the private lens-10 raw inputs, prepared lens bundle, fetched baseline checkout, extracted vocabulary, built executable, and native packages are ready for the real monocular run. The command writes `reports/out/insta360_x3_lens10_monocular_prereqs.md` and exits non-zero while blockers remain.
- `make monocular-followup`: run the HEL-73 aggressive private monocular follow-up entrypoint. The helper writes `.symphony/progress/HEL-73.json`, `logs/out/hel-73_private_monocular_followup.log`, and `reports/out/hel-73_private_monocular_followup.md`, fails fast on missing calibration/extrinsics sidecars when the prepared bundle is absent, and otherwise rebuilds `mono_tum_vi` with the HEL-72 ASan plus no-static-alignment toggles before delegating to `scripts/run_monocular_baseline.py`.
- `make normalize-fixture`: normalize the checked-in stereo+IMU fixture into `build/fixtures/stereo_imu_fixture/normalized/` and write a report to `reports/out/stereo_imu_fixture_normalization.md`.
- `make test`: run the repository tests.
- `make check`: run tests, build, smoke, calibration-smoke, and fixture normalization together.
- `./scripts/fetch_orbslam3_baseline.sh`: clone the pinned ORB-SLAM3 upstream baseline into `third_party/orbslam3/upstream` and unpack `Vocabulary/ORBvoc.txt` from the upstream archive so the runtime vocabulary path exists before the full native build.
- `./scripts/fetch_tum_rgbd_dataset.py --manifest manifests/tum_rgbd_fr1_xyz_sanity.json`: download the official TUM RGB-D `fr1/xyz` archive into `datasets/public/tum_rgbd/`, extract it in place, and leave a deterministic dataset root for the public sanity lane.
- `./scripts/fetch_tum_vi_dataset.py --manifest manifests/tum_vi_room1_512_16_cam0_sanity.json`: download the official TUM-VI `room1_512_16` EuRoC export into `datasets/public/tum_vi/`, extract it in place, and leave a deterministic `mav0/cam0` root for the public monocular sanity lane.
- `./scripts/bootstrap_local_cmake.sh`: extract a repo-local `cmake` toolchain from Ubuntu packages into `build/local-tools/cmake-root/`. `./scripts/build_orbslam3_baseline.sh` will use that fallback automatically if `cmake` is not available on `PATH`.
- `./scripts/bootstrap_local_eigen.sh`: extract a repo-local `Eigen3` prefix from Ubuntu packages into `build/local-tools/eigen-root/`. `./scripts/build_orbslam3_baseline.sh` will add that prefix to `CMAKE_PREFIX_PATH` automatically if present.
- `./scripts/bootstrap_local_opencv.sh`: extract the Ubuntu OpenCV 4 dev/runtime package set plus its transitive dependency closure into `build/local-tools/opencv-root/`, and record the resolved package list in `build/local-tools/opencv-root/bootstrap-manifest.txt`. `./scripts/build_orbslam3_baseline.sh` and `make monocular-prereqs` will reuse that prefix automatically if the host does not already provide OpenCV.
- `./scripts/bootstrap_local_boost.sh`: extract the Ubuntu Boost serialization headers/libs into `build/local-tools/boost-root/`. `./scripts/build_orbslam3_baseline.sh` and `make monocular-prereqs` will reuse that prefix automatically if the host does not already provide Boost serialization.
- `./scripts/bootstrap_local_ffmpeg.sh`: download a pinned static `ffmpeg`/`ffprobe` bundle into `build/local-tools/ffmpeg-root/`. `./scripts/import_monocular_video_inputs.py` will reuse that fallback automatically when host binaries are absent.
- `./scripts/bootstrap_local_pangolin.sh`: clone Pangolin `v0.8`, resolve the Ubuntu GL/GLEW/X11 development package closure into `build/local-tools/pangolin-root/sysroot/`, and install `PangolinConfig.cmake` plus the Pangolin shared libraries under `build/local-tools/pangolin-root/usr/local/`. The helper injects `-include cstdint` so Pangolin still builds under Ubuntu `noble`'s GCC 13 toolchain, and both `./scripts/build_orbslam3_baseline.sh` and the real monocular runner will reuse the repo-local Pangolin runtime paths automatically.
- `./scripts/extract_orbslam3_vocabulary.py --checkout-dir third_party/orbslam3/upstream`: unpack `Vocabulary/ORBvoc.txt` directly if a checkout already exists but the vocabulary text file has not been materialized yet.
- `./scripts/build_orbslam3_baseline.sh`: run the pinned ORB-SLAM3 native build sequence so `Examples/Monocular/mono_tum_vi` exists. The wrapper keeps the upstream component order, automatically reuses repo-local `cmake`, `Eigen3`, OpenCV, Boost serialization, and Pangolin fallbacks, disables optional `Thirdparty/Sophus` tests/examples because they are not required for `mono_tum_vi` and fail under newer GCC releases when upstream `-Werror` is enabled, asks CMake to build only the required `mono_tum_vi` target instead of the full upstream example set, and patches the upstream trajectory-save path so empty-keyframe runs fail cleanly instead of segfaulting during shutdown.
- `ORB_SLAM3_BUILD_TARGET=rgbd_tum ./scripts/build_orbslam3_baseline.sh`: build the upstream public RGB-D example target instead of the private monocular one.
- `./scripts/check_monocular_baseline_prereqs.py --manifest manifests/insta360_x3_lens10_monocular_baseline.json --report reports/out/insta360_x3_lens10_monocular_prereqs.md`: generate a saved readiness report for the private lens-10 monocular lane and fail fast if the environment still cannot execute the real baseline. The report now distinguishes missing raw `00.mp4` / `10.mp4`, missing raw calibration/extrinsics sidecars, missing prepared bundle outputs, and missing execution assets.
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/tum_rgbd_fr1_xyz_sanity.json`: execute the public RGB-D sanity lane with upstream `rgbd_tum`, the upstream `TUM1.yaml` settings file, the upstream `fr1_xyz.txt` association file, and non-empty trajectory verification.
- `./scripts/run_clean_room_rgbd_sanity.sh manifests/tum_rgbd_fr1_xyz_sanity.json`: run the full clean-room HEL-61 sequence in one repo-local command, including fetch, dependency bootstrap, dataset download, build, and RGB-D execution.
- `./scripts/materialize_public_tum_vi_sequence.py --manifest manifests/tum_vi_room1_512_16_cam0_sanity.json`: derive a monocular calibration JSON and frame-index CSV from the downloaded public TUM-VI `mav0/cam0` dataset so the existing `mono_tum_vi` wrapper can reuse the same preparation path as the private monocular lane.
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/tum_vi_room1_512_16_cam0_sanity.json`: execute the public TUM-VI monocular sanity lane with the generated settings YAML, prepared timestamp-named `cam0` images, and upstream `mono_tum_vi`.
- `./scripts/run_clean_room_public_tum_vi_sanity.sh manifests/tum_vi_room1_512_16_cam0_sanity.json`: run the full clean-room HEL-67 public TUM-VI sequence in one repo-local command, including fetch, dependency bootstrap, dataset download, materialization, build, and monocular execution while updating `.symphony/progress/HEL-67.json`.
- `./scripts/import_monocular_video_inputs.py --video-00 /path/to/00.mp4 --video-10 /path/to/10.mp4 --calibration-00 /path/to/insta360_x3_kb4_00_calib.txt --calibration-10 /path/to/insta360_x3_kb4_10_calib.txt --extrinsics /path/to/insta360_x3_extr_rigs_calib.json`: copy the raw one-lens assets into `datasets/user/insta360_x3_one_lens_baseline/`, extract source PNGs for both lenses, derive per-lens calibration JSON files, and write frame-index/timestamp/import-manifest outputs for the monocular baseline lane.
- `./scripts/run_private_monocular_followup.py --video-00 /path/to/00.mp4 --video-10 /path/to/10.mp4 --calibration-00 /path/to/insta360_x3_kb4_00_calib.txt --calibration-10 /path/to/insta360_x3_kb4_10_calib.txt --extrinsics /path/to/insta360_x3_extr_rigs_calib.json`: execute the HEL-73 private follow-up lane from the HEL-57 aggressive ORB baseline. The helper reuses an existing prepared bundle when present, otherwise imports lens `10` from the raw source contract, rebuilds `mono_tum_vi` with `ORB_SLAM3_ENABLE_ASAN=1` plus `ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1`, and then delegates to `scripts/run_monocular_baseline.py` with `nFeatures=4000`, `iniThFAST=8`, and `minThFAST=3`.
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json`: execute the real upstream `mono_tum_vi` runner once the baseline checkout and private inputs exist. The wrapper injects repo-local OpenCV, Boost, and Pangolin runtime library paths, auto-wraps the binary with `xvfb-run -a` when `DISPLAY` is absent, runs from the configured trajectory directory so ORB-SLAM3 writes `f_<stem>.txt` and `kf_<stem>.txt` in the expected place, and exits non-zero when the process finishes without those trajectory artifacts.
- `./scripts/prepare_stereo_imu_sequence.py --manifest manifests/stereo_imu_fixture_normalization.json`: normalize one raw stereo+IMU sequence into the canonical output layout defined in `docs/dataset-normalization.md`.
- `./scripts/render_shareable_calibration_settings.py --calibration configs/calibration/insta360_x3_shareable_rig.json --lens 10 --fps 30 --color-order RGB --output configs/orbslam3/insta360_x3_lens10_monocular.yaml`: render one committed shareable monocular settings file directly.
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_shareable_calibration_smoke.json`: regenerate both committed shareable monocular YAMLs and save the config-smoke evidence.
- `./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_lens10_monocular_baseline.json --prepare-only`: turn the private monocular calibration plus frame index into a runnable settings file and timestamp-named image folder.
- `make verify-production ARTIFACT_URL=https://<published-artifact-url>`: verify a published report or results bundle once deployment exists.

## Test-first rule

Behavior changes should begin with a failing test in `tests/`, or land with the implementation in the same change if the behavior is new. Keep tests mirrored against the code and docs they protect so it is obvious where future expectations belong.

## Repository layout

- `configs/calibration/`: camera and IMU calibration inputs.
- `configs/orbslam3/`: ORB-SLAM3 settings bundles.
- `datasets/fixtures/`: small shareable smoke fixtures.
- `datasets/public/`: public datasets that the repo can redownload for clean-room validation.
- `datasets/user/`: local-only user datasets and larger recordings.
- `docs/`: design, scope, and operator docs.
- `logs/out/`: generated logs from dry-runs and future real runs.
- `reports/out/`: generated validation reports and publishable results artifacts.
- `scripts/`: runnable entrypoints and verification helpers.
- `src/splatica_orb_test/`: Python helpers that define the harness contract.
- `tests/`: automated tests for harness behavior and expectations.
- `third_party/orbslam3/`: the future pinned upstream ORB-SLAM3 checkout or vendored baseline.
