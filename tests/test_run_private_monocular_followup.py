from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_private_monocular_followup.py"
SPEC = importlib.util.spec_from_file_location(
    "run_private_monocular_followup",
    SCRIPT_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PrivateMonocularFollowupTests(unittest.TestCase):
    def test_resolve_source_inputs_prefers_explicit_overrides(self) -> None:
        dataset_root = Path("/tmp/repo/datasets/user/insta360_x3_one_lens_baseline")

        source_inputs = MODULE.resolve_source_inputs(
            dataset_root,
            video_00="/tmp/raw/00.mp4",
            video_10="/tmp/raw/10.mp4",
            calibration_00="/tmp/raw/insta360_x3_kb4_00_calib.txt",
            calibration_10="/tmp/raw/insta360_x3_kb4_10_calib.txt",
            extrinsics="/tmp/raw/insta360_x3_extr_rigs_calib.json",
        )

        self.assertEqual(source_inputs.video_00, Path("/tmp/raw/00.mp4"))
        self.assertEqual(source_inputs.video_10, Path("/tmp/raw/10.mp4"))
        self.assertEqual(
            source_inputs.calibration_00,
            Path("/tmp/raw/insta360_x3_kb4_00_calib.txt"),
        )
        self.assertEqual(
            source_inputs.calibration_10,
            Path("/tmp/raw/insta360_x3_kb4_10_calib.txt"),
        )
        self.assertEqual(
            source_inputs.extrinsics,
            Path("/tmp/raw/insta360_x3_extr_rigs_calib.json"),
        )

    def test_resolve_source_inputs_discovers_openclaw_sidecars_when_repo_raw_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dataset_root = tmp_path / "datasets/user/insta360_x3_one_lens_baseline"
            downloads_root = tmp_path / "downloads"
            inbound_root = tmp_path / "inbound"
            latest_bundle = downloads_root / "insta360-zulu"
            latest_bundle.mkdir(parents=True)
            inbound_root.mkdir()

            (latest_bundle / "00.mp4").write_text("00", encoding="utf-8")
            (latest_bundle / "10.mp4").write_text("10", encoding="utf-8")
            calibration_00 = (
                inbound_root / "insta360_x3_calib_insta360_x3_kb4_00_calib---latest.txt"
            )
            calibration_10 = (
                inbound_root / "insta360_x3_calib_insta360_x3_kb4_10_calib---latest.txt"
            )
            extrinsics = (
                inbound_root / "insta360_x3_calib_insta360_x3_extr_rigs_calib---latest.json"
            )
            calibration_00.write_text("00", encoding="utf-8")
            calibration_10.write_text("10", encoding="utf-8")
            extrinsics.write_text("{}", encoding="utf-8")

            source_inputs = MODULE.resolve_source_inputs(
                dataset_root,
                video_00=None,
                video_10=None,
                calibration_00=None,
                calibration_10=None,
                extrinsics=None,
                video_downloads_root=downloads_root,
                media_inbound_root=inbound_root,
            )

        self.assertEqual(source_inputs.video_00, latest_bundle / "00.mp4")
        self.assertEqual(source_inputs.video_10, latest_bundle / "10.mp4")
        self.assertEqual(source_inputs.calibration_00, calibration_00)
        self.assertEqual(source_inputs.calibration_10, calibration_10)
        self.assertEqual(source_inputs.extrinsics, extrinsics)

    def test_render_status_report_calls_out_missing_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            report_path = tmp_path / "reports/out/hel-73_private_monocular_followup.md"
            log_path = tmp_path / "logs/out/hel-73_private_monocular_followup.log"
            delegate_report = tmp_path / "reports/out/delegate.md"
            expected_artifact = tmp_path / "build/out/f_example.txt"
            missing_checks = (
                MODULE.PrerequisiteCheck(
                    label="Source calibration 00",
                    ready=False,
                    detail="/tmp/raw/insta360_x3_kb4_00_calib.txt",
                ),
                MODULE.PrerequisiteCheck(
                    label="Source stereo extrinsics",
                    ready=False,
                    detail="/tmp/raw/insta360_x3_extr_rigs_calib.json",
                ),
            )
            prerequisites = MODULE.MonocularBaselinePrerequisites(
                manifest_path=tmp_path / "manifests/example.json",
                raw_input_checks=(),
                prepare_checks=(),
                execute_checks=(),
            )

            report = MODULE.render_status_report(
                command="not started",
                dataset_root=tmp_path / "datasets/user/insta360_x3_one_lens_baseline",
                execution_blocked=True,
                execution_details=[
                    "Missing source inputs: Source calibration 00, Source stereo extrinsics",
                    "Next action: provide the missing raw source files or import the prepared lens-10 bundle into datasets/user/insta360_x3_one_lens_baseline/.",
                ],
                experiment={
                    "changed_variable": "HEL-57 aggressive ORB plus HEL-72 build toggles",
                    "expected_artifact": "build/insta360_x3_lens10/monocular/trajectory/f_example.txt",
                },
                issue_identifier="HEL-74",
                prerequisites=prerequisites,
                report_path=report_path,
                run_log_path=log_path,
                run_report_path=delegate_report,
                source_checks=missing_checks,
                trajectory_path=expected_artifact,
            )

        self.assertIn("Status: `blocked`", report)
        self.assertIn("# HEL-74 Private Monocular Follow-up Status", report)
        self.assertIn("Issue: HEL-74", report)
        self.assertIn("Source calibration 00: **missing**", report)
        self.assertIn("Source stereo extrinsics: **missing**", report)
        self.assertIn("Next action: provide the missing raw source files", report)
        self.assertIn("Expected trajectory artifact", report)
