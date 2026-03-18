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
        self.assertIn("local-only input bundle", report)
        self.assertIn("Pangolin", report)
        self.assertIn("make check", report)
        self.assertIn("make monocular-prereqs", report)
        self.assertIn("./scripts/build_orbslam3_baseline.sh", report)
        self.assertIn(
            "reports/out/insta360_x3_lens10_monocular_prereqs.md",
            report,
        )
        self.assertIn("Reference-Only Paths", report)

    def test_final_report_relative_links_resolve(self) -> None:
        source = REPO_ROOT / "docs/final-validation-report.md"
        text = source.read_text(encoding="utf-8")

        for link_target in RELATIVE_LINK_PATTERN.findall(text):
            resolved = (source.parent / link_target).resolve()
            self.assertTrue(
                resolved.exists(),
                f"docs/final-validation-report.md references missing {link_target}",
            )
