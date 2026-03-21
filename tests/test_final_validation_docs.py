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
        self.assertIn("(docs/hel-72-asan-static-alignment-follow-up.md)", readme)
        self.assertIn("(docs/hel-73-private-aggressive-follow-up.md)", readme)
        self.assertIn("(docs/hel-74-private-asan-leak-follow-up.md)", readme)
        self.assertIn("(docs/hel-75-public-save-path-follow-up.md)", readme)
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
        self.assertIn("HEL-72 ASan plus no-static-alignment follow-up", report)
        self.assertIn("HEL-73 private aggressive follow-up", report)
        self.assertIn("HEL-74 private ASan leak follow-up", report)
        self.assertIn("HEL-75 public save-path probe follow-up", report)
        self.assertIn("double free or corruption", report)
        self.assertIn("nFeatures: 4000", report)
        self.assertIn("LeakSanitizer", report)
        self.assertIn("SaveTrajectoryEuRoC", report)
        self.assertIn("5437", report)
        self.assertIn("924", report)
        self.assertIn("post-close diagnostics", report)
        self.assertIn(
            "reports/out/insta360_x3_lens10_monocular_prereqs.md",
            report,
        )
        self.assertIn("scripts/run_private_monocular_followup.py", report)
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

    def test_hel72_follow_up_doc_records_asan_static_alignment_lane(self) -> None:
        follow_up = (
            REPO_ROOT / "docs/hel-72-asan-static-alignment-follow-up.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-72", follow_up)
        self.assertIn("ORB_SLAM3_ENABLE_ASAN=1", follow_up)
        self.assertIn("ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT=1", follow_up)
        self.assertIn("ORB_SLAM3_ASAN_COMPILE_FLAGS", follow_up)
        self.assertIn("run_clean_room_public_tum_vi_sanity.py", follow_up)
        self.assertIn(".symphony/progress/HEL-72.json", follow_up)
        self.assertIn(".symphony/progress/HEL-72.jsonl", follow_up)
        self.assertIn("scripts/monitor_monocular_progress.py", follow_up)
        self.assertIn("monocular_runtime_progress.py", follow_up)
        self.assertIn("datasets/user/README.md", follow_up)
        self.assertIn("00.mp4", follow_up)
        self.assertIn("10.mp4", follow_up)
        self.assertIn("AddressSanitizer", follow_up)
        self.assertIn("frame 638", follow_up)
        self.assertIn("Fail to track local map!", follow_up)
        self.assertIn("Creation of new map with id: 1", follow_up)
        self.assertIn("157 points", follow_up)
        self.assertIn("*Merge detected", follow_up)
        self.assertIn("Local Mapping STOP", follow_up)
        self.assertIn("Change to map with id: 0", follow_up)
        self.assertIn("Local Mapping RELEASE", follow_up)
        self.assertIn("Merge finished!", follow_up)
        self.assertIn("run_with_progress_guard.py", follow_up)
        self.assertIn("asan_no_static_alignment_guarded_rerun", follow_up)
        self.assertIn("frame 2124", follow_up)
        self.assertIn("systemd-journald: Time jumped backwards, rotating.", follow_up)
        self.assertIn("last KF id: 70", follow_up)
        self.assertIn("155 points", follow_up)
        self.assertIn("SaveTrajectoryEuRoC", follow_up)
        self.assertIn("SaveKeyFrameTrajectoryEuRoC", follow_up)
        self.assertIn("Map 1 has 72 KFs", follow_up)
        self.assertIn("310392", follow_up)
        self.assertIn("8212", follow_up)
        self.assertIn("successful public rerun artifacts", follow_up)

    def test_hel73_follow_up_doc_records_private_blocker_and_runner(self) -> None:
        follow_up = (
            REPO_ROOT / "docs/hel-73-private-aggressive-follow-up.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-73", follow_up)
        self.assertIn("run_private_monocular_followup.py", follow_up)
        self.assertIn(".symphony/progress/HEL-73.json", follow_up)
        self.assertIn("AddressSanitizer", follow_up)
        self.assertIn("Eigen static alignment", follow_up)
        self.assertIn("00.mp4", follow_up)
        self.assertIn("10.mp4", follow_up)
        self.assertIn("insta360_x3_kb4_00_calib.txt", follow_up)
        self.assertIn("insta360_x3_extr_rigs_calib.json", follow_up)
        self.assertIn("blocked before the aggressive rerun could start", follow_up)
        self.assertIn("reports/out/hel-73_private_monocular_followup.md", follow_up)

    def test_hel74_follow_up_doc_records_shutdown_save_boundary(self) -> None:
        follow_up = (
            REPO_ROOT / "docs/hel-74-private-asan-leak-follow-up.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-74", follow_up)
        self.assertIn("AddressSanitizer", follow_up)
        self.assertIn("SaveTrajectoryEuRoC completed", follow_up)
        self.assertIn("No keyframes were recorded; skipping keyframe trajectory save.", follow_up)
        self.assertIn("598421471 byte(s) leaked in 2383336 allocation(s).", follow_up)
        self.assertIn("New Map created with 93 points", follow_up)
        self.assertIn("New Map created with 71 points", follow_up)
        self.assertIn("Reseting active map in monocular case", follow_up)
        self.assertIn("expected frame trajectory is still missing", follow_up)

    def test_hel75_follow_up_doc_records_public_save_probe(self) -> None:
        follow_up = (
            REPO_ROOT / "docs/hel-75-public-save-path-follow-up.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-75", follow_up)
        self.assertIn("--max-frames 140", follow_up)
        self.assertIn("hel75_save_probe_140", follow_up)
        self.assertIn("New Map created with 375 points", follow_up)
        self.assertIn("SaveTrajectoryEuRoC post_close open=1, bytes=5437", follow_up)
        self.assertIn(
            "SaveKeyFrameTrajectoryEuRoC post_close open=1, bytes=924",
            follow_up,
        )
        self.assertIn("7152947 byte(s) leaked in 16038 allocation(s).", follow_up)
        self.assertIn("private-lane-specific", follow_up)

    def test_hel76_follow_up_doc_records_private_save_comparison_lane(self) -> None:
        follow_up = (
            REPO_ROOT / "docs/hel-76-private-save-comparison-follow-up.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Issue: HEL-76", follow_up)
        self.assertIn("run_private_save_comparison_followup.py", follow_up)
        self.assertIn("make monocular-save-compare-followup", follow_up)
        self.assertIn(".symphony/progress/HEL-76.json", follow_up)
        self.assertIn("5437", follow_up)
        self.assertIn("924", follow_up)
        self.assertIn("insta360-b87308a3/00.mp4", follow_up)
        self.assertIn("insta360_x3_extr_rigs_calib.json", follow_up)

    def test_final_report_relative_links_resolve(self) -> None:
        source = REPO_ROOT / "docs/final-validation-report.md"
        text = source.read_text(encoding="utf-8")

        for link_target in RELATIVE_LINK_PATTERN.findall(text):
            resolved = (source.parent / link_target).resolve()
            self.assertTrue(
                resolved.exists(),
                f"docs/final-validation-report.md references missing {link_target}",
            )
