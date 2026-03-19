from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
import shutil


ORB_SLAM3_UPSTREAM_MASTER = "4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4"
ORB_SLAM3_V1_0_RELEASE = "0df83dde1c85c7ab91a0d47de7a29685d046f637"
SUPPORTED_SOURCE_CAMERA_MODELS = {
    "KANNALABRANDT4",
    "KANNALABRANDT8",
}


@dataclass(frozen=True)
class OrbParameters:
    ini_fast: int
    min_fast: int
    n_features: int
    n_levels: int
    scale_factor: float


@dataclass(frozen=True)
class ViewerParameters:
    camera_line_width: float
    camera_size: float
    graph_line_width: float
    key_frame_line_width: float
    key_frame_size: float
    point_size: float
    viewpoint_f: float
    viewpoint_x: float
    viewpoint_y: float
    viewpoint_z: float


@dataclass(frozen=True)
class MonocularCalibration:
    camera_label: str
    camera_model: str
    color_order: str
    fps: int | float
    fx: float
    fy: float
    cx: float
    cy: float
    image_height: int
    image_width: int
    k1: float
    k2: float
    k3: float
    k4: float
    notes: str
    orb: OrbParameters
    viewer: ViewerParameters


@dataclass(frozen=True)
class MonocularBaselineManifest:
    baseline_commit: str
    baseline_name: str
    calibration_path: str
    camera_label: str
    checkout_path: str
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
    timestamps_path: str
    trajectory_stem: str
    vocabulary_path: str


@dataclass(frozen=True)
class ResolvedMonocularBaselinePaths:
    baseline_root: Path
    calibration: Path
    executable: Path
    frame_index: Path
    image_dir: Path
    log: Path
    report: Path
    settings: Path
    timestamps: Path
    trajectory_stem: Path
    vocabulary: Path


@dataclass(frozen=True)
class PreparedSequence:
    first_timestamp_ns: int
    frame_count: int
    last_timestamp_ns: int


@dataclass(frozen=True)
class MonocularTrajectoryOutputs:
    frame_trajectory: Path
    keyframe_trajectory: Path


DEFAULT_ORB = OrbParameters(
    n_features=1500,
    scale_factor=1.2,
    n_levels=8,
    ini_fast=20,
    min_fast=7,
)
DEFAULT_VIEWER = ViewerParameters(
    key_frame_size=0.05,
    key_frame_line_width=1.0,
    graph_line_width=0.9,
    point_size=2.0,
    camera_size=0.08,
    camera_line_width=3.0,
    viewpoint_x=0.0,
    viewpoint_y=-0.7,
    viewpoint_z=-3.5,
    viewpoint_f=500.0,
)


def _format_number(value: int | float, *, force_decimal: bool = False) -> str:
    if isinstance(value, int):
        return str(value)

    rendered = f"{value:.12f}".rstrip("0")
    if rendered.endswith("."):
        return f"{rendered}0" if force_decimal else rendered[:-1]
    return rendered


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_orb_parameters(raw: dict[str, object]) -> OrbParameters:
    return OrbParameters(
        n_features=int(raw.get("n_features", DEFAULT_ORB.n_features)),
        scale_factor=float(raw.get("scale_factor", DEFAULT_ORB.scale_factor)),
        n_levels=int(raw.get("n_levels", DEFAULT_ORB.n_levels)),
        ini_fast=int(raw.get("ini_fast", DEFAULT_ORB.ini_fast)),
        min_fast=int(raw.get("min_fast", DEFAULT_ORB.min_fast)),
    )


def _load_viewer_parameters(raw: dict[str, object]) -> ViewerParameters:
    return ViewerParameters(
        key_frame_size=float(raw.get("key_frame_size", DEFAULT_VIEWER.key_frame_size)),
        key_frame_line_width=float(
            raw.get("key_frame_line_width", DEFAULT_VIEWER.key_frame_line_width)
        ),
        graph_line_width=float(
            raw.get("graph_line_width", DEFAULT_VIEWER.graph_line_width)
        ),
        point_size=float(raw.get("point_size", DEFAULT_VIEWER.point_size)),
        camera_size=float(raw.get("camera_size", DEFAULT_VIEWER.camera_size)),
        camera_line_width=float(
            raw.get("camera_line_width", DEFAULT_VIEWER.camera_line_width)
        ),
        viewpoint_x=float(raw.get("viewpoint_x", DEFAULT_VIEWER.viewpoint_x)),
        viewpoint_y=float(raw.get("viewpoint_y", DEFAULT_VIEWER.viewpoint_y)),
        viewpoint_z=float(raw.get("viewpoint_z", DEFAULT_VIEWER.viewpoint_z)),
        viewpoint_f=float(raw.get("viewpoint_f", DEFAULT_VIEWER.viewpoint_f)),
    )


