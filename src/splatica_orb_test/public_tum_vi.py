from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import statistics

from .rgbd_tum_baseline import compute_tum_trajectory_metrics, load_tum_trajectory_points


@dataclass(frozen=True)
class PublicTumViManifest:
    archive_path: str
    archive_url: str
    baseline_commit: str
    baseline_name: str
    calibration_path: str
    camera_label: str
    camera_name: str
    checkout_path: str
    dataset_name: str
    dataset_root: str
    executable_path: str
    frame_index_path: str
    image_dir: str
    launch_script: str
    log_path: str
    notes: str
    repo_url: str
    report_path: str
    sequence_name: str
    settings_path: str
    summary_json_path: str
    timestamps_path: str
    trajectory_plot_path: str
    trajectory_stem: str
    visual_report_path: str
    vocabulary_path: str


@dataclass(frozen=True)
class ResolvedPublicTumViPaths:
    archive: Path
    baseline_root: Path
    calibration: Path
    camera_data: Path
    camera_model: Path
    data_csv: Path
    dataset_root: Path
    executable: Path
    frame_index: Path
    image_dir: Path
    log: Path
    report: Path
    settings: Path
    summary_json: Path
    timestamps: Path
    trajectory_plot: Path
    trajectory_stem: Path
    visual_report: Path
    vocabulary: Path


@dataclass(frozen=True)
class MaterializedPublicTumViSequence:
    first_timestamp_ns: int
    frame_count: int
    last_timestamp_ns: int


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_public_tum_vi_manifest(path: Path) -> PublicTumViManifest:
    raw = _load_json(path)

    try:
        baseline = raw["baseline"]
        launch = raw["launch"]
        notes = raw["notes"]
        outputs = raw["outputs"]
        public_dataset = raw["public_dataset"]
        sequence = raw["sequence"]
    except KeyError as error:
        raise ValueError(f"Missing manifest section: {error.args[0]}") from error

    if not all(
        isinstance(section, dict)
        for section in (baseline, launch, outputs, public_dataset, sequence)
    ):
        raise ValueError(
            "Manifest sections baseline, sequence, outputs, launch, and public_dataset must be objects."
        )

    return PublicTumViManifest(
        archive_path=str(public_dataset["archive_path"]),
        archive_url=str(public_dataset["archive_url"]),
        baseline_commit=str(baseline["commit"]),
        baseline_name=str(baseline["name"]),
        calibration_path=str(sequence["calibration_path"]),
        camera_label=str(sequence["camera_label"]),
        camera_name=str(public_dataset["camera"]),
        checkout_path=str(baseline["checkout_path"]),
        dataset_name=str(public_dataset["dataset_name"]),
        dataset_root=str(public_dataset["dataset_root"]),
        executable_path=str(baseline["executable_path"]),
        frame_index_path=str(sequence["frame_index_path"]),
        image_dir=str(outputs["image_dir"]),
        launch_script=str(launch["script"]),
        log_path=str(outputs["log_path"]),
        notes=str(notes),
        repo_url=str(baseline["repo_url"]),
        report_path=str(outputs["report_path"]),
        sequence_name=str(sequence["name"]),
        settings_path=str(outputs["settings_path"]),
        summary_json_path=str(outputs["summary_json_path"]),
        timestamps_path=str(outputs["timestamps_path"]),
        trajectory_plot_path=str(outputs["trajectory_plot_path"]),
        trajectory_stem=str(outputs["trajectory_stem"]),
        visual_report_path=str(outputs["visual_report_path"]),
        vocabulary_path=str(baseline["vocabulary_path"]),
    )


