#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.local_tooling import (  # noqa: E402
    resolve_ffmpeg_tool,
    resolve_ffprobe_tool,
)
from splatica_orb_test.monocular_inputs import (  # noqa: E402
    DEFAULT_MONOCULAR_INPUT_DATASET_ROOT,
    RAW_EXTRINSICS_FILENAME,
    build_monocular_calibration_json,
    copy_input_file,
    extract_png_frames,
    load_raw_lens_calibration,
    probe_frame_timestamps_ns,
    probe_video_summary,
    resolve_lens_input_layout,
    write_frame_index_bundle,
    write_import_manifest,
    write_markdown_report,
)


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-root",
        default=DEFAULT_MONOCULAR_INPUT_DATASET_ROOT,
    )
    parser.add_argument("--video-00", required=True)
    parser.add_argument("--video-10", required=True)
    parser.add_argument("--calibration-00", required=True)
    parser.add_argument("--calibration-10", required=True)
    parser.add_argument("--extrinsics", required=True)
    parser.add_argument(
        "--color-order",
        default="BGR",
        choices=("RGB", "BGR", "rgb", "bgr"),
    )
    parser.add_argument(
        "--lenses",
        nargs="+",
        default=["10", "00"],
        choices=("10", "00"),
    )
    args = parser.parse_args()

    ffmpeg = resolve_ffmpeg_tool(REPO_ROOT)
    ffprobe = resolve_ffprobe_tool(REPO_ROOT)
    if ffmpeg is None or ffprobe is None:
        missing = []
        if ffmpeg is None:
            missing.append("ffmpeg")
        if ffprobe is None:
            missing.append("ffprobe")
        parser.error(
            "Missing required media tools: "
            + ", ".join(missing)
            + ". Run `make bootstrap-local-ffmpeg` or install them on PATH."
        )

    dataset_root = resolve_repo_path(args.dataset_root)
    source_videos = {
        "00": resolve_repo_path(args.video_00),
        "10": resolve_repo_path(args.video_10),
    }
    source_calibrations = {
        "00": resolve_repo_path(args.calibration_00),
        "10": resolve_repo_path(args.calibration_10),
    }
    source_extrinsics = resolve_repo_path(args.extrinsics)
    copied_extrinsics = dataset_root / "raw/calibration" / RAW_EXTRINSICS_FILENAME
    copy_input_file(source_extrinsics, copied_extrinsics)

    summaries: list[dict[str, object]] = []
    for lens_id in args.lenses:
        layout = resolve_lens_input_layout(dataset_root, lens_id=lens_id)
        copy_input_file(source_videos[lens_id], layout.raw_video_path)
        copy_input_file(source_calibrations[lens_id], layout.raw_calibration_path)

        raw_calibration = load_raw_lens_calibration(layout.raw_calibration_path)
        video_summary = probe_video_summary(ffprobe.path, layout.raw_video_path)

        if (
            raw_calibration.image_width != video_summary.width
            or raw_calibration.image_height != video_summary.height
        ):
            raise ValueError(
                f"Lens {lens_id} calibration image size "
                f"{raw_calibration.image_width}x{raw_calibration.image_height} "
                f"does not match probed video size "
                f"{video_summary.width}x{video_summary.height}."
            )

        timestamps_ns = probe_frame_timestamps_ns(ffprobe.path, layout.raw_video_path)
        extracted_frame_count = extract_png_frames(
            ffmpeg.path,
            layout.raw_video_path,
            layout.source_png_dir,
        )
        write_frame_index_bundle(
            layout.source_png_dir,
            timestamps_ns,
            layout.frame_index_path,
            layout.timestamps_path,
        )

        calibration_json = build_monocular_calibration_json(
            raw_calibration,
            lens_id=lens_id,
            fps=video_summary.avg_fps,
            color_order=args.color_order,
            source_video_path=layout.raw_video_path,
            source_calibration_path=layout.raw_calibration_path,
        )
        layout.monocular_calibration_path.parent.mkdir(parents=True, exist_ok=True)
        layout.monocular_calibration_path.write_text(
            json.dumps(calibration_json, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        write_import_manifest(
            layout.import_manifest_path,
            calibration_json_path=layout.monocular_calibration_path,
            frame_count=extracted_frame_count,
            frame_index_path=layout.frame_index_path,
            lens_id=lens_id,
            raw_calibration_path=layout.raw_calibration_path,
            raw_video_path=layout.raw_video_path,
            source_png_dir=layout.source_png_dir,
            timestamps_ns=timestamps_ns,
            timestamps_path=layout.timestamps_path,
            video_summary=video_summary,
        )

        summaries.append(
            {
                "lens_id": lens_id,
                "raw_video_path": layout.raw_video_path,
                "raw_calibration_path": layout.raw_calibration_path,
                "source_png_dir": layout.source_png_dir,
                "frame_index_path": layout.frame_index_path,
                "timestamps_path": layout.timestamps_path,
                "calibration_json_path": layout.monocular_calibration_path,
                "codec_name": video_summary.codec_name,
                "width": video_summary.width,
                "height": video_summary.height,
                "avg_fps": video_summary.avg_fps,
                "duration_seconds": video_summary.duration_seconds,
                "frame_count": extracted_frame_count,
            }
        )

    report_path = dataset_root / "reports/ingest_report.md"
    write_markdown_report(
        report_path,
        dataset_root=dataset_root,
        summaries=summaries,
    )

    for summary in summaries:
        print(f"Lens {summary['lens_id']}:")
        print(f"  raw video: {summary['raw_video_path']}")
        print(f"  source_png_dir: {summary['source_png_dir']}")
        print(
            "  video: "
            f"{summary['codec_name']} "
            f"{summary['width']}x{summary['height']} "
            f"{summary['avg_fps']:.6f} fps"
        )
        print(f"  extracted frames: {summary['frame_count']}")
        print(f"  frame index: {summary['frame_index_path']}")
        print(f"  timestamps: {summary['timestamps_path']}")
        print(f"  derived calibration: {summary['calibration_json_path']}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
