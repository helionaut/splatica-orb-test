from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class TumRgbdSanityDocsTests(unittest.TestCase):
    def test_readme_links_tum_rgbd_sanity_report_and_publish_target(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("(docs/tum-rgbd-sanity-report.md)", readme)
        self.assertIn("make publish-rgbd-sanity", readme)
        self.assertIn("reports/published/tum_rgbd_fr1_xyz_sanity/", readme)

    def test_tum_rgbd_sanity_report_records_verdict_metrics_and_artifacts(self) -> None:
        report = (REPO_ROOT / "docs/tum-rgbd-sanity-report.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Issue: HEL-64", report)
        self.assertIn("Published report verdict: `not_useful`", report)
        self.assertIn("double free or corruption (out)", report)
        self.assertIn("837", report)
        self.assertIn("associations", report.lower())
        self.assertIn("reports/published/tum_rgbd_fr1_xyz_sanity/index.html", report)
        self.assertIn("artifact-manifest.json", report)
        self.assertIn("CameraTrajectory.txt", report)
        self.assertIn("KeyFrameTrajectory.txt", report)
        self.assertIn("Acceptance Criteria Check", report)

    def test_publication_docs_record_pages_deploy_path(self) -> None:
        decision = (REPO_ROOT / "docs/publication-decision.md").read_text(
            encoding="utf-8"
        )
        verification = (REPO_ROOT / "docs/PRODUCTION_VERIFICATION.md").read_text(
            encoding="utf-8"
        )
        workflow = (
            REPO_ROOT / ".github/workflows/publish-rgbd-sanity.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("https://helionaut.github.io/splatica-orb-test/", decision)
        self.assertIn("reports/published/tum_rgbd_fr1_xyz_sanity/", decision)
        self.assertIn("make verify-production", verification)
        self.assertIn("https://helionaut.github.io/splatica-orb-test/", verification)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("actions/upload-pages-artifact@v3", workflow)