def resolve_public_tum_vi_paths(
    repo_root: Path,
    manifest: PublicTumViManifest,
) -> ResolvedPublicTumViPaths:
    baseline_root = repo_root / manifest.checkout_path
    dataset_root = repo_root / manifest.dataset_root
    camera_root = dataset_root / "mav0" / manifest.camera_name
    return ResolvedPublicTumViPaths(
        archive=repo_root / manifest.archive_path,
        baseline_root=baseline_root,
        calibration=repo_root / manifest.calibration_path,
        camera_data=camera_root / "data",
        camera_model=dataset_root / "dso" / manifest.camera_name / "camera.txt",
        data_csv=camera_root / "data.csv",
        dataset_root=dataset_root,
        executable=baseline_root / manifest.executable_path,
        frame_index=repo_root / manifest.frame_index_path,
        image_dir=repo_root / manifest.image_dir,
        log=repo_root / manifest.log_path,
        report=repo_root / manifest.report_path,
        settings=repo_root / manifest.settings_path,
        summary_json=repo_root / manifest.summary_json_path,
        timestamps=repo_root / manifest.timestamps_path,
        trajectory_plot=repo_root / manifest.trajectory_plot_path,
        trajectory_stem=repo_root / manifest.trajectory_stem,
        visual_report=repo_root / manifest.visual_report_path,
        vocabulary=baseline_root / manifest.vocabulary_path,
    )


def public_tum_vi_dataset_is_ready(resolved: ResolvedPublicTumViPaths) -> bool:
    return (
        resolved.dataset_root.is_dir()
        and resolved.camera_data.is_dir()
        and resolved.camera_model.is_file()
        and resolved.data_csv.is_file()
    )


def load_tum_vi_camera_txt(path: Path) -> dict[str, object]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError(f"TUM-VI camera model file is incomplete: {path}")

    calibration_parts = lines[0].split()
    if len(calibration_parts) != 9:
        raise ValueError(f"Unexpected TUM-VI camera model line in {path}: {lines[0]}")
    if calibration_parts[0].lower() != "equidistant":
        raise ValueError(
            f"Unsupported TUM-VI camera model in {path}: {calibration_parts[0]}"
        )

    resolution_parts = lines[1].split()
    if len(resolution_parts) != 2:
        raise ValueError(f"Unexpected TUM-VI resolution line in {path}: {lines[1]}")

    width = int(resolution_parts[0])
    height = int(resolution_parts[1])
    intrinsics = [float(value) for value in calibration_parts[1:5]]
    distortion = [float(value) for value in calibration_parts[5:9]]

    return {
        "camera_model": "pinhole",
        "distortion_model": "equidistant",
        "intrinsics": [
            intrinsics[0] * width,
            intrinsics[1] * height,
            intrinsics[2] * width,
            intrinsics[3] * height,
        ],
        "distortion_coefficients": distortion,
        "resolution": [width, height],
    }


def build_tum_vi_monocular_calibration(
    *,
    camera_label: str,
    fps: float,
    notes: str,
    camera_model: dict[str, object],
) -> dict[str, object]:
    resolution = camera_model.get("resolution")
    intrinsics = camera_model.get("intrinsics")
    distortion = camera_model.get("distortion_coefficients")
    distortion_model = str(camera_model.get("distortion_model", "")).strip().lower()

    if not isinstance(resolution, list) or len(resolution) != 2:
        raise ValueError("TUM-VI sensor.yaml must define resolution as [width, height].")
    if not isinstance(intrinsics, list) or len(intrinsics) != 4:
        raise ValueError("TUM-VI sensor.yaml must define intrinsics as [fx, fy, cx, cy].")
    if not isinstance(distortion, list) or len(distortion) != 4:
        raise ValueError(
            "TUM-VI sensor.yaml must define distortion_coefficients as [k1, k2, k3, k4]."
        )
    if distortion_model not in {"equidistant", "kannalabrandt4", "kannalabrandt8"}:
        raise ValueError(
            "TUM-VI camera metadata distortion_model must be equidistant/Kannala-Brandt."
        )

    return {
        "camera": {
            "label": camera_label,
            "model": "KannalaBrandt8",
            "image_width": int(resolution[0]),
            "image_height": int(resolution[1]),
            "fps": float(fps),
            "color_order": "RGB",
            "intrinsics": {
                "fx": float(intrinsics[0]),
                "fy": float(intrinsics[1]),
                "cx": float(intrinsics[2]),
                "cy": float(intrinsics[3]),
            },
            "distortion": {
                "k1": float(distortion[0]),
                "k2": float(distortion[1]),
                "k3": float(distortion[2]),
                "k4": float(distortion[3]),
            },
        },
        "notes": notes,
    }