def load_monocular_calibration(path: Path) -> MonocularCalibration:
    raw = _load_json(path)

    try:
        camera = raw["camera"]
        if not isinstance(camera, dict):
            raise TypeError("camera")
        intrinsics = camera["intrinsics"]
        distortion = camera["distortion"]
        if not isinstance(intrinsics, dict):
            raise TypeError("camera.intrinsics")
        if not isinstance(distortion, dict):
            raise TypeError("camera.distortion")
    except KeyError as error:
        raise ValueError(f"Missing calibration section: {error.args[0]}") from error
    except TypeError as error:
        raise ValueError(f"Invalid calibration section: {error.args[0]}") from error

    source_camera_model = str(camera["model"]).strip()
    if source_camera_model.upper() not in SUPPORTED_SOURCE_CAMERA_MODELS:
        raise ValueError(
            "Monocular baseline only supports Kannala-Brandt 4/8 source models."
        )
    color_order = camera.get("color_order")
    if color_order is None:
        raise ValueError("Missing calibration field: camera.color_order")
    normalized_color_order = str(color_order).upper()
    if normalized_color_order not in {"RGB", "BGR"}:
        raise ValueError("camera.color_order must be either RGB or BGR.")

    orb_raw = raw.get("orb", {})
    viewer_raw = raw.get("viewer", {})

    if not isinstance(orb_raw, dict):
        raise ValueError("Calibration orb section must be an object if provided.")
    if not isinstance(viewer_raw, dict):
        raise ValueError("Calibration viewer section must be an object if provided.")

    return MonocularCalibration(
        camera_label=str(camera["label"]),
        camera_model="KannalaBrandt8",
        color_order=normalized_color_order,
        fps=camera["fps"],
        fx=float(intrinsics["fx"]),
        fy=float(intrinsics["fy"]),
        cx=float(intrinsics["cx"]),
        cy=float(intrinsics["cy"]),
        image_height=int(camera["image_height"]),
        image_width=int(camera["image_width"]),
        k1=float(distortion["k1"]),
        k2=float(distortion["k2"]),
        k3=float(distortion["k3"]),
        k4=float(distortion["k4"]),
        notes=str(raw.get("notes", "")),
        orb=_load_orb_parameters(orb_raw),
        viewer=_load_viewer_parameters(viewer_raw),
    )


def load_monocular_baseline_manifest(path: Path) -> MonocularBaselineManifest:
    raw = _load_json(path)

    try:
        baseline = raw["baseline"]
        sequence = raw["sequence"]
        outputs = raw["outputs"]
        launch = raw["launch"]
        notes = raw["notes"]
    except KeyError as error:
        raise ValueError(f"Missing manifest section: {error.args[0]}") from error

    if not all(isinstance(section, dict) for section in (baseline, sequence, outputs, launch)):
        raise ValueError("Manifest sections baseline, sequence, outputs, and launch must be objects.")

    return MonocularBaselineManifest(
        baseline_commit=str(baseline["commit"]),
        baseline_name=str(baseline["name"]),
        calibration_path=str(sequence["calibration_path"]),
        camera_label=str(sequence["camera_label"]),
        checkout_path=str(baseline["checkout_path"]),
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
        timestamps_path=str(outputs["timestamps_path"]),
        trajectory_stem=str(outputs["trajectory_stem"]),
        vocabulary_path=str(baseline["vocabulary_path"]),
    )


def resolve_monocular_baseline_paths(
    repo_root: Path,
    manifest: MonocularBaselineManifest,
) -> ResolvedMonocularBaselinePaths:
    baseline_root = repo_root / manifest.checkout_path
    return ResolvedMonocularBaselinePaths(
        baseline_root=baseline_root,
        calibration=repo_root / manifest.calibration_path,
        executable=baseline_root / manifest.executable_path,
        frame_index=repo_root / manifest.frame_index_path,
        image_dir=repo_root / manifest.image_dir,
        log=repo_root / manifest.log_path,
        report=repo_root / manifest.report_path,
        settings=repo_root / manifest.settings_path,
        timestamps=repo_root / manifest.timestamps_path,
        trajectory_stem=repo_root / manifest.trajectory_stem,
        vocabulary=baseline_root / manifest.vocabulary_path,
    )


