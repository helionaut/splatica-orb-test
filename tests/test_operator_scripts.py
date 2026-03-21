from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class OperatorScriptTests(unittest.TestCase):
    def test_opencv_bootstrap_resolves_dependency_closure(self) -> None:
        script = (REPO_ROOT / "scripts/bootstrap_local_opencv.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("apt-cache depends", script)
        self.assertIn("--recurse", script)
        self.assertIn("Seed packages", script)
        self.assertIn("Resolved package closure", script)
        self.assertIn("bootstrap-manifest.txt", script)
        self.assertIn('progress_artifact="${ORB_SLAM3_PROGRESS_ARTIFACT:-}"', script)
        self.assertIn('progress_issue_id="${ORB_SLAM3_PROGRESS_ISSUE_ID:-}"', script)
        self.assertIn("ORB_SLAM3_BOOTSTRAP_PROGRESS_HEARTBEAT_SECONDS", script)
        self.assertIn("write_progress_artifact()", script)
        self.assertIn("start_progress_heartbeat()", script)
        self.assertIn("stop_progress_heartbeat()", script)
        self.assertIn("OpenCV bootstrap failed", script)
        self.assertIn("OpenCV bootstrap completed", script)

    def test_pangolin_bootstrap_emits_progress_artifacts(self) -> None:
        script = (REPO_ROOT / "scripts/bootstrap_local_pangolin.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('progress_artifact="${ORB_SLAM3_PROGRESS_ARTIFACT:-}"', script)
        self.assertIn('progress_issue_id="${ORB_SLAM3_PROGRESS_ISSUE_ID:-}"', script)
        self.assertIn("ORB_SLAM3_BOOTSTRAP_PROGRESS_HEARTBEAT_SECONDS", script)
        self.assertIn("write_progress_artifact()", script)
        self.assertIn("start_progress_heartbeat()", script)
        self.assertIn("stop_progress_heartbeat()", script)
        self.assertIn("Pangolin bootstrap failed", script)
        self.assertIn("Pangolin bootstrap completed", script)

    def test_orbslam3_build_targets_mono_tum_vi(self) -> None:
        script = (REPO_ROOT / "scripts/build_orbslam3_baseline.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('build_target="${ORB_SLAM3_BUILD_TARGET:-mono_tum_vi}"', script)
        self.assertIn('build_type="${requested_build_type:-Release}"', script)
        self.assertIn('enable_asan="${ORB_SLAM3_ENABLE_ASAN:-0}"', script)
        self.assertIn(
            'disable_eigen_static_alignment="${ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT:-0}"',
            script,
        )
        self.assertIn('append_march_native="${ORB_SLAM3_APPEND_MARCH_NATIVE:-OFF}"', script)
        self.assertIn('build_parallelism="${ORB_SLAM3_BUILD_PARALLELISM:-1}"', script)
        self.assertIn('build_experiment="${ORB_SLAM3_BUILD_EXPERIMENT:-orbslam3-${build_target}-portable-build}"', script)
        self.assertIn('changed_variable="${ORB_SLAM3_BUILD_CHANGED_VARIABLE:-disable -march=native and capture build-attempt signature}"', script)
        self.assertIn('allow_identical_retry="${ORB_SLAM3_ALLOW_IDENTICAL_RETRY:-0}"', script)
        self.assertIn('build_progress_heartbeat_seconds="${ORB_SLAM3_BUILD_PROGRESS_HEARTBEAT_SECONDS:-30}"', script)
        self.assertIn('extra_compile_flags="${ORB_SLAM3_EXTRA_COMPILE_FLAGS:-}"', script)
        self.assertIn('extra_link_flags="${ORB_SLAM3_EXTRA_LINK_FLAGS:-}"', script)
        self.assertIn('asan_compile_flags="${ORB_SLAM3_ASAN_COMPILE_FLAGS:- -fsanitize=address -fno-omit-frame-pointer -g -O1}"', script)
        self.assertIn('progress_artifact="${ORB_SLAM3_PROGRESS_ARTIFACT:-}"', script)
        self.assertIn('progress_issue_id="${ORB_SLAM3_PROGRESS_ISSUE_ID:-}"', script)
        self.assertIn('progress_artifact="${repo_root}/${progress_artifact}"', script)
        self.assertIn('resolve_example_artifact_paths() {', script)
        self.assertIn('Examples/Monocular/${1}', script)
        self.assertIn('Examples/RGB-D/${1}', script)
        self.assertIn('build_example_source_path="${build_example_artifacts[1]}"', script)
        self.assertIn('AddressSanitizer diagnostic builds default to RelWithDebInfo.', script)
        self.assertIn('cmake_cxx_flags+="${asan_compile_flags}"', script)
        self.assertIn('cmake_c_flags+="${asan_compile_flags}"', script)
        self.assertIn('cmake_linker_flags+=" -fsanitize=address"', script)
        self.assertIn(
            'cmake_cxx_flags+=" -DEIGEN_MAX_STATIC_ALIGN_BYTES=0 -DEIGEN_DONT_ALIGN_STATICALLY"',
            script,
        )
        self.assertIn(
            'cmake_c_flags+=" -DEIGEN_MAX_STATIC_ALIGN_BYTES=0 -DEIGEN_DONT_ALIGN_STATICALLY"',
            script,
        )
        self.assertIn('"example_entrypoint": sha256(example_source_path)', script)
        self.assertIn(".symphony/build-attempts", script)
        self.assertIn("orbslam3-build-latest.log", script)
        self.assertIn("dmesg -T", script)
        self.assertIn("ORB_SLAM3_BUILD_PROGRESS_HEARTBEAT_SECONDS must be a positive integer", script)
        self.assertIn("render_build_heartbeat_step()", script)
        self.assertIn("start_build_progress_heartbeat()", script)
        self.assertIn("stop_build_progress_heartbeat()", script)
        self.assertIn('sleep "${build_progress_heartbeat_seconds}"', script)
        self.assertIn("--verbose", script)
        self.assertIn("Build PID:", script)
        self.assertIn("Kernel OOM evidence detected", script)
        self.assertIn("Identical retry rejected", script)
        self.assertIn("write_progress_artifact()", script)
        self.assertIn(
            '"disable_eigen_static_alignment": disable_eigen_static_alignment == "1"',
            script,
        )
        self.assertIn('"expected_artifact": relative_text(build_executable_path)', script)
        self.assertIn('update_progress_phase 7 "in_progress" "Root ORB_SLAM3 build is running for ${build_target} (pid ${build_pid})"', script)
        self.assertIn("--target", script)
        self.assertIn('"${build_target}"', script)
        self.assertIn("-Wl,-rpath-link", script)
        self.assertIn('build_rpath_dirs=()', script)
        self.assertIn('append_build_rpath_dir "${checkout_dir}/lib"', script)
        self.assertIn('append_build_rpath_dir "${checkout_dir}/Thirdparty/DBoW2/lib"', script)
        self.assertIn('append_build_rpath_dir "${checkout_dir}/Thirdparty/g2o/lib"', script)
        self.assertIn('cmake_args+=("-DCMAKE_BUILD_RPATH=${build_rpath_text}")', script)
        self.assertIn('cmake_build_type_suffix="$(printf \'%s\' "${build_type}" | tr \'[:lower:]\' \'[:upper:]\')"', script)
        self.assertIn('cmake_cxx_flag_name="CMAKE_CXX_FLAGS_${cmake_build_type_suffix}"', script)
        self.assertIn('cmake_c_flag_name="CMAKE_C_FLAGS_${cmake_build_type_suffix}"', script)
        self.assertIn('"-D${cmake_cxx_flag_name}=${cmake_cxx_flags}"', script)
        self.assertIn('"-D${cmake_c_flag_name}=${cmake_c_flags}"', script)
        self.assertIn("patch_orbslam3_baseline.py", script)

    def test_orbslam3_patch_helper_guards_empty_keyframe_saves(self) -> None:
        script = (REPO_ROOT / "scripts/patch_orbslam3_baseline.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("patch_cmakelists", script)
        self.assertIn(
            "wrapper-controlled release flags instead of",
            script,
        )
        self.assertIn(
            "Failed to normalize upstream -march=native release flags",
            script,
        )
        self.assertIn(
            "Waiting for ORB-SLAM3 worker shutdown before trajectory save.", script
        )
        self.assertIn(
            "Shutdown worker state before save: local_mapping_finished=", script
        )
        self.assertIn("No keyframes were recorded; skipping trajectory save.", script)
        self.assertIn(
            "No keyframes were recorded; skipping keyframe trajectory save.", script
        )
        self.assertIn("Map* pBiggerMap = nullptr;", script)
        self.assertIn("HEL-63 diagnostic: entering SLAM shutdown", script)
        self.assertIn("HEL-63 diagnostic: frame ", script)
        self.assertIn("ORB_SLAM3_HEL63_MAX_FRAMES", script)
        self.assertIn("ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE", script)
        self.assertIn("ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE", script)
        self.assertIn("patch_optimizable_types", script)
        self.assertIn("EdgeSE3ProjectXYZ Jacobian lifetime fix", script)
        self.assertIn("const Eigen::Matrix<double, 2, 3> project_jac =", script)

    def test_monocular_runner_uses_trajectory_workdir_and_validates_outputs(self) -> None:
        script = (REPO_ROOT / "scripts/run_monocular_baseline.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("resolve_monocular_trajectory_outputs", script)
        self.assertIn("cwd=run_workdir", script)
        self.assertIn("without writing non-empty trajectory artifacts", script)
        self.assertIn("--frame-stride", script)
        self.assertIn("--max-frames", script)
        self.assertIn("--progress-artifact", script)
        self.assertIn("--progress-issue", script)
        self.assertIn("--output-tag", script)
        self.assertIn("--skip-frame-trajectory-save", script)
        self.assertIn("ORB_SLAM3_HEL68_MAX_FRAMES", script)
        self.assertIn("FRAME_COMPLETED_PATTERN", script)
        self.assertIn("write_progress_artifact", script)
        self.assertIn("process = subprocess.Popen(", script)
        self.assertNotIn("Popen(\n            command,\n            check=False,", script)

    def test_rgbd_runner_supports_hel63_diagnostics(self) -> None:
        script = (REPO_ROOT / "scripts/run_rgbd_tum_baseline.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("--max-frames", script)
        self.assertIn("--disable-viewer", script)
        self.assertIn("--skip-frame-trajectory-save", script)
        self.assertIn("--skip-keyframe-trajectory-save", script)
        self.assertIn("ORB_SLAM3_HEL63_MAX_FRAMES", script)

    def test_sequence_launcher_supports_rgbd_tum_mode(self) -> None:
        script = (REPO_ROOT / "scripts/run_orbslam3_sequence.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("rgbd_tum", script)
        self.assertIn("run_rgbd_tum_baseline.py", script)

    def test_rgbd_runner_supports_diagnostic_toggles(self) -> None:
        script = (REPO_ROOT / "scripts/run_rgbd_tum_baseline.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("--output-tag", script)
        self.assertIn("--disable-viewer", script)
        self.assertIn("--skip-frame-trajectory-save", script)
        self.assertIn("--skip-keyframe-trajectory-save", script)
        self.assertIn("ORB_SLAM3_DISABLE_VIEWER", script)

    def test_clean_room_rgbd_sanity_script_covers_fetch_build_and_run(self) -> None:
        script = (REPO_ROOT / "scripts/run_clean_room_rgbd_sanity.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("run_clean_room_rgbd_sanity.py", script)

    def test_clean_room_rgbd_sanity_python_runner_tracks_progress(self) -> None:
        script = (REPO_ROOT / "scripts/run_clean_room_rgbd_sanity.py").read_text(
            encoding="utf-8"
        )

        self.assertIn(".symphony/progress/HEL-64.json", script)
        self.assertIn(".symphony/build-attempts/orbslam3-build-latest.json", script)
        self.assertIn(".symphony/build-attempts/orbslam3-build-latest.log", script)
        self.assertIn("build_progress_payload", script)
        self.assertIn("ORB_SLAM3_BUILD_TARGET", script)
        self.assertIn("ORB_SLAM3_APPEND_MARCH_NATIVE", script)
        self.assertIn("ORB_SLAM3_BUILD_PARALLELISM", script)
        self.assertIn("ORB_SLAM3_BUILD_CHANGED_VARIABLE", script)
        self.assertIn("limit ORB-SLAM3 compile parallelism to 1 job", script)
        self.assertIn("build phase completed without expected outputs", script)
        self.assertIn("fresh_execution_paths", script)

    def test_makefile_exposes_publish_rgbd_sanity_target(self) -> None:
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("publish-rgbd-sanity", makefile)
        self.assertIn("scripts/publish_rgbd_tum_sanity.py", makefile)

    def test_makefile_exposes_public_tum_vi_sanity_targets(self) -> None:
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn("fetch-tum-vi", makefile)
        self.assertIn("tum-vi-sanity", makefile)
        self.assertIn("scripts/fetch_tum_vi_dataset.py", makefile)
        self.assertIn("scripts/run_clean_room_public_tum_vi_sanity.sh", makefile)

    def test_clean_room_public_tum_vi_python_runner_tracks_progress(self) -> None:
        script = (
            REPO_ROOT / "scripts/run_clean_room_public_tum_vi_sanity.py"
        ).read_text(encoding="utf-8")

        self.assertIn(".symphony/progress/HEL-67.json", script)
        self.assertIn(".symphony/build-attempts/orbslam3-build-latest.json", script)
        self.assertIn(".symphony/build-attempts/orbslam3-build-latest.log", script)
        self.assertIn("build_progress_payload", script)
        self.assertIn("ORB_SLAM3_BUILD_TARGET", script)
        self.assertIn("ORB_SLAM3_APPEND_MARCH_NATIVE", script)
        self.assertIn("ORB_SLAM3_BUILD_PARALLELISM", script)
        self.assertIn("ORB_SLAM3_BUILD_TYPE", script)
        self.assertIn("ORB_SLAM3_ENABLE_ASAN", script)
        self.assertIn("ORB_SLAM3_ASAN_COMPILE_FLAGS", script)
        self.assertIn("ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT", script)
        self.assertIn("infer_progress_issue_id", script)
        self.assertIn('"ORB_SLAM3_PROGRESS_ARTIFACT": str(progress_artifact)', script)
        self.assertIn('"ORB_SLAM3_PROGRESS_ISSUE_ID": infer_progress_issue_id(', script)
        self.assertIn("ORB_SLAM3_BUILD_CHANGED_VARIABLE", script)
        self.assertIn('"ORB_SLAM3_BUILD_CHANGED_VARIABLE": os.environ.get(', script)
        self.assertIn('"ORB_SLAM3_BUILD_HYPOTHESIS": os.environ.get(', script)
        self.assertIn('"ORB_SLAM3_BUILD_SUCCESS_CRITERION": os.environ.get(', script)
        self.assertIn("public TUM-VI room1_512_16 archive", script)
        self.assertIn("fresh_execution_paths", script)

    def test_monocular_progress_monitor_supports_pid_and_jsonl_artifacts(self) -> None:
        script = (
            REPO_ROOT / "scripts/monitor_monocular_progress.py"
        ).read_text(encoding="utf-8")

        self.assertIn("--artifact", script)
        self.assertIn("--pid", script)
        self.assertIn("--poll-seconds", script)
        self.assertIn("summarize_monocular_runtime_log", script)
        self.assertIn("write_progress_snapshot", script)
        self.assertIn('"local_map_failure_count": summary.local_map_failure_count', script)
        self.assertIn('"latest_map_points": summary.latest_map_points', script)
        self.assertIn(
            'status = "completed" if summary.shutdown_completed else "failed"',
            script,
        )
