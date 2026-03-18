from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
import shutil


FRAME_INDEX_HEADER = ["timestamp_ns", "source_path"]
IMU_HEADER = [
    "timestamp_ns",
    "angular_velocity_x",
    "angular_velocity_y",
    "angular_velocity_z",
    "linear_acceleration_x",
    "linear_acceleration_y",
    "linear_acceleration_z",
]
REQUIRED_RAW_INPUTS = (
    "sequence.json",
    "left_frames.csv",
    "right_frames.csv",
    "imu_samples.csv",
)


@dataclass(frozen=True)
class StereoImuNormalizationManifest:
    launch_mode: str
    launch_script: str
    normalized_root: str
    notes: str
    raw_root: str
    report_path: str
    sequence_name: str


@dataclass(frozen=True)
class ResolvedStereoImuNormalizationPaths:
    normalized_root: Path
    raw_root: Path
    report: Path


@dataclass(frozen=True)
class FrameEntry:
    source_path: Path
    timestamp_ns: int


@dataclass(frozen=True)
class ImuSample:
    rendered_values: tuple[str, ...]
    timestamp_ns: int


@dataclass(frozen=True)
class NormalizedStereoImuSummary:
    first_timestamp_ns: int
    imu_first_timestamp_ns: int
    imu_last_timestamp_ns: int
    imu_path: Path
    imu_sample_count: int
    last_timestamp_ns: int
    left_image_dir: Path
    metadata_path: Path
    normalized_root: Path
    right_image_dir: Path
    sequence_id: str
    stereo_pair_count: int
    timestamps_path: Path