def render_monocular_settings_yaml(calibration: MonocularCalibration) -> str:
    camera_rgb = 1 if calibration.color_order == "RGB" else 0
    camera_fps = int(round(calibration.fps))

    return f"""%YAML:1.0

#--------------------------------------------------------------------------------------------
# Camera Parameters. Adjust them!
#--------------------------------------------------------------------------------------------
File.version: "1.0"

Camera.type: "{calibration.camera_model}"

# Camera calibration and distortion parameters (OpenCV)
Camera1.fx: {_format_number(calibration.fx)}
Camera1.fy: {_format_number(calibration.fy)}
Camera1.cx: {_format_number(calibration.cx)}
Camera1.cy: {_format_number(calibration.cy)}

Camera1.k1: {_format_number(calibration.k1)}
Camera1.k2: {_format_number(calibration.k2)}
Camera1.k3: {_format_number(calibration.k3)}
Camera1.k4: {_format_number(calibration.k4)}

# Camera resolution
Camera.width: {calibration.image_width}
Camera.height: {calibration.image_height}

# Camera frames per second
Camera.fps: {camera_fps}

# Color order of the images (0: BGR, 1: RGB. It is ignored if images are grayscale)
Camera.RGB: {camera_rgb}

#--------------------------------------------------------------------------------------------
# ORB Parameters
#--------------------------------------------------------------------------------------------
ORBextractor.nFeatures: {calibration.orb.n_features}
ORBextractor.scaleFactor: {_format_number(calibration.orb.scale_factor, force_decimal=True)}
ORBextractor.nLevels: {calibration.orb.n_levels}
ORBextractor.iniThFAST: {calibration.orb.ini_fast}
ORBextractor.minThFAST: {calibration.orb.min_fast}

#--------------------------------------------------------------------------------------------
# Viewer Parameters
#--------------------------------------------------------------------------------------------
Viewer.KeyFrameSize: {_format_number(calibration.viewer.key_frame_size, force_decimal=True)}
Viewer.KeyFrameLineWidth: {_format_number(calibration.viewer.key_frame_line_width, force_decimal=True)}
Viewer.GraphLineWidth: {_format_number(calibration.viewer.graph_line_width, force_decimal=True)}
Viewer.PointSize: {_format_number(calibration.viewer.point_size, force_decimal=True)}
Viewer.CameraSize: {_format_number(calibration.viewer.camera_size, force_decimal=True)}
Viewer.CameraLineWidth: {_format_number(calibration.viewer.camera_line_width, force_decimal=True)}
Viewer.ViewpointX: {_format_number(calibration.viewer.viewpoint_x, force_decimal=True)}
Viewer.ViewpointY: {_format_number(calibration.viewer.viewpoint_y, force_decimal=True)}
Viewer.ViewpointZ: {_format_number(calibration.viewer.viewpoint_z, force_decimal=True)}
Viewer.ViewpointF: {_format_number(calibration.viewer.viewpoint_f, force_decimal=True)}
"""


def prepare_monocular_sequence(
    frame_index_path: Path,
    image_dir: Path,
    timestamps_path: Path,
) -> PreparedSequence:
    entries: list[tuple[int, Path]] = []

    with frame_index_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["timestamp_ns", "source_path"]:
            raise ValueError(
                "Frame index must use the exact header: timestamp_ns,source_path"
            )

        for row in reader:
            timestamp_ns = int(row["timestamp_ns"])
            source_path = Path(row["source_path"])
            if not source_path.is_absolute():
                source_path = frame_index_path.parent / source_path

            entries.append((timestamp_ns, source_path))

    if not entries:
        raise ValueError("Frame index did not contain any frames.")

    previous_timestamp = None
    for timestamp_ns, source_path in entries:
        if previous_timestamp is not None and timestamp_ns <= previous_timestamp:
            raise ValueError("Frame index timestamps must be strictly increasing.")
        if source_path.suffix.lower() != ".png":
            raise ValueError("Frame index source files must already be PNG images.")
        if not source_path.exists():
            raise ValueError(f"Frame index source path does not exist: {source_path}")
        previous_timestamp = timestamp_ns

    image_dir.mkdir(parents=True, exist_ok=True)
    timestamps_path.parent.mkdir(parents=True, exist_ok=True)

    written_timestamps: list[str] = []
    for timestamp_ns, source_path in entries:
        destination = image_dir / f"{timestamp_ns}.png"
        shutil.copyfile(source_path, destination)
        written_timestamps.append(str(timestamp_ns))

    timestamps_path.write_text("\n".join(written_timestamps) + "\n", encoding="utf-8")

    return PreparedSequence(
        first_timestamp_ns=entries[0][0],
        frame_count=len(entries),
        last_timestamp_ns=entries[-1][0],
    )


def resolve_monocular_trajectory_outputs(
    resolved: ResolvedMonocularBaselinePaths,
) -> MonocularTrajectoryOutputs:
    output_dir = resolved.trajectory_stem.parent
    stem_name = resolved.trajectory_stem.name
    return MonocularTrajectoryOutputs(
        frame_trajectory=output_dir / f"f_{stem_name}.txt",
        keyframe_trajectory=output_dir / f"kf_{stem_name}.txt",
    )


def build_monocular_tum_vi_command(
    resolved: ResolvedMonocularBaselinePaths,
) -> list[str]:
    return [
        str(resolved.executable),
        str(resolved.vocabulary),
        str(resolved.settings),
        str(resolved.image_dir),
        str(resolved.timestamps),
        resolved.trajectory_stem.name,
    ]
