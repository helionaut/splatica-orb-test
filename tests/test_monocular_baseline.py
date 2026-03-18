from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.monocular_baseline import (
    ORB_SLAM3_V1_0_RELEASE,
    build_monocular_tum_vi_command,
    load_monocular_baseline_manifest,
    load_monocular_calibration,
    prepare_monocular_sequence,
    render_monocular_settings_yaml,
    resolve_monocular_baseline_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_calibration(
    path: Path,
    *,
    color_order: str = "RGB",
    model: str = "KannalaBrandt8",
) -> None:
    path.write_text(
        json.dumps(
            {
                "camera": {
                    "label": "insta360_x3_lens10",
                    "model": model,
                    "image_width": 1920,
                    "image_height": 1920,
                    "fps": 30,
                    "color_order": color_order,
                    "intrinsics": {
                        "fx": 812.5,
                        "fy": 811.75,
                        "cx": 959.5,
                        "cy": 960.25,
                    },
                    "distortion": {
                        "k1": 0.0123,
                        "k2": -0.0011,
                        "k3": 0.00021,
                        "k4": -0.000031,
                    },
                },
                "orb": {
                    "n_features": 1800,
                    "scale_factor": 1.2,
                    "n_levels": 8,
                    "ini_fast": 18,
                    "min_fast": 7,
                },
                "viewer": {
                    "key_frame_size": 0.05,
                    "key_frame_line_width": 1.0,
                    "graph_line_width": 0.9,
                    "point_size": 2.0,
                    "camera_size": 0.08,
                    "camera_line_width": 3.0,
                    "viewpoint_x": 0.0,
                    "viewpoint_y": -0.7,
                    "viewpoint_z": -3.5,
                    "viewpoint_f": 500.0,
                },
                "notes": "Synthetic fixture for monocular baseline tests.",
            }
        ),
        encoding="utf-8",
    )


class MonocularBaselineManifestTests(unittest.TestCase):
    def test_loads_checked_in_monocular_baseline_manifest(self) -> None:
        manifest = load_monocular_baseline_manifest(
            REPO_ROOT / "manifests/insta360_x3_lens10_monocular_baseline.json"
        )

        self.assertEqual(manifest.baseline_commit, ORB_SLAM3_V1_0_RELEASE)
        self.assertEqual(manifest.executable_path, "Examples/Monocular/mono_tum_vi")
        self.assertEqual(manifest.launch_script, "scripts/run_orbslam3_sequence.sh")
        self.assertIn("without IMU", manifest.notes)


class MonocularCalibrationRenderingTests(unittest.TestCase):
    def test_renders_tum_vi_style_kannala_brandt_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            calibration_path = Path(tmpdir) / "calibration.json"
            write_calibration(calibration_path)

            calibration = load_monocular_calibration(calibration_path)
            settings = render_monocular_settings_yaml(calibration)

        self.assertIn('Camera.type: "KannalaBrandt8"', settings)
        self.assertIn("Camera.width: 1920", settings)
        self.assertIn("Camera.height: 1920", settings)
        self.assertIn("Camera.fps: 30", settings)
        self.assertIn("Camera1.fx: 812.5", settings)
        self.assertIn("Camera1.k4: -0.000031", settings)
        self.assertIn("ORBextractor.nFeatures: 1800", settings)
        self.assertIn("Viewer.ViewpointF: 500.0", settings)

    def test_accepts_kannala_brandt4_source_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            calibration_path = Path(tmpdir) / "calibration.json"
            write_calibration(calibration_path, model="kannalabrandt4")

            calibration = load_monocular_calibration(calibration_path)

        self.assertEqual(calibration.camera_model, "KannalaBrandt8")

    def test_requires_explicit_color_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            calibration_path = Path(tmpdir) / "calibration.json"
            write_calibration(calibration_path)
            raw = json.loads(calibration_path.read_text(encoding="utf-8"))
            raw["camera"].pop("color_order")
            calibration_path.write_text(json.dumps(raw), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "Missing calibration field: camera.color_order"
            ):
                load_monocular_calibration(calibration_path)


class MonocularSequencePreparationTests(unittest.TestCase):
    def test_prepares_monocular_sequence_with_timestamp_named_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_dir = tmp_path / "source"
            source_dir.mkdir()

            (source_dir / "frame-a.png").write_text("frame-a", encoding="utf-8")
            (source_dir / "frame-b.png").write_text("frame-b", encoding="utf-8")

            frame_index_path = tmp_path / "frame_index.csv"
            frame_index_path.write_text(
                "\n".join(
                    [
                        "timestamp_ns,source_path",
                        "1710000000000000000,source/frame-a.png",
                        "1710000000033333333,source/frame-b.png",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            image_dir = tmp_path / "prepared" / "images"
            timestamps_path = tmp_path / "prepared" / "timestamps.txt"

            prepared = prepare_monocular_sequence(
                frame_index_path,
                image_dir,
                timestamps_path,
            )

            self.assertEqual(prepared.frame_count, 2)
            self.assertEqual(prepared.first_timestamp_ns, 1710000000000000000)
            self.assertEqual(prepared.last_timestamp_ns, 1710000000033333333)
            self.assertEqual(
                (image_dir / "1710000000000000000.png").read_text(encoding="utf-8"),
                "frame-a",
            )
            self.assertEqual(
                (image_dir / "1710000000033333333.png").read_text(encoding="utf-8"),
                "frame-b",
            )
            self.assertEqual(
                timestamps_path.read_text(encoding="utf-8"),
                "1710000000000000000\n1710000000033333333\n",
            )

    def test_requires_strictly_increasing_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_dir = tmp_path / "source"
            source_dir.mkdir()
            (source_dir / "frame-a.png").write_text("frame-a", encoding="utf-8")
            (source_dir / "frame-b.png").write_text("frame-b", encoding="utf-8")

            frame_index_path = tmp_path / "frame_index.csv"
            frame_index_path.write_text(
                "\n".join(
                    [
                        "timestamp_ns,source_path",
                        "1710000000000000000,source/frame-a.png",
                        "1710000000000000000,source/frame-b.png",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "strictly increasing"):
                prepare_monocular_sequence(
                    frame_index_path,
                    tmp_path / "prepared" / "images",
                    tmp_path / "prepared" / "timestamps.txt",
                )


class MonocularCommandTests(unittest.TestCase):
    def test_builds_mono_tum_vi_command_from_manifest(self) -> None:
        manifest = load_monocular_baseline_manifest(
            REPO_ROOT / "manifests/insta360_x3_lens10_monocular_baseline.json"
        )
        resolved = resolve_monocular_baseline_paths(REPO_ROOT, manifest)

        self.assertEqual(
            build_monocular_tum_vi_command(resolved),
            [
                str(
                    REPO_ROOT
                    / "third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi"
                ),
                str(REPO_ROOT / "third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt"),
                str(
                    REPO_ROOT
                    / "build/insta360_x3_lens10/monocular/TUM-VI-insta360-x3-lens10.yaml"
                ),
                str(REPO_ROOT / "build/insta360_x3_lens10/monocular/images"),
                str(REPO_ROOT / "build/insta360_x3_lens10/monocular/timestamps.txt"),
                str(
                    REPO_ROOT
                    / "build/insta360_x3_lens10/monocular/trajectory/insta360_x3_lens10"
                ),
            ],
        )
