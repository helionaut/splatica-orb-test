from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.rgbd_tum_baseline import (
    apply_rgbd_tum_output_tag,
    build_rgbd_tum_command,
    load_rgbd_tum_associations,
    load_rgbd_tum_baseline_manifest,
    load_tum_trajectory_points,
    render_tum_trajectory_svg,
    resolve_rgbd_tum_baseline_paths,
)
from splatica_orb_test.clean_room_rgbd_sanity import (
    build_progress_payload,
    fresh_execution_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class RgbdTumBaselineManifestTests(unittest.TestCase):
    def test_loads_checked_in_manifest(self) -> None:
        manifest = load_rgbd_tum_baseline_manifest(
            REPO_ROOT / "manifests/tum_rgbd_fr1_xyz_sanity.json"
        )

        self.assertEqual(manifest.sequence_name, "tum-rgbd-fr1-xyz-sanity")
        self.assertEqual(manifest.dataset_name, "rgbd_dataset_freiburg1_xyz")
        self.assertEqual(manifest.launch_script, "scripts/run_orbslam3_sequence.sh")

    def test_requires_top_level_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text(json.dumps({"baseline": {}}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Missing manifest section"):
                load_rgbd_tum_baseline_manifest(manifest_path)


class RgbdTumBaselinePathTests(unittest.TestCase):
    def test_resolves_paths_and_builds_command(self) -> None:
        manifest = load_rgbd_tum_baseline_manifest(
            REPO_ROOT / "manifests/tum_rgbd_fr1_xyz_sanity.json"
        )
        resolved = resolve_rgbd_tum_baseline_paths(REPO_ROOT, manifest)

        self.assertEqual(
            build_rgbd_tum_command(resolved),
            [
                str(resolved.executable),
                str(resolved.vocabulary),
                str(resolved.settings),
                str(resolved.dataset_root),
                str(resolved.association),
            ],
        )
        self.assertEqual(
            resolved.camera_trajectory,
            REPO_ROOT / "build/tum_rgbd_fr1_xyz/trajectory/CameraTrajectory.txt",
        )

    def test_applies_output_tag_to_rgbd_artifacts(self) -> None:
        manifest = load_rgbd_tum_baseline_manifest(
            REPO_ROOT / "manifests/tum_rgbd_fr1_xyz_sanity.json"
        )
        resolved = apply_rgbd_tum_output_tag(
            resolve_rgbd_tum_baseline_paths(REPO_ROOT, manifest),
            "no_viewer",
        )

        self.assertEqual(
            resolved.trajectory_dir,
            REPO_ROOT / "build/tum_rgbd_fr1_xyz/trajectory_no_viewer",
        )
        self.assertEqual(
            resolved.log,
            REPO_ROOT / "logs/out/tum_rgbd_fr1_xyz_no_viewer.log",
        )
        self.assertEqual(
            resolved.report,
            REPO_ROOT / "reports/out/tum_rgbd_fr1_xyz_no_viewer.md",
        )

    def test_loads_associations_and_trajectory_points(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            association_path = tmp_root / "fr1_xyz.txt"
            association_path.write_text(
                "\n".join(
                    [
                        "1.0 rgb/1.png 1.1 depth/1.png",
                        "2.0 rgb/2.png 2.1 depth/2.png",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            trajectory_path = tmp_root / "CameraTrajectory.txt"
            trajectory_path.write_text(
                "\n".join(
                    [
                        "1.0 0.0 0.0 0.0 0 0 0 1",
                        "2.0 1.0 0.2 2.0 0 0 0 1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            associations = load_rgbd_tum_associations(association_path)
            points = load_tum_trajectory_points(trajectory_path)

        self.assertEqual(len(associations), 2)
        self.assertEqual(associations[0].rgb_path, "rgb/1.png")
        self.assertEqual(points[-1][1:], (1.0, 0.2, 2.0))

    def test_renders_svg_with_polyline(self) -> None:
        svg = render_tum_trajectory_svg(
            [
                (1.0, 0.0, 0.0, 0.0),
                (2.0, 1.0, 0.0, 1.0),
                (3.0, 2.0, 0.0, 0.5),
            ],
            title="Trajectory",
        )

        self.assertIn("<polyline", svg)
        self.assertIn("Trajectory", svg)


class CleanRoomRgbdSanityTests(unittest.TestCase):
    def test_progress_payload_reports_phase_completion(self) -> None:
        payload = build_progress_payload(
            artifacts={"runner": "scripts/run_clean_room_rgbd_sanity.sh"},
            current_step="building upstream ORB-SLAM3 rgbd_tum target",
            completed=6,
            status="in_progress",
        )

        self.assertEqual(payload["status"], "in_progress")
        self.assertEqual(payload["completed"], 6)
        self.assertEqual(payload["total"], 8)
        self.assertEqual(payload["progress_percent"], 75)

    def test_fresh_execution_paths_cover_checkout_dataset_and_outputs(self) -> None:
        manifest = load_rgbd_tum_baseline_manifest(
            REPO_ROOT / "manifests/tum_rgbd_fr1_xyz_sanity.json"
        )

        paths = fresh_execution_paths(
            REPO_ROOT,
            manifest,
            orchestration_log=REPO_ROOT / "logs/out/tum_rgbd_fr1_xyz_orchestration.log",
        )
        path_text = {str(path.relative_to(REPO_ROOT)) for path in paths}

        self.assertIn("third_party/orbslam3/upstream", path_text)
        self.assertIn("datasets/public/tum_rgbd/rgbd_dataset_freiburg1_xyz", path_text)
        self.assertIn("build/tum_rgbd_fr1_xyz/trajectory", path_text)
        self.assertIn("logs/out/tum_rgbd_fr1_xyz_orchestration.log", path_text)
