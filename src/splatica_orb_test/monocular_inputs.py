from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


DEFAULT_MONOCULAR_INPUT_DATASET_ROOT = (
    "datasets/user/insta360_x3_one_lens_baseline"
)
RAW_CALIBRATION_FILENAMES = {
    "00": "insta360_x3_kb4_00_calib.txt",
    "10": "insta360_x3_kb4_10_calib.txt",
}
RAW_EXTRINSICS_FILENAME = "insta360_x3_extr_rigs_calib.json"


@dataclass(frozen=True)
class RawLensCalibration:
    camera_model: str
    cx: float
    cy: float
    fx: float
    fy: float
    image_height: int
    image_width: int
    k1: float
    k2: float
    k3: float
    k4: float


@dataclass(frozen=True)
class VideoSummary:
    avg_fps: float
    avg_frame_rate: str
    codec_name: str
    duration_seconds: float
    frame_count: int | None
    height: int
    nominal_fps: float
    r_frame_rate: str
    size_bytes: int
    width: int


@dataclass(frozen=True)
class LensInputLayout:
    dataset_root: Path
    frame_index_path: Path
    import_manifest_path: Path
    lens_root: Path
    monocular_calibration_path: Path
    raw_calibration_path: Path
    raw_video_path: Path
    source_png_dir: Path
    timestamps_path: Path


def _parse_rational(value: str) -> float:
    numerator_text, denominator_text = value.split("/", maxsplit=1)
    numerator = Decimal(numerator_text)
    denominator = Decimal(denominator_text)
    if denominator == 0:
        raise ValueError("ffprobe reported a zero denominator frame rate.")
    return float(numerator / denominator)


