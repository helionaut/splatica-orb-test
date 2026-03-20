from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.monocular_baseline import MonocularTrajectoryOutputs


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_monocular_baseline.py"
SPEC = importlib.util.spec_from_file_location("run_monocular_baseline", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
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
