from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from splatica_orb_test.monocular_baseline import MonocularTrajectoryOutputs


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_monocular_baseline.py"
SPEC = importlib.util.spec_from_file_location("run_monocular_baseline", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RunMonocularBaselineTests(unittest.TestCase):
    def test_render_runtime_progress_includes_experiment_contract(self) -> None:
        payload = MODULE.render_runtime_progress(
            artifacts={"report_path": "reports/out/example.md"},
            issue="HEL-70",
            status="in_progress",
            current_step="frame 93 TrackMonocular start",
            completed=93,
            total=270,
            metrics={"command": "./scripts/run_monocular_baseline.py"},
            experiment={
                "changed_variable": "apply the HEL-68 Jacobian lifetime fix",
                "hypothesis": "the aggressive lane will survive first-map creation",
                "success_criterion": "trajectory artifacts are written",
                "abort_condition": "the process aborts again before save",
                "expected_artifact": "build/insta360_x3_lens10/monocular/trajectory/f_insta360_x3_lens10.txt",
            },
        )

        self.assertEqual(payload["progress_percent"], 34)
        self.assertEqual(payload["experiment"]["changed_variable"], "apply the HEL-68 Jacobian lifetime fix")
        self.assertEqual(
            payload["experiment"]["expected_artifact"],
            "build/insta360_x3_lens10/monocular/trajectory/f_insta360_x3_lens10.txt",
        )

    def test_skipped_trajectory_outputs_are_not_treated_as_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            outputs = MonocularTrajectoryOutputs(
                frame_trajectory=tmp_path / "f_example.txt",
                keyframe_trajectory=tmp_path / "kf_example.txt",
            )

            details, missing = MODULE.inspect_trajectory_outputs(
                outputs,
                skip_frame_trajectory_save=True,
                skip_keyframe_trajectory_save=True,
                path_renderer=str,
            )

        self.assertEqual(missing, [])
        self.assertIn("Frame trajectory: intentionally skipped", details[0])
        self.assertIn("Keyframe trajectory: intentionally skipped", details[1])

    def test_required_trajectory_outputs_still_fail_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            keyframe_path = tmp_path / "kf_example.txt"
            keyframe_path.write_text("kf", encoding="utf-8")
            outputs = MonocularTrajectoryOutputs(
                frame_trajectory=tmp_path / "f_example.txt",
                keyframe_trajectory=keyframe_path,
            )

            details, missing = MODULE.inspect_trajectory_outputs(
                outputs,
                skip_frame_trajectory_save=False,
                skip_keyframe_trajectory_save=False,
                path_renderer=str,
            )

        self.assertEqual(missing, [outputs.frame_trajectory])
        self.assertIn("Frame trajectory: missing at", details[0])
        self.assertIn("Keyframe trajectory:", details[1])

    def test_runtime_log_summary_records_maps_resets_and_asan_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "run.log"
            log_path.write_text(
                "\n".join(
                    [
                        "New Map created with 93 points",
                        "SYSTEM-> Reseting active map in monocular case",
                        "HEL-75 diagnostic: trajectory save cwd=/tmp/trajectory",
                        "Saving trajectory to f_example.txt ...",
                        "HEL-63 diagnostic: SaveTrajectoryEuRoC completed",
                        "HEL-75 diagnostic: SaveTrajectoryEuRoC post_close open=1, bytes=321, filename=f_example.txt",
                        "Saving keyframe trajectory to kf_example.txt ...",
                        "No keyframes were recorded; skipping keyframe trajectory save.",
                        "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed",
                        "HEL-75 diagnostic: SaveKeyFrameTrajectoryEuRoC post_close open=0, bytes=-1, filename=kf_example.txt",
                        "SUMMARY: AddressSanitizer: 123 byte(s) leaked in 4 allocation(s).",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = MODULE.summarize_runtime_log(log_path)
            details = MODULE.render_runtime_log_details(summary)

        self.assertEqual(summary.map_points, (93,))
        self.assertEqual(summary.reset_count, 1)
        self.assertEqual(summary.trajectory_save_cwd, "/tmp/trajectory")
        self.assertTrue(summary.frame_trajectory_save_completed)
        self.assertTrue(summary.frame_trajectory_post_close_open)
        self.assertEqual(summary.frame_trajectory_post_close_bytes, 321)
        self.assertTrue(summary.keyframe_trajectory_save_completed)
        self.assertFalse(summary.keyframe_trajectory_post_close_open)
        self.assertEqual(summary.keyframe_trajectory_post_close_bytes, -1)
        self.assertTrue(summary.keyframe_trajectory_skipped)
        self.assertEqual(
            summary.asan_summary,
            "123 byte(s) leaked in 4 allocation(s).",
        )
        self.assertIn("Initialization maps created: 1 (points=93)", details)
        self.assertIn("Active map resets observed: 1", details)
        self.assertIn("Trajectory save cwd reported: /tmp/trajectory", details)
        self.assertIn("Frame trajectory save call reached completion", details)
        self.assertIn(
            "Frame trajectory post-close visibility: open=True, bytes=321",
            details,
        )
        self.assertIn(
            "Keyframe trajectory save skipped because no keyframes were recorded",
            details,
        )
        self.assertIn(
            "AddressSanitizer summary: 123 byte(s) leaked in 4 allocation(s).",
            details,
        )

    def test_resolve_runtime_saved_path_uses_reported_cwd_for_relative_outputs(self) -> None:
        runtime_path = MODULE.resolve_runtime_saved_path(
            save_cwd="/tmp/trajectory",
            save_path="f_example.txt",
        )

        self.assertEqual(runtime_path, Path("/tmp/trajectory/f_example.txt"))