def _timestamp_to_ns(timestamp_text: str) -> int:
    timestamp = Decimal(timestamp_text)
    return int(
        (timestamp * Decimal("1000000000")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_raw_lens_calibration(path: Path) -> RawLensCalibration:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 6:
        raise ValueError("Raw lens calibration must contain exactly 6 non-empty lines.")

    image_width_text, image_height_text = lines[1].split()
    fx_text, fy_text = lines[2].split()
    cx_text, cy_text = lines[3].split()
    k1_text, k2_text = lines[4].split()
    k3_text, k4_text = lines[5].split()

    return RawLensCalibration(
        camera_model=lines[0],
        image_width=int(image_width_text),
        image_height=int(image_height_text),
        fx=float(fx_text),
        fy=float(fy_text),
        cx=float(cx_text),
        cy=float(cy_text),
        k1=float(k1_text),
        k2=float(k2_text),
        k3=float(k3_text),
        k4=float(k4_text),
    )


def parse_ffprobe_video_summary(raw: dict[str, object]) -> VideoSummary:
    streams = raw.get("streams")
    if not isinstance(streams, list) or not streams:
        raise ValueError("ffprobe summary did not include a video stream.")
    stream = streams[0]
    if not isinstance(stream, dict):
        raise ValueError("ffprobe summary stream must be an object.")
    format_raw = raw.get("format")
    if not isinstance(format_raw, dict):
        raise ValueError("ffprobe summary did not include a format object.")

    raw_frame_count = stream.get("nb_frames")
    frame_count = None
    if raw_frame_count not in (None, "N/A"):
        frame_count = int(str(raw_frame_count))

    return VideoSummary(
        codec_name=str(stream["codec_name"]),
        width=int(stream["width"]),
        height=int(stream["height"]),
        avg_frame_rate=str(stream["avg_frame_rate"]),
        avg_fps=_parse_rational(str(stream["avg_frame_rate"])),
        r_frame_rate=str(stream["r_frame_rate"]),
        nominal_fps=_parse_rational(str(stream["r_frame_rate"])),
        duration_seconds=float(format_raw["duration"]),
        size_bytes=int(format_raw["size"]),
        frame_count=frame_count,
    )


def parse_ffprobe_frame_timestamps_ns(raw: dict[str, object]) -> tuple[int, ...]:
    frames = raw.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("ffprobe frame probe did not include any frames.")

    timestamps_ns: list[int] = []
    previous_timestamp = None
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError("ffprobe frame entries must be objects.")

        timestamp_text = next(
            (
                str(frame[key])
                for key in (
                    "best_effort_timestamp_time",
                    "pts_time",
                    "pkt_dts_time",
                )
                if frame.get(key) not in (None, "N/A")
            ),
            None,
        )
        if timestamp_text is None:
            raise ValueError("ffprobe frame probe did not expose usable timestamps.")

        timestamp_ns = _timestamp_to_ns(timestamp_text)
        if previous_timestamp is not None and timestamp_ns <= previous_timestamp:
            raise ValueError("Video frame timestamps must be strictly increasing.")
        timestamps_ns.append(timestamp_ns)
        previous_timestamp = timestamp_ns

    return tuple(timestamps_ns)


def resolve_lens_input_layout(dataset_root: Path, *, lens_id: str) -> LensInputLayout:
    lens_root = dataset_root / "lenses" / lens_id
    return LensInputLayout(
        dataset_root=dataset_root,
        lens_root=lens_root,
        raw_video_path=dataset_root / "raw" / "video" / f"{lens_id}.mp4",
        raw_calibration_path=dataset_root / "raw" / "calibration" / RAW_CALIBRATION_FILENAMES[lens_id],
        source_png_dir=lens_root / "source_png",
        frame_index_path=lens_root / "frame_index.csv",
        timestamps_path=lens_root / "timestamps.txt",
        monocular_calibration_path=lens_root / "monocular_calibration.json",
        import_manifest_path=lens_root / "import_manifest.json",
    )


def write_frame_index_bundle(
    source_png_dir: Path,
    timestamps_ns: tuple[int, ...] | list[int],
    frame_index_path: Path,
    timestamps_path: Path,
) -> None:
    png_paths = sorted(source_png_dir.glob("*.png"))
    if not png_paths:
        raise ValueError("Source PNG directory does not contain any PNG frames.")
    if len(png_paths) != len(timestamps_ns):
        raise ValueError("Extracted PNG count must match the probed timestamp count.")

    frame_index_path.parent.mkdir(parents=True, exist_ok=True)
    timestamps_path.parent.mkdir(parents=True, exist_ok=True)

    with frame_index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp_ns", "source_path"])
        for timestamp_ns, png_path in zip(timestamps_ns, png_paths, strict=True):
            writer.writerow(
                [
                    timestamp_ns,
                    png_path.relative_to(frame_index_path.parent).as_posix(),
                ]
            )

    timestamps_path.write_text(
        "\n".join(str(timestamp_ns) for timestamp_ns in timestamps_ns) + "\n",
        encoding="utf-8",
    )


def build_monocular_calibration_json(
    raw_calibration: RawLensCalibration,
    *,
    lens_id: str,
    fps: int | float,
    color_order: str,
    source_video_path: Path,
    source_calibration_path: Path,
) -> dict[str, object]:
    return {
        "camera": {
            "label": f"insta360_x3_lens{lens_id}",
            "model": raw_calibration.camera_model,
            "image_width": raw_calibration.image_width,
            "image_height": raw_calibration.image_height,
            "fps": fps,
            "color_order": color_order.upper(),
            "intrinsics": {
                "fx": raw_calibration.fx,
                "fy": raw_calibration.fy,
                "cx": raw_calibration.cx,
                "cy": raw_calibration.cy,
            },
            "distortion": {
                "k1": raw_calibration.k1,
                "k2": raw_calibration.k2,
                "k3": raw_calibration.k3,
                "k4": raw_calibration.k4,
            },
        },
        "source": {
            "calibration_path": str(source_calibration_path),
            "video_path": str(source_video_path),
        },
        "notes": (
            "Derived from the raw Insta360 X3 lens calibration text export plus "
            "the probed mp4 stream metadata during HEL-52 input import."
        ),
    }


def compute_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def copy_input_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def probe_video_summary(ffprobe_path: Path, video_path: Path) -> VideoSummary:
    command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames",
        "-show_entries",
        "format=duration,size",
        "-of",
        "json",
        str(video_path),
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_ffprobe_video_summary(json.loads(completed.stdout))


def probe_frame_timestamps_ns(ffprobe_path: Path, video_path: Path) -> tuple[int, ...]:
    command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "frame=best_effort_timestamp_time,pts_time,pkt_dts_time",
        "-show_frames",
        "-of",
        "json",
        str(video_path),
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_ffprobe_frame_timestamps_ns(json.loads(completed.stdout))


def extract_png_frames(ffmpeg_path: Path, video_path: Path, output_dir: Path) -> int:
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(ffmpeg_path),
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-map",
        "0:v:0",
        "-fps_mode",
        "passthrough",
        "-start_number",
        "0",
        str(output_dir / "frame-%06d.png"),
    ]
    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return len(list(output_dir.glob("*.png")))


def write_import_manifest(
    path: Path,
    *,
    calibration_json_path: Path,
    frame_count: int,
    frame_index_path: Path,
    lens_id: str,
    raw_calibration_path: Path,
    raw_video_path: Path,
    source_png_dir: Path,
    timestamps_ns: tuple[int, ...],
    timestamps_path: Path,
    video_summary: VideoSummary,
) -> None:
    _write_json(
        path,
        {
            "lens_id": lens_id,
            "raw_video": {
                "path": str(raw_video_path),
                "sha256": compute_file_sha256(raw_video_path),
                "size_bytes": raw_video_path.stat().st_size,
            },
            "raw_calibration": {
                "path": str(raw_calibration_path),
                "sha256": compute_file_sha256(raw_calibration_path),
                "size_bytes": raw_calibration_path.stat().st_size,
            },
            "video_summary": {
                "codec_name": video_summary.codec_name,
                "width": video_summary.width,
                "height": video_summary.height,
                "avg_frame_rate": video_summary.avg_frame_rate,
                "avg_fps": video_summary.avg_fps,
                "r_frame_rate": video_summary.r_frame_rate,
                "nominal_fps": video_summary.nominal_fps,
                "duration_seconds": video_summary.duration_seconds,
                "frame_count": video_summary.frame_count,
                "size_bytes": video_summary.size_bytes,
            },
            "derived": {
                "source_png_dir": str(source_png_dir),
                "frame_index_path": str(frame_index_path),
                "timestamps_path": str(timestamps_path),
                "monocular_calibration_path": str(calibration_json_path),
                "frame_count": frame_count,
                "first_timestamp_ns": timestamps_ns[0],
                "last_timestamp_ns": timestamps_ns[-1],
            },
        },
    )


def write_markdown_report(path: Path, *, dataset_root: Path, summaries: list[dict[str, object]]) -> None:
    lines = [
        "# Monocular Input Import Report",
        "",
        f"- Dataset root: `{dataset_root}`",
        "",
    ]
    for summary in summaries:
        lines.extend(
            [
                f"## Lens {summary['lens_id']}",
                "",
                f"- Raw video: `{summary['raw_video_path']}`",
                f"- Raw calibration: `{summary['raw_calibration_path']}`",
                f"- Source PNG directory: `{summary['source_png_dir']}`",
                f"- Frame index: `{summary['frame_index_path']}`",
                f"- Timestamps: `{summary['timestamps_path']}`",
                f"- Derived calibration JSON: `{summary['calibration_json_path']}`",
                f"- Codec: `{summary['codec_name']}`",
                f"- Resolution: `{summary['width']}x{summary['height']}`",
                f"- Avg fps: `{summary['avg_fps']:.6f}`",
                f"- Duration seconds: `{summary['duration_seconds']:.6f}`",
                f"- Extracted frame count: `{summary['frame_count']}`",
                "",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
