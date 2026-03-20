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

    def test_orbslam3_build_targets_mono_tum_vi(self) -> None:
        script = (REPO_ROOT / "scripts/build_orbslam3_baseline.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('build_target="${ORB_SLAM3_BUILD_TARGET:-mono_tum_vi}"', script)
        self.assertIn('append_march_native="${ORB_SLAM3_APPEND_MARCH_NATIVE:-OFF}"', script)
        self.assertIn('build_parallelism="${ORB_SLAM3_BUILD_PARALLELISM:-1}"', script)
        self.assertIn('build_experiment="${ORB_SLAM3_BUILD_EXPERIMENT:-orbslam3-${build_target}-portable-build}"', script)
        self.assertIn('changed_variable="${ORB_SLAM3_BUILD_CHANGED_VARIABLE:-disable -march=native and capture build-attempt signature}"', script)
        self.assertIn('allow_identical_retry="${ORB_SLAM3_ALLOW_IDENTICAL_RETRY:-0}"', script)
        self.assertIn('resolve_example_artifact_paths() {', script)
        self.assertIn('Examples/Monocular/${1}', script)
        self.assertIn('Examples/RGB-D/${1}', script)
        self.assertIn('build_example_source_path="${build_example_artifacts[1]}"', script)
        self.assertIn('"example_entrypoint": sha256(example_source_path)', script)
        self.assertIn(".symphony/build-attempts", script)
        self.assertIn("orbslam3-build-latest.log", script)
        self.assertIn("dmesg -T", script)
        self.assertIn("--verbose", script)
        self.assertIn("Build PID:", script)
        self.assertIn("Kernel OOM evidence detected", script)
        self.assertIn("Identical retry rejected", script)
        self.assertIn("--target", script)
        self.assertIn('"${build_target}"', script)
        self.assertIn("-Wl,-rpath-link", script)
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
            'set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -march=native")',
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

    def test_monocular_runner_uses_trajectory_workdir_and_validates_outputs(self) -> None:
        script = (REPO_ROOT / "scripts/run_monocular_baseline.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("resolve_monocular_trajectory_outputs", script)
        self.assertIn("cwd=run_workdir", script)
        self.assertIn("without writing non-empty trajectory artifacts", script)
        self.assertIn("--frame-stride", script)
        self.assertIn("--output-tag", script)
        self.assertIn("--skip-frame-trajectory-save", script)

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
        self.assertIn("ORB_SLAM3_BUILD_CHANGED_VARIABLE", script)
        self.assertIn("public TUM-VI room1_512_16 archive", script)
        self.assertIn("fresh_execution_paths", script)
