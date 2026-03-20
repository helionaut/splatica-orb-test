from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.clean_room_public_tum_vi import (
    build_progress_payload,
    fresh_execution_paths,
)
from splatica_orb_test.public_tum_vi import (
    build_tum_vi_monocular_calibration,
    estimate_tum_vi_fps,
    load_public_tum_vi_manifest,
    load_tum_vi_camera_txt,
    load_tum_vi_camera_rows,
    materialize_public_tum_vi_sequence,
    public_tum_vi_dataset_is_ready,
    resolve_public_tum_vi_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


CAMERA_TXT = """EquiDistant 0.373004838186 0.372994740336 0.498890050897 0.502729380663 0.00348238940225 0.000715034845216 -0.00205323614187 0.000202936735918
512 512
crop
512 512
"""


class PublicTumViManifestTests(unittest.TestCase):
    def test_loads_checked_in_manifest(self) -> None:
        manifest = load_public_tum_vi_manifest(
            REPO_ROOT / "manifests/tum_vi_room1_512_16_cam0_sanity.json"
        )

        self.assertEqual(manifest.sequence_name, "tum-vi-room1-512-16-cam0-sanity")
        self.assertEqual(manifest.dataset_name, "dataset-room1_512_16")
        self.assertEqual(manifest.camera_name, "cam0")
        self.assertIn("full motion-capture ground truth", manifest.notes)

    def test_resolves_expected_paths(self) -> None:
        manifest = load_public_tum_vi_manifest(
            REPO_ROOT / "manifests/tum_vi_room1_512_16_cam0_sanity.json"
        )
        resolved = resolve_public_tum_vi_paths(REPO_ROOT, manifest)

        self.assertEqual(
            resolved.camera_model,
            REPO_ROOT
            / "datasets/public/tum_vi/dataset-room1_512_16/dso/cam0/camera.txt",
        )
        self.assertEqual(
            resolved.summary_json,
            REPO_ROOT / "reports/out/tum_vi_room1_512_16_cam0_summary.json",
        )


class PublicTumViMaterializationTests(unittest.TestCase):
    def test_loads_camera_txt_and_builds_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            camera_path = Path(tmpdir) / "camera.txt"
            camera_path.write_text(CAMERA_TXT, encoding="utf-8")
            rows = [(1, "1.png"), (50_000_001, "2.png"), (100_000_001, "3.png")]

            parsed = load_tum_vi_camera_txt(camera_path)
            calibration = build_tum_vi_monocular_calibration(
                camera_label="tum_vi_room1_512_16_cam0",
                fps=estimate_tum_vi_fps(rows),
                notes="Synthetic public TUM-VI test.",
                camera_model=parsed,
            )

        self.assertEqual(calibration["camera"]["model"], "KannalaBrandt8")
        self.assertEqual(calibration["camera"]["image_width"], 512)
        self.assertEqual(calibration["camera"]["fps"], 20.0)
        self.assertAlmostEqual(
            calibration["camera"]["distortion"]["k4"],
            0.000202936735918,
        )

    def test_loads_camera_rows_and_materializes_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            repo_root = tmp_root / "repo"
            repo_root.mkdir()
            manifest_path = repo_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "baseline": {
                            "name": "orbslam3-upstream-master",
                            "repo_url": "https://github.com/UZ-SLAMLab/ORB_SLAM3",
                            "commit": "4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4",
                            "checkout_path": "third_party/orbslam3/upstream",
                            "executable_path": "Examples/Monocular/mono_tum_vi",
                            "vocabulary_path": "Vocabulary/ORBvoc.txt",
                        },
                        "sequence": {
                            "name": "synthetic-room1",
                            "camera_label": "tum_vi_room1_512_16_cam0",
                            "calibration_path": "build/materialized/cam0_calibration.json",
                            "frame_index_path": "build/materialized/cam0_frame_index.csv",
                        },
                        "public_dataset": {
                            "archive_url": "https://example.invalid/dataset.tar",
                            "archive_path": "datasets/public/tum_vi/dataset.tar",
                            "dataset_name": "dataset-room1_512_16",
                            "dataset_root": "datasets/public/tum_vi/dataset-room1_512_16",
                            "camera": "cam0",
                        },
                        "outputs": {
                            "image_dir": "build/mono/images",
                            "log_path": "logs/out/synthetic.log",
                            "report_path": "reports/out/synthetic.md",
                            "settings_path": "build/mono/settings.yaml",
                            "summary_json_path": "reports/out/synthetic_summary.json",
                            "timestamps_path": "build/mono/timestamps.txt",
                            "trajectory_plot_path": "reports/out/synthetic_trajectory.svg",
                            "trajectory_stem": "build/mono/trajectory/synthetic",
                            "visual_report_path": "reports/out/synthetic.html",
                        },
                        "launch": {
                            "mode": "monocular_tum_vi",
                            "script": "scripts/run_orbslam3_sequence.sh",
                        },
                        "notes": "Synthetic room test.",
                    }
                ),
                encoding="utf-8",
            )

            dataset_root = (
                repo_root / "datasets/public/tum_vi/dataset-room1_512_16/mav0/cam0"
            )
            (dataset_root / "data").mkdir(parents=True)
            (dataset_root / "data.csv").write_text(
                "\n".join(
                    [
                        "#timestamp [ns],filename",
                        "1,1.png",
                        "2,2.png",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            camera_model = repo_root / "datasets/public/tum_vi/dataset-room1_512_16/dso/cam0"
            camera_model.mkdir(parents=True)
            (camera_model / "camera.txt").write_text(CAMERA_TXT, encoding="utf-8")
            (dataset_root / "data/1.png").write_text("frame-1", encoding="utf-8")
            (dataset_root / "data/2.png").write_text("frame-2", encoding="utf-8")

            manifest = load_public_tum_vi_manifest(manifest_path)
            resolved = resolve_public_tum_vi_paths(repo_root, manifest)
            rows = load_tum_vi_camera_rows(resolved.data_csv)
            materialized = materialize_public_tum_vi_sequence(
                manifest=manifest,
                resolved=resolved,
            )
            dataset_ready = public_tum_vi_dataset_is_ready(resolved)

            calibration = json.loads(resolved.calibration.read_text(encoding="utf-8"))
            frame_index = resolved.frame_index.read_text(encoding="utf-8")

        self.assertTrue(dataset_ready)
        self.assertEqual(rows, [(1, "1.png"), (2, "2.png")])
        self.assertEqual(materialized.frame_count, 2)
        self.assertEqual(materialized.first_timestamp_ns, 1)
        self.assertEqual(materialized.last_timestamp_ns, 2)
        self.assertEqual(calibration["camera"]["label"], "tum_vi_room1_512_16_cam0")
        self.assertIn("timestamp_ns,source_path", frame_index)
        self.assertIn(str((dataset_root / "data/1.png").resolve()), frame_index)


class CleanRoomPublicTumViTests(unittest.TestCase):
    def test_progress_payload_reports_phase_completion(self) -> None:
        payload = build_progress_payload(
            artifacts={"runner": "scripts/run_clean_room_public_tum_vi_sanity.py"},
            current_step="materializing public TUM-VI cam0 calibration and frame index",
            completed=7,
            status="in_progress",
        )

        self.assertEqual(payload["status"], "in_progress")
        self.assertEqual(payload["completed"], 7)
        self.assertEqual(payload["total"], 10)
        self.assertEqual(payload["progress_percent"], 70)

    def test_fresh_execution_paths_cover_dataset_and_outputs(self) -> None:
        manifest = load_public_tum_vi_manifest(
            REPO_ROOT / "manifests/tum_vi_room1_512_16_cam0_sanity.json"
        )

        paths = fresh_execution_paths(
            REPO_ROOT,
            manifest,
            orchestration_log=REPO_ROOT / "logs/out/tum_vi_room1_512_16_orchestration.log",
        )
        path_text = {str(path.relative_to(REPO_ROOT)) for path in paths}

        self.assertIn("third_party/orbslam3/upstream", path_text)
        self.assertIn("datasets/public/tum_vi/dataset-room1_512_16", path_text)
        self.assertIn("build/tum_vi_room1_512_16/materialized/cam0_calibration.json", path_text)
        self.assertIn("reports/out/tum_vi_room1_512_16_cam0_summary.json", path_text)
