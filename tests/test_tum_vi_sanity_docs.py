from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class TumViSanityDocsTests(unittest.TestCase):
    def test_readme_links_tum_vi_sanity_report_and_make_target(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("(docs/reports/hel-67-public-tum-vi-room1-cam0.md)", readme)
        self.assertIn("make fetch-tum-vi", readme)
        self.assertIn("make tum-vi-sanity", readme)
        self.assertIn("manifests/tum_vi_room1_512_16_cam0_sanity.json", readme)

    def test_tum_vi_sanity_report_records_runtime_blocker_and_artifacts(self) -> None:
        report = (
            REPO_ROOT / "docs/reports/hel-67-public-tum-vi-room1-cam0.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-67", report)
        self.assertIn("Public TUM-VI `mono_tum_vi` Sanity Report", report)
        self.assertIn("dataset-room1_512_16", report)
        self.assertIn("dso/cam0/camera.txt", report)
        self.assertIn("mav0/cam0", report)
        self.assertIn("2821", report)
        self.assertIn("375", report)
        self.assertIn("double free or corruption (out)", report)
        self.assertIn("Runtime exit code: `134`", report)
        self.assertIn("orbslam3-build-latest.json", report)
        self.assertIn("f_tum_vi_room1_512_16_cam0.txt", report)
        self.assertIn("kf_tum_vi_room1_512_16_cam0.txt", report)
        self.assertIn("Minimal Reproducible Failure Boundary", report)
