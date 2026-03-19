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
        self.assertIn('--target "${build_target}"', script)
        self.assertIn("-Wl,-rpath-link", script)
        self.assertIn("patch_orbslam3_baseline.py", script)

    def test_orbslam3_patch_helper_guards_empty_keyframe_saves(self) -> None:
        script = (REPO_ROOT / "scripts/patch_orbslam3_baseline.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("No keyframes were recorded; skipping trajectory save.", script)
        self.assertIn(
            "No keyframes were recorded; skipping keyframe trajectory save.", script
        )
        self.assertIn("Map* pBiggerMap = nullptr;", script)

    def test_monocular_runner_uses_trajectory_workdir_and_validates_outputs(self) -> None:
        script = (REPO_ROOT / "scripts/run_monocular_baseline.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("resolve_monocular_trajectory_outputs", script)
        self.assertIn("cwd=run_workdir", script)
        self.assertIn("without writing non-empty trajectory artifacts", script)

    def test_sequence_launcher_supports_rgbd_tum_mode(self) -> None:
        script = (REPO_ROOT / "scripts/run_orbslam3_sequence.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("rgbd_tum", script)
        self.assertIn("run_rgbd_tum_baseline.py", script)

    def test_clean_room_rgbd_sanity_script_covers_fetch_build_and_run(self) -> None:
        script = (REPO_ROOT / "scripts/run_clean_room_rgbd_sanity.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("run_clean_room_rgbd_sanity.py", script)

    def test_clean_room_rgbd_sanity_python_runner_tracks_progress(self) -> None:
        script = (REPO_ROOT / "scripts/run_clean_room_rgbd_sanity.py").read_text(
            encoding="utf-8"
        )

        self.assertIn(".symphony/progress/HEL-61.json", script)
        self.assertIn("build_progress_payload", script)
        self.assertIn("ORB_SLAM3_BUILD_TARGET", script)
        self.assertIn("fresh_execution_paths", script)
