from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_private_save_comparison_followup.py"
SPEC = importlib.util.spec_from_file_location(
    "run_private_save_comparison_followup",
    SCRIPT_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PrivateSaveComparisonFollowupTests(unittest.TestCase):
    def test_discover_openclaw_video_inputs_prefers_complete_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            downloads_root = Path(tmpdir)
            incomplete = downloads_root / "insta360-alpha"
            incomplete.mkdir()
            (incomplete / "00.mp4").write_text("00", encoding="utf-8")

            complete = downloads_root / "insta360-zulu"
            complete.mkdir()
            (complete / "00.mp4").write_text("00", encoding="utf-8")
            (complete / "10.mp4").write_text("10", encoding="utf-8")

            video_00, video_10 = MODULE.discover_openclaw_video_inputs(downloads_root)

        self.assertEqual(video_00, complete / "00.mp4")
        self.assertEqual(video_10, complete / "10.mp4")

    def test_discover_openclaw_calibration_inputs_prefers_matching_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            inbound_root = Path(tmpdir)
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

            discovered = MODULE.discover_openclaw_calibration_inputs(inbound_root)

        self.assertEqual(discovered, (calibration_00, calibration_10, extrinsics))

    def test_parse_private_run_evidence_reads_missing_sources_and_delegate_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            delegate_report = tmp_path / "reports/out/delegate.md"
            delegate_report.parent.mkdir(parents=True)
            delegate_report.write_text(
                "\n".join(
                    [
                        "- Trajectory save cwd reported: /tmp/private/trajectory",
                        "- Frame trajectory post-close visibility: open=False, bytes=0",
                        "- Keyframe trajectory post-close visibility: open=True, bytes=12",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            status_report = tmp_path / "reports/out/status.md"
            status_report.write_text(
                "\n".join(
                    [
                        "- Status: `blocked`",
                        "- Orchestration log: `logs/out/private.log`",
                        f"- Delegate monocular report: `{delegate_report}`",
                        "- Source calibration 00: **missing** (`/tmp/raw/insta360_x3_kb4_00_calib.txt`)",
                        "- Source stereo extrinsics: **missing** (`/tmp/raw/insta360_x3_extr_rigs_calib.json`)",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            evidence = MODULE.parse_private_run_evidence(status_report)

        self.assertEqual(evidence.status, "blocked")
        self.assertEqual(
            evidence.missing_sources,
            ("Source calibration 00", "Source stereo extrinsics"),
        )
        self.assertEqual(evidence.save_cwd, "/tmp/private/trajectory")
        self.assertFalse(evidence.frame_post_close_open)
        self.assertEqual(evidence.frame_post_close_bytes, 0)
        self.assertTrue(evidence.keyframe_post_close_open)
        self.assertEqual(evidence.keyframe_post_close_bytes, 12)

    def test_render_status_report_records_reference_and_blocker(self) -> None:
        report = MODULE.render_status_report(
            issue_identifier="HEL-77",
            command="python3 scripts/run_private_monocular_followup.py",
            delegate_exit_code=1,
            downloads_root=Path("/tmp/downloads"),
            public_reference=MODULE.PublicSaveReference(
                issue_identifier="HEL-75",
                report_path=Path("docs/hel-75-public-save-path-follow-up.md"),
                save_cwd="build/tum_vi_room1_512_16/monocular/trajectory_hel75_save_probe_140",
                frame_bytes=5437,
                keyframe_bytes=924,
            ),
            private_evidence=MODULE.PrivateRunEvidence(
                status="blocked",
                missing_sources=("Source calibration 00", "Source stereo extrinsics"),
                save_cwd=None,
                frame_post_close_open=None,
                frame_post_close_bytes=None,
                keyframe_post_close_open=None,
                keyframe_post_close_bytes=None,
                delegate_report_path=Path("reports/out/delegate.md"),
                delegate_log_path=Path("logs/out/private.log"),
            ),
            discovered_video_00=Path("/tmp/downloads/insta360-b87308a3/00.mp4"),
            discovered_video_10=Path("/tmp/downloads/insta360-b87308a3/10.mp4"),
            discovered_calibration_00=Path("/tmp/inbound/insta360_x3_kb4_00_calib.txt"),
            discovered_calibration_10=Path("/tmp/inbound/insta360_x3_kb4_10_calib.txt"),
            discovered_extrinsics=Path("/tmp/inbound/insta360_x3_extr_rigs_calib.json"),
            orchestration_log=Path("logs/out/hel-76.log"),
            status_report=Path("reports/out/hel-76.md"),
            delegate_status_report=Path("reports/out/hel-76_private_monocular_followup.md"),
        )

        self.assertIn("# HEL-77 Private Save Comparison Follow-up", report)
        self.assertIn("Issue: HEL-77", report)
        self.assertIn(
            "Delegate status report: `reports/out/hel-76_private_monocular_followup.md`",
            report,
        )
        self.assertIn("Reference frame post-close bytes: `5437`", report)
        self.assertIn("Reference keyframe post-close bytes: `924`", report)
        self.assertIn("Raw video 00: `/tmp/downloads/insta360-b87308a3/00.mp4`", report)
        self.assertIn("Calibration 00: `/tmp/inbound/insta360_x3_kb4_00_calib.txt`", report)
        self.assertIn("Stereo extrinsics: `/tmp/inbound/insta360_x3_extr_rigs_calib.json`", report)
        self.assertIn("`Source calibration 00`", report)
        self.assertIn("private rerun is still blocked before save comparison", report)