def load_tum_vi_camera_rows(path: Path) -> list[tuple[int, str]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"TUM-VI camera CSV is empty: {path}")

    header = lines[0].lstrip("#").strip().lower()
    columns = [column.strip() for column in header.split(",")]
    if len(columns) != 2 or "timestamp" not in columns[0] or columns[1] != "filename":
        raise ValueError(f"Unexpected TUM-VI camera CSV header in {path}: {lines[0]}")

    rows: list[tuple[int, str]] = []
    for raw_line in lines[1:]:
        if raw_line.startswith("#"):
            continue
        parts = [part.strip() for part in raw_line.split(",", 1)]
        if len(parts) != 2:
            raise ValueError(f"Malformed TUM-VI camera CSV row in {path}: {raw_line}")
        rows.append((int(parts[0]), parts[1]))
    if not rows:
        raise ValueError(f"TUM-VI camera CSV did not contain any frame rows: {path}")
    return rows


def estimate_tum_vi_fps(rows: list[tuple[int, str]]) -> float:
    if len(rows) < 2:
        raise ValueError("Need at least two TUM-VI camera rows to estimate fps.")
    deltas = [current[0] - previous[0] for previous, current in zip(rows, rows[1:])]
    median_delta_ns = statistics.median(deltas)
    if median_delta_ns <= 0:
        raise ValueError("TUM-VI frame timestamps must be strictly increasing.")
    return 1_000_000_000.0 / float(median_delta_ns)


def materialize_public_tum_vi_sequence(
    *,
    manifest: PublicTumViManifest,
    resolved: ResolvedPublicTumViPaths,
) -> MaterializedPublicTumViSequence:
    if not public_tum_vi_dataset_is_ready(resolved):
        raise ValueError(
            "TUM-VI dataset is incomplete. Fetch and extract the public dataset first."
        )

    camera_rows = load_tum_vi_camera_rows(resolved.data_csv)
    camera_model = load_tum_vi_camera_txt(resolved.camera_model)
    calibration_payload = build_tum_vi_monocular_calibration(
        camera_label=manifest.camera_label,
        fps=estimate_tum_vi_fps(camera_rows),
        notes=manifest.notes,
        camera_model=camera_model,
    )

    resolved.calibration.parent.mkdir(parents=True, exist_ok=True)
    resolved.calibration.write_text(
        json.dumps(calibration_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    previous_timestamp: int | None = None
    resolved.frame_index.parent.mkdir(parents=True, exist_ok=True)
    with resolved.frame_index.open("w", encoding="utf-8", newline="") as handle:
        handle.write("timestamp_ns,source_path\n")
        for timestamp_ns, filename in camera_rows:
            if previous_timestamp is not None and timestamp_ns <= previous_timestamp:
                raise ValueError("TUM-VI frame timestamps must be strictly increasing.")
            source_path = (resolved.camera_data / filename).resolve()
            if source_path.suffix.lower() != ".png":
                raise ValueError(
                    f"TUM-VI camera rows must reference PNG frames: {source_path}"
                )
            if not source_path.exists():
                raise ValueError(f"TUM-VI frame path does not exist: {source_path}")
            handle.write(f"{timestamp_ns},{source_path}\n")
            previous_timestamp = timestamp_ns

    return MaterializedPublicTumViSequence(
        first_timestamp_ns=camera_rows[0][0],
        frame_count=len(camera_rows),
        last_timestamp_ns=camera_rows[-1][0],
    )


def summarize_tum_vi_trajectory(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "size_bytes": 0, "metrics": compute_tum_trajectory_metrics([])}

    size_bytes = path.stat().st_size
    if size_bytes == 0:
        return {"exists": True, "size_bytes": 0, "metrics": compute_tum_trajectory_metrics([])}

    points = load_tum_trajectory_points(path)
    return {
        "exists": True,
        "size_bytes": size_bytes,
        "metrics": compute_tum_trajectory_metrics(points),
    }
