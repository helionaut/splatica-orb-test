from __future__ import annotations

import re
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
RELATIVE_LINK_PATTERN = re.compile(
    r"\[[^]]+\]\((?!https?://|mailto:|#)([^)]+)\)"
)


class FinalValidationDocsTests(unittest.TestCase):
    def test_readme_links_final_validation_report(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("(docs/final-validation-report.md)", readme)
        self.assertIn(
            "(docs/hel-63-post-initialization-abort-follow-up.md)",
            readme,
        )
        self.assertIn("make check", readme)

    def test_final_report_records_canonical_baseline_and_verdict(self) -> None:
        report = (REPO_ROOT / "docs/final-validation-report.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Status: Final", report)
        self.assertIn("User rig verdict: `blocked`", report)
        self.assertIn("Checked-in repo rerun verdict: `validated`", report)
        self.assertIn(
            "4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4",
            report,
        )
        self.assertIn(
            "manifests/insta360_x3_lens10_monocular_baseline.json",
            report,
        )
        self.assertIn(
            "datasets/user/insta360_x3_one_lens_baseline/raw/video/{00.mp4,10.mp4}",
            report,
        )
        self.assertIn(
            "datasets/user/insta360_x3_one_lens_baseline/raw/calibration/",
            report,
        )
        self.assertIn(
            "datasets/user/insta360_x3_one_lens_baseline/lenses/10/import_manifest.json",
            report,
        )
        self.assertIn(
            "datasets/user/insta360_x3_one_lens_baseline/reports/ingest_report.md",
            report,
        )
        self.assertIn("Next follow-up task:", report)
        self.assertIn("Pangolin", report)
        self.assertIn("make check", report)
        self.assertIn("make monocular-prereqs", report)
        self.assertIn("./scripts/import_monocular_video_inputs.py", report)
        self.assertIn("./scripts/build_orbslam3_baseline.sh", report)
        self.assertIn("HEL-57 monocular follow-up report", report)
        self.assertIn("double free or corruption", report)
        self.assertIn("nFeatures: 4000", report)
        self.assertIn(
            "reports/out/insta360_x3_lens10_monocular_prereqs.md",
            report,
        )
        self.assertIn("Reference-Only Paths", report)
        self.assertNotIn("datasets/user/insta360_x3_lens10/", report)

    def test_hel57_follow_up_doc_records_narrowed_blocker(self) -> None:
        follow_up = (REPO_ROOT / "docs/hel-57-monocular-follow-up.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Issue: HEL-57", follow_up)
        self.assertIn("Map 0 has 0 KFs", follow_up)
        self.assertIn("double free or corruption (out)", follow_up)
        self.assertIn("New Map created with 93 points", follow_up)
        self.assertIn("New Map created with 83 points", follow_up)

    def test_hel63_follow_up_doc_records_diagnostic_lane(self) -> None:
        follow_up = (
            REPO_ROOT / "docs/hel-63-post-initialization-abort-follow-up.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-63", follow_up)
        self.assertIn("--output-tag", follow_up)
        self.assertIn("--frame-stride", follow_up)
        self.assertIn("--skip-frame-trajectory-save", follow_up)
        self.assertIn("--skip-keyframe-trajectory-save", follow_up)
        self.assertIn("HEL-63 diagnostic: entering SLAM shutdown", follow_up)
        self.assertIn(
            "ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE=1",
            follow_up,
        )
        self.assertIn(
            "ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE=1",
            follow_up,
        )

    def test_final_report_relative_links_resolve(self) -> None:
        source = REPO_ROOT / "docs/final-validation-report.md"
        text = source.read_text(encoding="utf-8")

        for link_target in RELATIVE_LINK_PATTERN.findall(text):
            resolved = (source.parent / link_target).resolve()
            self.assertTrue(
                resolved.exists(),
                f"docs/final-validation-report.md references missing {link_target}",
            )