def _load_json(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected a JSON object at {path}.")
    return raw


def load_stereo_imu_normalization_manifest(
    path: Path,
) -> StereoImuNormalizationManifest:
    raw = _load_json(path)

    try:
        sequence = raw["sequence"]
        outputs = raw["outputs"]
        launch = raw["launch"]
        notes = raw["notes"]
    except KeyError as error:
        raise ValueError(f"Missing manifest section: {error.args[0]}") from error

    if not all(isinstance(section, dict) for section in (sequence, outputs, launch)):
        raise ValueError("Manifest sections sequence, outputs, and launch must be objects.")

    return StereoImuNormalizationManifest(
        launch_mode=str(launch["mode"]),
        launch_script=str(launch["script"]),
        normalized_root=str(outputs["normalized_root"]),
        notes=str(notes),
        raw_root=str(sequence["raw_root"]),
        report_path=str(outputs["report_path"]),
        sequence_name=str(sequence["name"]),
    )


def resolve_stereo_imu_normalization_paths(
    repo_root: Path,
    manifest: StereoImuNormalizationManifest,
) -> ResolvedStereoImuNormalizationPaths:
    return ResolvedStereoImuNormalizationPaths(
        normalized_root=repo_root / manifest.normalized_root,
        raw_root=repo_root / manifest.raw_root,
        report=repo_root / manifest.report_path,
    )


def _load_sequence_metadata(path: Path) -> dict[str, object]:
    raw = _load_json(path)
    sequence_id = str(raw.get("sequence_id", "")).strip()
    if not sequence_id:
        raise ValueError("Sequence metadata must define a non-empty sequence_id.")

    if raw.get("timestamp_unit") != "ns":
        raise ValueError("Sequence metadata must declare timestamp_unit as 'ns'.")

    rig = raw.get("rig")
    if not isinstance(rig, dict):
        raise ValueError("Sequence metadata must define a rig object.")

    for field in ("left_camera", "right_camera", "imu"):
        if not str(rig.get(field, "")).strip():
            raise ValueError(f"Sequence metadata rig is missing '{field}'.")

    return raw


def _load_frame_entries(index_path: Path, *, sensor_label: str) -> list[FrameEntry]:
    entries: list[FrameEntry] = []

    with index_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FRAME_INDEX_HEADER:
            raise ValueError(
                f"{sensor_label.capitalize()} index must use the exact header: "
                "timestamp_ns,source_path"
            )

        previous_timestamp = None
        for row_number, row in enumerate(reader, start=2):
            raw_timestamp = row["timestamp_ns"]
            try:
                timestamp_ns = int(raw_timestamp)
            except ValueError as error:
                raise ValueError(
                    f"Invalid frame timestamp for {sensor_label} at row "
                    f"{row_number}: {raw_timestamp!r}"
                ) from error

            if previous_timestamp is not None and timestamp_ns <= previous_timestamp:
                raise ValueError(
                    f"{sensor_label.capitalize()} timestamps must be strictly increasing."
                )

            raw_source_path = row["source_path"]
            source_path = Path(raw_source_path)
            if not source_path.is_absolute():
                source_path = index_path.parent / source_path

            if source_path.suffix.lower() != ".png":
                raise ValueError(
                    f"Only PNG frame sources are supported for {sensor_label}: "
                    f"{raw_source_path}"
                )
            if not source_path.exists():
                raise ValueError(
                    f"Missing frame source for {sensor_label}: {source_path}"
                )

            entries.append(
                FrameEntry(
                    source_path=source_path,
                    timestamp_ns=timestamp_ns,
                )
            )
            previous_timestamp = timestamp_ns

    if not entries:
        raise ValueError(f"{sensor_label.capitalize()} index did not contain any frames.")

    return entries


def _load_imu_samples(path: Path) -> list[ImuSample]:
    samples: list[ImuSample] = []

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != IMU_HEADER:
            raise ValueError(
                "IMU samples must use the exact header: "
                + ",".join(IMU_HEADER)
            )

        previous_timestamp = None
        for row_number, row in enumerate(reader, start=2):
            raw_timestamp = row["timestamp_ns"]
            try:
                timestamp_ns = int(raw_timestamp)
            except ValueError as error:
                raise ValueError(
                    f"Invalid IMU timestamp at row {row_number}: {raw_timestamp!r}"
                ) from error

            if previous_timestamp is not None and timestamp_ns <= previous_timestamp:
                raise ValueError("IMU timestamps must be strictly increasing.")

            rendered_values = [str(timestamp_ns)]
            for field_name in IMU_HEADER[1:]:
                raw_value = row[field_name]
                try:
                    float(raw_value)
                except ValueError as error:
                    raise ValueError(
                        f"Invalid IMU value for {field_name} at row {row_number}: "
                        f"{raw_value!r}"
                    ) from error
                rendered_values.append(raw_value)

            samples.append(
                ImuSample(
                    rendered_values=tuple(rendered_values),
                    timestamp_ns=timestamp_ns,
                )
            )
            previous_timestamp = timestamp_ns

    if not samples:
        raise ValueError("IMU samples did not contain any rows.")

    return samples


def _validate_stereo_alignment(
    left_entries: list[FrameEntry],
    right_entries: list[FrameEntry],
) -> None:
    if len(left_entries) != len(right_entries):
        raise ValueError(
            "Stereo pair count mismatch: "
            f"left camera has {len(left_entries)} frames but right camera has "
            f"{len(right_entries)} frames."
        )

    for pair_number, (left_entry, right_entry) in enumerate(
        zip(left_entries, right_entries),
        start=1,
    ):
        if left_entry.timestamp_ns != right_entry.timestamp_ns:
            raise ValueError(
                f"Stereo timestamp gap at pair {pair_number}: "
                f"left={left_entry.timestamp_ns}, right={right_entry.timestamp_ns}."
            )


def _validate_imu_coverage(
    imu_samples: list[ImuSample],
    *,
    first_frame_timestamp_ns: int,
    last_frame_timestamp_ns: int,
) -> None:
    imu_first = imu_samples[0].timestamp_ns
    imu_last = imu_samples[-1].timestamp_ns
    if imu_first > first_frame_timestamp_ns or imu_last < last_frame_timestamp_ns:
        raise ValueError(
            "IMU samples must cover the full stereo interval: "
            f"frames={first_frame_timestamp_ns}..{last_frame_timestamp_ns}, "
            f"imu={imu_first}..{imu_last}."
        )


def normalize_stereo_imu_sequence(
    raw_root: Path,
    normalized_root: Path,
) -> NormalizedStereoImuSummary:
    missing = [
        filename for filename in REQUIRED_RAW_INPUTS if not (raw_root / filename).exists()
    ]
    if missing:
        raise ValueError(
            "Missing required raw inputs: " + ", ".join(sorted(missing))
        )

    metadata = _load_sequence_metadata(raw_root / "sequence.json")
    left_entries = _load_frame_entries(
        raw_root / "left_frames.csv",
        sensor_label="left camera",
    )
    right_entries = _load_frame_entries(
        raw_root / "right_frames.csv",
        sensor_label="right camera",
    )
    _validate_stereo_alignment(left_entries, right_entries)

    imu_samples = _load_imu_samples(raw_root / "imu_samples.csv")
    _validate_imu_coverage(
        imu_samples,
        first_frame_timestamp_ns=left_entries[0].timestamp_ns,
        last_frame_timestamp_ns=left_entries[-1].timestamp_ns,
    )

    if normalized_root.exists():
        shutil.rmtree(normalized_root)

    left_output_dir = normalized_root / "stereo" / "left"
    right_output_dir = normalized_root / "stereo" / "right"
    imu_output_dir = normalized_root / "imu"
    timestamps_path = normalized_root / "stereo" / "timestamps.csv"
    metadata_path = normalized_root / "sequence.json"

    left_output_dir.mkdir(parents=True, exist_ok=True)
    right_output_dir.mkdir(parents=True, exist_ok=True)
    imu_output_dir.mkdir(parents=True, exist_ok=True)

    timestamp_rows = ["timestamp_ns,left_path,right_path"]
    for left_entry, right_entry in zip(left_entries, right_entries):
        timestamp_text = str(left_entry.timestamp_ns)
        left_name = f"{timestamp_text}.png"
        right_name = f"{timestamp_text}.png"

        shutil.copyfile(left_entry.source_path, left_output_dir / left_name)
        shutil.copyfile(right_entry.source_path, right_output_dir / right_name)
        timestamp_rows.append(
            f"{timestamp_text},left/{left_name},right/{right_name}"
        )

    timestamps_path.write_text(
        "\n".join(timestamp_rows) + "\n",
        encoding="utf-8",
    )

    imu_path = imu_output_dir / "data.csv"
    imu_rows = [",".join(IMU_HEADER)]
    imu_rows.extend(",".join(sample.rendered_values) for sample in imu_samples)
    imu_path.write_text("\n".join(imu_rows) + "\n", encoding="utf-8")

    normalized_metadata = dict(metadata)
    normalized_metadata["raw_layout"] = {
        "left_index_path": "left_frames.csv",
        "right_index_path": "right_frames.csv",
        "imu_samples_path": "imu_samples.csv",
    }
    normalized_metadata["normalized_layout"] = {
        "left_image_dir": "stereo/left",
        "right_image_dir": "stereo/right",
        "stereo_timestamps_path": "stereo/timestamps.csv",
        "imu_path": "imu/data.csv",
    }
    normalized_metadata["counts"] = {
        "stereo_pairs": len(left_entries),
        "imu_samples": len(imu_samples),
    }
    normalized_metadata["timestamp_range_ns"] = {
        "first": left_entries[0].timestamp_ns,
        "last": left_entries[-1].timestamp_ns,
    }
    normalized_metadata["imu_coverage_ns"] = {
        "first": imu_samples[0].timestamp_ns,
        "last": imu_samples[-1].timestamp_ns,
    }
    metadata_path.write_text(
        json.dumps(normalized_metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    return NormalizedStereoImuSummary(
        first_timestamp_ns=left_entries[0].timestamp_ns,
        imu_first_timestamp_ns=imu_samples[0].timestamp_ns,
        imu_last_timestamp_ns=imu_samples[-1].timestamp_ns,
        imu_path=imu_path,
        imu_sample_count=len(imu_samples),
        last_timestamp_ns=left_entries[-1].timestamp_ns,
        left_image_dir=left_output_dir,
        metadata_path=metadata_path,
        normalized_root=normalized_root,
        right_image_dir=right_output_dir,
        sequence_id=str(metadata["sequence_id"]),
        stereo_pair_count=len(left_entries),
        timestamps_path=timestamps_path,
    )


def render_stereo_imu_normalization_report(
    *,
    notes: str,
    raw_root: str,
    report_path: str,
    summary: NormalizedStereoImuSummary,
    normalized_root: str,
) -> str:
    return f"""# Stereo + IMU normalization report: {summary.sequence_id}

## Result

- Stereo pairs: `{summary.stereo_pair_count}`
- IMU samples: `{summary.imu_sample_count}`
- First stereo timestamp: `{summary.first_timestamp_ns}`
- Last stereo timestamp: `{summary.last_timestamp_ns}`
- IMU coverage: `{summary.imu_first_timestamp_ns}` to `{summary.imu_last_timestamp_ns}`

## Raw input

- Raw root: `{raw_root}`
- Required metadata: `sequence.json`
- Required stereo indexes: `left_frames.csv`, `right_frames.csv`
- Required IMU samples: `imu_samples.csv`

## Normalized output

- Normalized root: `{normalized_root}`
- Sequence metadata: `{normalized_root}/sequence.json`
- Left images: `{normalized_root}/stereo/left`
- Right images: `{normalized_root}/stereo/right`
- Stereo timestamps: `{normalized_root}/stereo/timestamps.csv`
- IMU samples: `{normalized_root}/imu/data.csv`
- Report path: `{report_path}`

## Notes

{notes}
"""
