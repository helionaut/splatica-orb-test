from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.rgbd_tum_publish import publish_rgbd_tum_bundle


class RgbdTumPublishTests(unittest.TestCase):
    def test_publish_bundle_preserves_repo_relative_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            summary_path = repo_root / "reports/out/tum_rgbd_fr1_xyz_summary.json"
            visual_report = repo_root / "reports/out/tum_rgbd_fr1_xyz.html"
            markdown_report = repo_root / "reports/out/tum_rgbd_fr1_xyz.md"
            plot = repo_root / "reports/out/tum_rgbd_fr1_xyz_trajectory.svg"
            camera = repo_root / "build/tum_rgbd_fr1_xyz/trajectory/CameraTrajectory.txt"
            keyframe = repo_root / "build/tum_rgbd_fr1_xyz/trajectory/KeyFrameTrajectory.txt"
            log = repo_root / "logs/out/tum_rgbd_fr1_xyz.log"
            sample = repo_root / "datasets/public/tum_rgbd/rgbd_dataset_freiburg1_xyz/rgb/1.png"

            for path in (visual_report, markdown_report, plot, camera, keyframe, log, sample):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(path.name, encoding="utf-8")

            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(
                json.dumps(
                    {
                        "repo": {
                            "head_sha": "abc123",
                        },
                        "baseline": {
                            "commit": "4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4",
                            "settings_path": "third_party/orbslam3/upstream/Examples/RGB-D/TUM1.yaml",
                        },
                        "sequence": {
                            "association_count": 792,
                            "association_path": "third_party/orbslam3/upstream/Examples/RGB-D/associations/fr1_xyz.txt",
                            "sample_frame_paths": [
                                "datasets/public/tum_rgbd/rgbd_dataset_freiburg1_xyz/rgb/1.png"
                            ]
                        },
                        "run": {
                            "manifest_path": "manifests/tum_rgbd_fr1_xyz_sanity.json",
                            "command_display": "./scripts/run_rgbd_tum_baseline.py --manifest manifests/tum_rgbd_fr1_xyz_sanity.json",
                        },
                        "metrics": {
                            "camera_trajectory": {
                                "point_count": 798,
                                "path_length_meters": 12.5,
                                "displacement_meters": 6.25,
                                "duration_seconds": 26.4,
                                "min_x": 0.0,
                                "max_x": 1.0,
                                "min_y": 0.0,
                                "max_y": 2.0,
                                "min_z": 0.0,
                                "max_z": 3.0,
                            },
                            "keyframe_trajectory": {
                                "point_count": 146,
                                "duration_seconds": 26.4,
                            },
                            "camera_to_association_ratio": 1.0,
                        },
                        "result": {
                            "known_good_baseline_verdict": "useful",
                            "known_good_baseline_reason": "Non-empty trajectories were produced.",
                            "final_exit_code": 0,
                        },
                        "artifacts": {
                            "visual_report": {"path": "reports/out/tum_rgbd_fr1_xyz.html", "exists": True, "size_bytes": 1},
                            "markdown_report": {"path": "reports/out/tum_rgbd_fr1_xyz.md", "exists": True, "size_bytes": 1},
                            "summary_json": {"path": "reports/out/tum_rgbd_fr1_xyz_summary.json", "exists": True, "size_bytes": 1},
                            "trajectory_plot": {"path": "reports/out/tum_rgbd_fr1_xyz_trajectory.svg", "exists": True, "size_bytes": 1},
                            "camera_trajectory": {"path": "build/tum_rgbd_fr1_xyz/trajectory/CameraTrajectory.txt", "exists": True, "size_bytes": 1},
                            "keyframe_trajectory": {"path": "build/tum_rgbd_fr1_xyz/trajectory/KeyFrameTrajectory.txt", "exists": True, "size_bytes": 1},
                            "log": {"path": "logs/out/tum_rgbd_fr1_xyz.log", "exists": True, "size_bytes": 1},
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            publish_dir = repo_root / "reports/published/tum_rgbd_fr1_xyz_sanity"
            manifest = publish_rgbd_tum_bundle(
                publish_dir=publish_dir,
                repo_root=repo_root,
                summary_path=summary_path,
            )

            self.assertEqual(manifest["published_entrypoint"], "index.html")
            self.assertTrue((publish_dir / "index.html").exists())
            self.assertTrue((publish_dir / "artifact-manifest.json").exists())
            self.assertTrue(
                (
                    publish_dir
                    / "reports/out/tum_rgbd_fr1_xyz.html"
                ).exists()
            )
            self.assertTrue(
                (
                    publish_dir
                    / "build/tum_rgbd_fr1_xyz/trajectory/CameraTrajectory.txt"
                ).exists()
            )
            self.assertTrue(
                (
                    publish_dir
                    / "datasets/public/tum_rgbd/rgbd_dataset_freiburg1_xyz/rgb/1.png"
                ).exists()
            )
