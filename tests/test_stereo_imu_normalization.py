from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.stereo_imu_normalization import (
    load_stereo_imu_normalization_manifest,
    normalize_stereo_imu_sequence,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_raw_sequence(root: Path) -> None:
    raw_root = root / "raw"
    source_root = raw_root / "source"
    left_source = source_root / "left"
    right_source = source_root / "right"
    left_source.mkdir(parents=True)
    right_source.mkdir(parents=True)

    (left_source / "frame-a.png").write_text("left-a", encoding="utf-8")
    (left_source / "frame-b.png").write_text("left-b", encoding="utf-8")
    (right_source / "frame-a.png").write_text("right-a", encoding="utf-8")
    (right_source / "frame-b.png").write_text("right-b", encoding="utf-8")

    (raw_root / "sequence.json").write_text(
        json.dumps(
            {
                "sequence_id": "fixture-stereo-imu-sequence",
                "rig": {
                    "left_camera": "cam_left",
                    "right_camera": "cam_right",
                    "imu": "imu0",
                },
                "timestamp_unit": "ns",
                "provenance": {
                    "source": "synthetic-fixture",
                    "notes": "Shareable fixture for HEL-46 normalization tests.",
                },
            }
        ),
        encoding="utf-8",
    )
    (raw_root / "left_frames.csv").write_text(
        "\n".join(
            [
                "timestamp_ns,source_path",
                "1710000000000000000,source/left/frame-a.png",
                "1710000000033333333,source/left/frame-b.png",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (raw_root / "right_frames.csv").write_text(
        "\n".join(
            [
                "timestamp_ns,source_path",
                "1710000000000000000,source/right/frame-a.png",
                "1710000000033333333,source/right/frame-b.png",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (raw_root / "imu_samples.csv").write_text(
        "\n".join(
            [
                "timestamp_ns,angular_velocity_x,angular_velocity_y,angular_velocity_z,linear_acceleration_x,linear_acceleration_y,linear_acceleration_z",
                "1709999999990000000,0.01,0.02,0.03,0.11,0.12,0.13",
                "1710000000011111111,0.02,0.03,0.04,0.21,0.22,0.23",
                "1710000000022222222,0.03,0.04,0.05,0.31,0.32,0.33",
                "1710000000044444444,0.04,0.05,0.06,0.41,0.42,0.43",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class StereoImuNormalizationManifestTests(unittest.TestCase):
    def test_loads_checked_in_fixture_manifest(self) -> None:
        manifest = load_stereo_imu_normalization_manifest(
            REPO_ROOT / "manifests/stereo_imu_fixture_normalization.json"
        )

        self.assertEqual(manifest.sequence_name, "fixture-stereo-imu-sequence")
        self.assertEqual(
            manifest.launch_script, "scripts/prepare_stereo_imu_sequence.py"
        )
        self.assertEqual(
            manifest.raw_root, "datasets/fixtures/stereo_imu_fixture/raw"
        )


class StereoImuNormalizationTests(unittest.TestCase):
    def test_normalizes_sequence_into_canonical_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            write_raw_sequence(tmp_path)

            summary = normalize_stereo_imu_sequence(
                tmp_path / "raw",
                tmp_path / "normalized",
            )

            self.assertEqual(summary.sequence_id, "fixture-stereo-imu-sequence")
            self.assertEqual(summary.stereo_pair_count, 2)
            self.assertEqual(summary.imu_sample_count, 4)
            self.assertEqual(summary.first_timestamp_ns, 1710000000000000000)
            self.assertEqual(summary.last_timestamp_ns, 1710000000033333333)
            self.assertEqual(
                (tmp_path / "normalized" / "stereo" / "left" / "1710000000000000000.png").read_text(
                    encoding="utf-8"
                ),
                "left-a",
            )
            self.assertEqual(
                (tmp_path / "normalized" / "stereo" / "right" / "1710000000033333333.png").read_text(
                    encoding="utf-8"
                ),
                "right-b",
            )
            self.assertEqual(
                (tmp_path / "normalized" / "stereo" / "timestamps.csv").read_text(
                    encoding="utf-8"
                ),
                "\n".join(
                    [
                        "timestamp_ns,left_path,right_path",
                        "1710000000000000000,left/1710000000000000000.png,right/1710000000000000000.png",
                        "1710000000033333333,left/1710000000033333333.png,right/1710000000033333333.png",
                    ]
                )
                + "\n",
            )
            normalized_metadata = json.loads(
                (tmp_path / "normalized" / "sequence.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(normalized_metadata["counts"]["stereo_pairs"], 2)
            self.assertEqual(normalized_metadata["counts"]["imu_samples"], 4)
            self.assertEqual(
                normalized_metadata["normalized_layout"]["imu_path"],
                "imu/data.csv",
            )

    def test_requires_missing_sensor_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            write_raw_sequence(tmp_path)
            (tmp_path / "raw" / "imu_samples.csv").unlink()

            with self.assertRaisesRegex(
                ValueError, "Missing required raw inputs: imu_samples.csv"
            ):
                normalize_stereo_imu_sequence(
                    tmp_path / "raw",
                    tmp_path / "normalized",
                )

    def test_rejects_unsupported_frame_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            write_raw_sequence(tmp_path)
            (tmp_path / "raw" / "left_frames.csv").write_text(
                "\n".join(
                    [
                        "timestamp_ns,source_path",
                        "1710000000000000000,source/left/frame-a.jpg",
                        "1710000000033333333,source/left/frame-b.png",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (tmp_path / "raw" / "source" / "left" / "frame-a.jpg").write_text(
                "jpg-placeholder",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "Only PNG frame sources are supported"
            ):
                normalize_stereo_imu_sequence(
                    tmp_path / "raw",
                    tmp_path / "normalized",
                )

    def test_rejects_malformed_frame_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            write_raw_sequence(tmp_path)
            (tmp_path / "raw" / "left_frames.csv").write_text(
                "\n".join(
                    [
                        "timestamp_ns,source_path",
                        "invalid,source/left/frame-a.png",
                        "1710000000033333333,source/left/frame-b.png",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "Invalid frame timestamp for left camera"
            ):
                normalize_stereo_imu_sequence(
                    tmp_path / "raw",
                    tmp_path / "normalized",
                )

    def test_rejects_stereo_timestamp_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            write_raw_sequence(tmp_path)
            (tmp_path / "raw" / "right_frames.csv").write_text(
                "\n".join(
                    [
                        "timestamp_ns,source_path",
                        "1710000000000000000,source/right/frame-a.png",
                        "1710000000066666666,source/right/frame-b.png",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "Stereo timestamp gap at pair 2"
            ):
                normalize_stereo_imu_sequence(
                    tmp_path / "raw",
                    tmp_path / "normalized",
                )
