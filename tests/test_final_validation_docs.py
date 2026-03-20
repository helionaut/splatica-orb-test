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
        self.assertIn("(docs/hel-68-asan-crash-follow-up.md)", readme)
        self.assertIn("(docs/hel-69-worktree-containment-follow-up.md)", readme)
        self.assertIn("(docs/hel-71-eigen-static-alignment-follow-up.md)", readme)
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
        self.assertIn("HEL-68 ASan crash follow-up", report)
        self.assertIn("HEL-71 Eigen static-alignment follow-up", report)
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
        self.assertIn("--max-frames", follow_up)
        self.assertIn("--disable-viewer", follow_up)
        self.assertIn("rgbd_tum", follow_up)
        self.assertIn("New Map created with 837 points", follow_up)
        self.assertIn("frame 0 TrackRGBD completed", follow_up)
        self.assertIn("frame 1 TrackRGBD start", follow_up)
        self.assertIn("HEL-63 diagnostic: frame <n> TrackRGBD", follow_up)
        self.assertIn("HEL-63 diagnostic: rgbd_tum disable_viewer=1", follow_up)
        self.assertIn("second `TrackRGBD` call", follow_up)
        self.assertIn("HEL-63 diagnostic: entering SLAM shutdown", follow_up)
        self.assertIn("ORB_SLAM3_HEL63_MAX_FRAMES=<N>", follow_up)
        self.assertIn(
            "ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE=1",
            follow_up,
        )
        self.assertIn(
            "ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE=1",
            follow_up,
        )

    def test_hel67_public_tum_vi_doc_records_runtime_blocker(self) -> None:
        report = (
            REPO_ROOT / "docs/reports/hel-67-public-tum-vi-room1-cam0.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-67", report)
        self.assertIn("dataset-room1_512_16", report)
        self.assertIn("room1_512_16", report)
        self.assertIn("mono_tum_vi", report)
        self.assertIn("2821", report)
        self.assertIn("New Map created with 375 points", report)
        self.assertIn("double free or corruption (out)", report)
        self.assertIn("exit code `134`", report)
        self.assertIn("No frame or keyframe trajectory files", report)
        self.assertIn("-march=native", report)
        self.assertIn("ulimit -c", report)

    def test_hel68_follow_up_doc_records_asan_lane(self) -> None:
        follow_up = (REPO_ROOT / "docs/hel-68-asan-crash-follow-up.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Issue: HEL-68", follow_up)
        self.assertIn("AddressSanitizer", follow_up)
        self.assertIn("ORB_SLAM3_ENABLE_ASAN=1", follow_up)
        self.assertIn("ORB_SLAM3_BUILD_TARGET=mono_tum_vi", follow_up)
        self.assertIn("ORB_SLAM3_ASAN_COMPILE_FLAGS", follow_up)
        self.assertIn("manifests/tum_vi_room1_512_16_cam0_sanity.json", follow_up)
        self.assertIn("run_monocular_baseline.py", follow_up)
        self.assertIn("--max-frames 20", follow_up)
        self.assertIn("ORB_SLAM3_HEL68_MAX_FRAMES", follow_up)
        self.assertIn("TrackMonocular", follow_up)
        self.assertIn("--skip-frame-trajectory-save", follow_up)
        self.assertIn("private lens-10 bundle", follow_up)
        self.assertIn("Out of memory: Killed process", follow_up)
        self.assertIn("asan_full_skip_save_r1", follow_up)
        self.assertIn("AddressSanitizer: stack-use-after-scope", follow_up)
        self.assertIn("EdgeSE3ProjectXYZ::linearizeOplus()", follow_up)
        self.assertIn("OptimizableTypes.cpp:152", follow_up)
        self.assertIn("frame `93`", follow_up)

    def test_hel69_follow_up_doc_records_checkout_containment_blocker(self) -> None:
        follow_up = (
            REPO_ROOT / "docs/hel-69-worktree-containment-follow-up.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-69", follow_up)
        self.assertIn("Runner libORB_SLAM3 linkage", follow_up)
        self.assertIn("HEL-68-restacked", follow_up)
        self.assertIn("third_party/orbslam3/upstream", follow_up)
        self.assertIn("HEL-68-repo/third_party/orbslam3/upstream/build", follow_up)
        self.assertIn(".symphony/build-attempts/orbslam3-build-20260320T145253Z.log", follow_up)
        self.assertIn(".symphony/progress/HEL-69.json", follow_up)

    def test_hel71_follow_up_doc_records_static_alignment_lane(self) -> None:
        follow_up = (
            REPO_ROOT / "docs/hel-71-eigen-static-alignment-follow-up.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-71", follow_up)
        self.assertIn("ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1", follow_up)
        self.assertIn("hel-71-eigen-static-alignment-public-tum-vi", follow_up)
        self.assertIn("disable_eigen_static_alignment: true", follow_up)
        self.assertIn("frame `93`", follow_up)
        self.assertIn("New Map created with 375 points", follow_up)
        self.assertIn("Segmentation fault (core dumped)", follow_up)
        self.assertIn(".symphony/progress/HEL-71.json", follow_up)
        self.assertIn("logs/out/tum_vi_room1_512_16_cam0.log", follow_up)
        self.assertIn(
            ".symphony/build-attempts/orbslam3-build-20260320T225148Z.json",
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
