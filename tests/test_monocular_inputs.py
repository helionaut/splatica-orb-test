from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.monocular_inputs import (
    build_monocular_calibration_json,
    load_raw_lens_calibration,
    parse_ffprobe_frame_timestamps_ns,
    parse_ffprobe_video_summary,
    resolve_lens_input_layout,
    write_frame_index_bundle,
)


class RawLensCalibrationTests(unittest.TestCase):
    def test_loads_kannala_brandt_text_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            calibration_path = Path(tmpdir) / "insta360_x3_kb4_10_calib.txt"
            calibration_path.write_text(
                "\n".join(
                    [
                        "kannalabrandt4",
                        "2880 2880",
                        "781.5982329802617 781.5740400214813",
                        "1434.2724594568516 1450.8528374988705",
                        "0.08422896345536275 -0.02915539854098567",
                        "0.008995285524657697 -0.002161607489144358",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            calibration = load_raw_lens_calibration(calibration_path)

        self.assertEqual(calibration.camera_model, "kannalabrandt4")
        self.assertEqual(calibration.image_width, 2880)
        self.assertEqual(calibration.image_height, 2880)
        self.assertAlmostEqual(calibration.fx, 781.5982329802617)
        self.assertAlmostEqual(calibration.k4, -0.002161607489144358)


class FfprobeParsingTests(unittest.TestCase):
    def test_parses_video_summary(self) -> None:
        summary = parse_ffprobe_video_summary(
            {
                "streams": [
                    {
                        "avg_frame_rate": "30000/1001",
                        "codec_name": "h264",
                        "height": 2880,
                        "nb_frames": "3",
                        "r_frame_rate": "30000/1001",
                        "width": 2880,
                    }
                ],
                "format": {
                    "duration": "0.100100",
                    "size": "123456",
                },
            }
        )

        self.assertEqual(summary.codec_name, "h264")
        self.assertEqual(summary.width, 2880)
        self.assertEqual(summary.height, 2880)
        self.assertEqual(summary.frame_count, 3)
        self.assertAlmostEqual(summary.avg_fps, 30000 / 1001)
        self.assertAlmostEqual(summary.duration_seconds, 0.1001)
        self.assertEqual(summary.size_bytes, 123456)

    def test_parses_frame_timestamps_to_nanoseconds(self) -> None:
        timestamps_ns = parse_ffprobe_frame_timestamps_ns(
            {
                "frames": [
                    {"best_effort_timestamp_time": "0.000000"},
                    {"best_effort_timestamp_time": "0.033366700"},
                    {"best_effort_timestamp_time": "0.066733400"},
                ]
            }
        )

        self.assertEqual(
            timestamps_ns,
            (
                0,
                33366700,
                66733400,
            ),
        )


class LensInputLayoutTests(unittest.TestCase):
    def test_resolves_expected_deterministic_paths(self) -> None:
        dataset_root = Path("/tmp/repo/datasets/user/insta360_x3_one_lens_baseline")

        layout = resolve_lens_input_layout(dataset_root, lens_id="10")

        self.assertEqual(layout.lens_root, dataset_root / "lenses/10")
        self.assertEqual(layout.raw_video_path, dataset_root / "raw/video/10.mp4")
        self.assertEqual(
            layout.raw_calibration_path,
            dataset_root / "raw/calibration/insta360_x3_kb4_10_calib.txt",
        )
        self.assertEqual(
            layout.frame_index_path,
            dataset_root / "lenses/10/frame_index.csv",
        )
        self.assertEqual(
            layout.timestamps_path,
            dataset_root / "lenses/10/timestamps.txt",
        )


class DerivedInputWritingTests(unittest.TestCase):
    def test_writes_frame_index_timestamps_and_calibration_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_root = Path(tmpdir) / "datasets/user/insta360_x3_one_lens_baseline"
            layout = resolve_lens_input_layout(dataset_root, lens_id="10")
            layout.source_png_dir.mkdir(parents=True, exist_ok=True)
            (layout.source_png_dir / "frame-000000.png").write_text(
                "frame-0",
                encoding="utf-8",
            )
            (layout.source_png_dir / "frame-000001.png").write_text(
                "frame-1",
                encoding="utf-8",
            )

            write_frame_index_bundle(
                layout.source_png_dir,
                (1710000000000000000, 1710000000033333333),
                layout.frame_index_path,
                layout.timestamps_path,
            )

            calibration_json = build_monocular_calibration_json(
                load_raw_lens_calibration(
                    _write_raw_lens_calibration(layout.raw_calibration_path)
                ),
                lens_id="10",
                fps=30.0,
                color_order="BGR",
                source_video_path=layout.raw_video_path,
                source_calibration_path=layout.raw_calibration_path,
            )
            self.assertEqual(
                layout.frame_index_path.read_text(encoding="utf-8"),
                "\n".join(
                    [
                        "timestamp_ns,source_path",
                        "1710000000000000000,source_png/frame-000000.png",
                        "1710000000033333333,source_png/frame-000001.png",
                    ]
                )
                + "\n",
            )
            self.assertEqual(
                layout.timestamps_path.read_text(encoding="utf-8"),
                "1710000000000000000\n1710000000033333333\n",
            )
            self.assertEqual(calibration_json["camera"]["label"], "insta360_x3_lens10")
            self.assertEqual(calibration_json["camera"]["fps"], 30.0)
            self.assertEqual(calibration_json["camera"]["color_order"], "BGR")
            self.assertEqual(
                calibration_json["source"]["video_path"],
                str(layout.raw_video_path),
            )


def _write_raw_lens_calibration(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "kannalabrandt4",
                "2880 2880",
                "781.5982329802617 781.5740400214813",
                "1434.2724594568516 1450.8528374988705",
                "0.08422896345536275 -0.02915539854098567",
                "0.008995285524657697 -0.002161607489144358",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path
