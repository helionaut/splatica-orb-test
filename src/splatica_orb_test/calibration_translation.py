from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .monocular_baseline import (
    DEFAULT_ORB,
    DEFAULT_VIEWER,
    MonocularCalibration,
    OrbParameters,
    ViewerParameters,
    render_monocular_settings_yaml,
)


SUPPORTED_SOURCE_CAMERA_MODELS = {
    "KANNALABRANDT4",
    "KANNALABRANDT8",
}
SUPPORTED_COLOR_ORDERS = {"RGB", "BGR"}
REQUIRED_MONOCULAR_SETTINGS_KEYS = (
    "File.version",
    "Camera.type",
    "Camera1.fx",
    "Camera1.fy",
    "Camera1.cx",
    "Camera1.cy",
    "Camera1.k1",
    "Camera1.k2",
    "Camera1.k3",
    "Camera1.k4",
    "Camera.width",
    "Camera.height",
    "Camera.fps",
    "Camera.RGB",
    "ORBextractor.nFeatures",
    "ORBextractor.scaleFactor",
    "ORBextractor.nLevels",
    "ORBextractor.iniThFAST",
    "ORBextractor.minThFAST",
    "Viewer.KeyFrameSize",
    "Viewer.KeyFrameLineWidth",
    "Viewer.GraphLineWidth",
    "Viewer.PointSize",
    "Viewer.CameraSize",
    "Viewer.CameraLineWidth",
    "Viewer.ViewpointX",
    "Viewer.ViewpointY",
    "Viewer.ViewpointZ",
    "Viewer.ViewpointF",
)
REQUIRED_IMU_FIELDS = (
    "noise_gyro",
    "noise_acc",
    "gyro_walk",
    "acc_walk",
    "frequency_hz",
)


@dataclass(frozen=True)
class ShareableLensCalibration:
    camera_label: str
    cx: float
    cy: float
    fx: float
    fy: float
    k1: float
    k2: float
    k3: float
    k4: float


@dataclass(frozen=True)
class ShareableRigExtrinsics:
    quaternion_xyzw: tuple[float, float, float, float]
    reference_camera: str
    relative_camera: str
    translation_m: tuple[float, float, float]


@dataclass(frozen=True)
class ShareableRigCalibration:
    cameras: dict[str, ShareableLensCalibration]
    image_height: int
    image_width: int
    layout: str
    notes: str
    raw: dict[str, object]
    reference_camera: str
    rig_extrinsics: ShareableRigExtrinsics | None
    source_camera_model: str
    source_file_names: tuple[str, ...]
    source_reference: str


@dataclass(frozen=True)
class CalibrationSmokeLensProfile:
    color_order: str
    fps: float
    lens_id: str
    notes: str
    orb_overrides: dict[str, object]
    output_path: str
    viewer_overrides: dict[str, object]


@dataclass(frozen=True)
class CalibrationConfigSmokeManifest:
    calibration_path: str
    launch_mode: str
    launch_script: str
    log_path: str
    notes: str
    profiles: tuple[CalibrationSmokeLensProfile, ...]
    report_path: str


@dataclass(frozen=True)
class CalibrationSmokeLensOutput:
    camera_label: str
    color_order: str
    fps: float
    lens_id: str
    output_path: Path


@dataclass(frozen=True)
class CalibrationConfigSmokeRun:
    blockers: tuple[str, ...]
    calibration_path: Path
    log_path: Path
    notes: str
    outputs: tuple[CalibrationSmokeLensOutput, ...]
    report_path: Path
    rig_extrinsics: ShareableRigExtrinsics | None
    source_camera_model: str
    source_reference: str


def _load_json(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected a JSON object at {path}.")
    return raw


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


def _require_dict(raw: object, *, name: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise ValueError(f"{name} must be an object.")
    return raw


def _load_lens_calibration(
    *,
    lens_id: str,
    raw: object,
) -> ShareableLensCalibration:
    lens = _require_dict(raw, name=f"rig.cameras.{lens_id}")
    intrinsics = _require_dict(
        lens.get("intrinsics"),
        name=f"rig.cameras.{lens_id}.intrinsics",
    )
    distortion = _require_dict(
        lens.get("distortion"),
        name=f"rig.cameras.{lens_id}.distortion",
    )

    return ShareableLensCalibration(
        camera_label=str(lens["label"]),
        fx=float(intrinsics["fx"]),
        fy=float(intrinsics["fy"]),
        cx=float(intrinsics["cx"]),
        cy=float(intrinsics["cy"]),
        k1=float(distortion["k1"]),
        k2=float(distortion["k2"]),
        k3=float(distortion["k3"]),
        k4=float(distortion["k4"]),
    )


def _load_rig_extrinsics(raw: object) -> ShareableRigExtrinsics | None:
    if raw is None:
        return None

    extrinsics = _require_dict(raw, name="rig.extrinsics")
    translation = extrinsics.get("translation_m")
    quaternion = extrinsics.get("quaternion_xyzw")

    if not isinstance(translation, list) or len(translation) != 3:
        raise ValueError("rig.extrinsics.translation_m must contain 3 numbers.")
    if not isinstance(quaternion, list) or len(quaternion) != 4:
        raise ValueError("rig.extrinsics.quaternion_xyzw must contain 4 numbers.")

    return ShareableRigExtrinsics(
        reference_camera=str(extrinsics["reference_camera"]),
        relative_camera=str(extrinsics["relative_camera"]),
        translation_m=tuple(float(value) for value in translation),
        quaternion_xyzw=tuple(float(value) for value in quaternion),
    )


def load_shareable_rig_calibration(path: Path) -> ShareableRigCalibration:
    raw = _load_json(path)
    rig = _require_dict(raw.get("rig"), name="rig")
    source = _require_dict(raw.get("source"), name="source")
    cameras = _require_dict(rig.get("cameras"), name="rig.cameras")

    source_camera_model = str(rig["source_model"]).strip()
    if source_camera_model.upper() not in SUPPORTED_SOURCE_CAMERA_MODELS:
        raise ValueError(
            "Only Kannala-Brandt 4/8 source models are supported for the shareable "
            "translation lane."
        )

    loaded_cameras = {
        lens_id: _load_lens_calibration(lens_id=lens_id, raw=lens_raw)
        for lens_id, lens_raw in cameras.items()
    }

    reference_camera = str(rig["reference_camera"])
    if reference_camera not in loaded_cameras:
        raise ValueError("rig.reference_camera must name one of rig.cameras.")

    raw_source_file_names = source.get("source_file_names", [])
    if not isinstance(raw_source_file_names, list):
        raise ValueError("source.source_file_names must be a list when provided.")

    return ShareableRigCalibration(
        cameras=loaded_cameras,
        image_width=int(rig["image_width"]),
        image_height=int(rig["image_height"]),
        layout=str(rig["layout"]),
        notes=str(raw.get("notes", "")),
        raw=raw,
        reference_camera=reference_camera,
        rig_extrinsics=_load_rig_extrinsics(rig.get("extrinsics")),
        source_camera_model=source_camera_model,
        source_file_names=tuple(str(name) for name in raw_source_file_names),
        source_reference=str(source.get("reference", "")),
    )


def build_shareable_monocular_calibration(
    calibration: ShareableRigCalibration,
    *,
    color_order: str | None,
    fps: int | float | None,
    lens_id: str,
    orb_overrides: dict[str, object] | None = None,
    viewer_overrides: dict[str, object] | None = None,
) -> MonocularCalibration:
    lens = calibration.cameras.get(lens_id)
    if lens is None:
        raise ValueError(f"Unknown lens id: {lens_id}")

    missing = []
    if fps is None:
        missing.append("fps")
    if color_order is None:
        missing.append("color_order")

    if missing:
        raise ValueError(
            "Missing required monocular overrides: " + ", ".join(sorted(missing))
        )

    normalized_color_order = color_order.upper()
    if normalized_color_order not in SUPPORTED_COLOR_ORDERS:
        raise ValueError(
            "color_order must be either RGB or BGR for ORB-SLAM3 rendering."
        )
    if float(fps) <= 0:
        raise ValueError("fps must be positive.")

    orb_raw = orb_overrides or {}
    viewer_raw = viewer_overrides or {}
    if not isinstance(orb_raw, dict):
        raise ValueError("orb overrides must be an object when provided.")
    if not isinstance(viewer_raw, dict):
        raise ValueError("viewer overrides must be an object when provided.")

    return MonocularCalibration(
        camera_label=lens.camera_label,
        camera_model="KannalaBrandt8",
        color_order=normalized_color_order,
        fps=float(fps),
        fx=lens.fx,
        fy=lens.fy,
        cx=lens.cx,
        cy=lens.cy,
        image_width=calibration.image_width,
        image_height=calibration.image_height,
        k1=lens.k1,
        k2=lens.k2,
        k3=lens.k3,
        k4=lens.k4,
        notes=calibration.notes,
        orb=_load_orb_parameters(orb_raw),
        viewer=_load_viewer_parameters(viewer_raw),
    )


def render_shareable_monocular_settings_yaml(
    calibration: ShareableRigCalibration,
    *,
    color_order: str,
    fps: int | float,
    lens_id: str,
    orb_overrides: dict[str, object] | None = None,
    source_label: str | None = None,
    viewer_overrides: dict[str, object] | None = None,
) -> str:
    monocular = build_shareable_monocular_calibration(
        calibration,
        color_order=color_order,
        fps=fps,
        lens_id=lens_id,
        orb_overrides=orb_overrides,
        viewer_overrides=viewer_overrides,
    )
    base = render_monocular_settings_yaml(monocular)
    lines = base.splitlines()
    source_text = source_label or "shareable calibration bundle"
    camera_rgb = 1 if color_order.upper() == "RGB" else 0

    comment_block = [
        lines[0],
        "",
        f"# Generated from {source_text} lens `{lens_id}`.",
        "# Source model mapping: the provided Kannala-Brandt source intrinsics map",
        "# directly into ORB-SLAM3's KannalaBrandt8 scalar fields fx, fy, cx, cy,",
        "# and k1-k4 for the monocular fisheye baseline.",
        f"# Smoke/profile override Camera.fps: {float(fps)}",
        f"# Smoke/profile override Camera.RGB: {camera_rgb} ({color_order.upper()})",
    ]

    return "\n".join(comment_block + lines[1:]) + "\n"


def parse_orbslam3_scalar_settings_text(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "%YAML:1.0":
        raise ValueError("ORB-SLAM3 settings must start with the %YAML:1.0 header.")

    parsed: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith("!!opencv-matrix"):
            raise ValueError(
                "The scalar settings smoke validator does not support matrix blocks."
            )
        if ":" not in stripped:
            raise ValueError(f"Unsupported ORB-SLAM3 settings line: {line}")

        key, raw_value = stripped.split(":", 1)
        value = raw_value.split("#", 1)[0].strip()
        if not value:
            raise ValueError(f"Missing value for ORB-SLAM3 setting {key}.")

        parsed[key.strip()] = value

    return parsed


def validate_orbslam3_monocular_settings_text(text: str) -> dict[str, str]:
    parsed = parse_orbslam3_scalar_settings_text(text)

    missing = [
        key for key in REQUIRED_MONOCULAR_SETTINGS_KEYS if key not in parsed
    ]
    if missing:
        raise ValueError(
            "Missing required ORB-SLAM3 monocular settings: "
            + ", ".join(sorted(missing))
        )

    if parsed["Camera.type"].strip('"') != "KannalaBrandt8":
        raise ValueError("Camera.type must be KannalaBrandt8 for this baseline.")
    if int(float(parsed["Camera.width"])) <= 0 or int(float(parsed["Camera.height"])) <= 0:
        raise ValueError("Camera.width and Camera.height must be positive.")
    if float(parsed["Camera.fps"]) <= 0:
        raise ValueError("Camera.fps must be positive.")
    if parsed["Camera.RGB"] not in {"0", "1"}:
        raise ValueError("Camera.RGB must be either 0 or 1.")

    return parsed


def list_full_rig_blockers(calibration: ShareableRigCalibration) -> tuple[str, ...]:
    blockers: list[str] = []

    if calibration.layout != "overlapping_stereo":
        blockers.append(
            "rig.layout is not overlapping_stereo, so the first pass should not "
            "emit a standard ORB-SLAM3 stereo pair settings bundle."
        )

    if calibration.rig_extrinsics is None:
        blockers.append("Missing rig.extrinsics needed for Stereo.T_c1_c2.")

    camera_to_imu = calibration.raw.get("camera_to_imu")
    if not isinstance(camera_to_imu, dict):
        blockers.append("Missing camera_to_imu needed for IMU.T_b_c1.")

    imu = calibration.raw.get("imu")
    if not isinstance(imu, dict):
        blockers.extend(
            [
                "Missing imu.noise_gyro needed for IMU.NoiseGyro.",
                "Missing imu.noise_acc needed for IMU.NoiseAcc.",
                "Missing imu.gyro_walk needed for IMU.GyroWalk.",
                "Missing imu.acc_walk needed for IMU.AccWalk.",
                "Missing imu.frequency_hz needed for IMU.Frequency.",
            ]
        )
    else:
        for field_name in REQUIRED_IMU_FIELDS:
            if field_name not in imu:
                blockers.append(
                    f"Missing imu.{field_name} needed for the ORB-SLAM3 IMU block."
                )

    if not calibration.source_file_names:
        blockers.append(
            "Missing source.source_file_names for provenance; the current repo only "
            "has the values quoted in HEL-47 comments."
        )

    return tuple(blockers)


def load_calibration_config_smoke_manifest(
    path: Path,
) -> CalibrationConfigSmokeManifest:
    raw = _load_json(path)
    calibration = _require_dict(raw.get("calibration"), name="calibration")
    outputs = _require_dict(raw.get("outputs"), name="outputs")
    launch = _require_dict(raw.get("launch"), name="launch")
    raw_profiles = raw.get("profiles")

    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise ValueError("profiles must be a non-empty list.")

    profiles = []
    for index, raw_profile in enumerate(raw_profiles, start=1):
        profile = _require_dict(raw_profile, name=f"profiles[{index}]")
        orb_overrides = profile.get("orb", {})
        viewer_overrides = profile.get("viewer", {})
        if not isinstance(orb_overrides, dict):
            raise ValueError(f"profiles[{index}].orb must be an object if provided.")
        if not isinstance(viewer_overrides, dict):
            raise ValueError(
                f"profiles[{index}].viewer must be an object if provided."
            )

        profiles.append(
            CalibrationSmokeLensProfile(
                lens_id=str(profile["lens_id"]),
                output_path=str(profile["output_path"]),
                fps=float(profile["fps"]),
                color_order=str(profile["color_order"]),
                notes=str(profile.get("notes", "")),
                orb_overrides=orb_overrides,
                viewer_overrides=viewer_overrides,
            )
        )

    return CalibrationConfigSmokeManifest(
        calibration_path=str(calibration["path"]),
        launch_mode=str(launch["mode"]),
        launch_script=str(launch["script"]),
        log_path=str(outputs["log_path"]),
        notes=str(raw.get("notes", "")),
        profiles=tuple(profiles),
        report_path=str(outputs["report_path"]),
    )


def _relative_to_repo(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _render_calibration_config_smoke_log(
    *,
    calibration_path: Path,
    outputs: tuple[CalibrationSmokeLensOutput, ...],
    repo_root: Path,
    blockers: tuple[str, ...],
    notes: str,
) -> str:
    lines = [
        f"Calibration config smoke: {_relative_to_repo(repo_root, calibration_path)}",
        f"Generated outputs: {len(outputs)}",
    ]

    for output in outputs:
        lines.append(
            f"- lens {output.lens_id}: {_relative_to_repo(repo_root, output.output_path)} "
            f"(fps={output.fps}, color_order={output.color_order})"
        )

    lines.append("Blockers:")
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.append(f"Notes: {notes}")
    return "\n".join(lines) + "\n"


def _render_calibration_config_smoke_report(
    *,
    calibration_path: Path,
    outputs: tuple[CalibrationSmokeLensOutput, ...],
    repo_root: Path,
    blockers: tuple[str, ...],
    notes: str,
    rig_extrinsics: ShareableRigExtrinsics | None,
    source_camera_model: str,
    source_reference: str,
) -> str:
    lines = [
        "# Calibration config smoke report",
        "",
        "## Result",
        "",
        f"- Calibration bundle: `{_relative_to_repo(repo_root, calibration_path)}`",
        f"- Source camera model: `{source_camera_model}`",
    ]

    if source_reference:
        lines.append(f"- Source reference: `{source_reference}`")

    lines.extend(
        [
            "",
            "## Generated settings bundles",
            "",
        ]
    )
    for output in outputs:
        lines.append(
            f"- Lens `{output.lens_id}` -> `{_relative_to_repo(repo_root, output.output_path)}` "
            f"with `Camera.fps={output.fps}` and `Camera.RGB="
            f"{1 if output.color_order == 'RGB' else 0} ({output.color_order})`"
        )

    lines.extend(
        [
            "",
            "## Raw rig extrinsics",
            "",
        ]
    )
    if rig_extrinsics is None:
        lines.append("- No shareable rig extrinsics are currently recorded.")
    else:
        lines.extend(
            [
                f"- Reference camera: `{rig_extrinsics.reference_camera}`",
                f"- Relative camera: `{rig_extrinsics.relative_camera}`",
                f"- Translation (meters): `{list(rig_extrinsics.translation_m)}`",
                f"- Quaternion xyzw: `{list(rig_extrinsics.quaternion_xyzw)}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Explicit blockers",
            "",
        ]
    )
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(
        [
            "",
            "## Notes",
            "",
            notes,
            "",
        ]
    )
    return "\n".join(lines)


def run_calibration_config_smoke(
    repo_root: Path,
    manifest: CalibrationConfigSmokeManifest,
) -> CalibrationConfigSmokeRun:
    calibration_path = repo_root / manifest.calibration_path
    calibration = load_shareable_rig_calibration(calibration_path)

    outputs = []
    for profile in manifest.profiles:
        output_path = repo_root / profile.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        settings_text = render_shareable_monocular_settings_yaml(
            calibration,
            color_order=profile.color_order,
            fps=profile.fps,
            lens_id=profile.lens_id,
            orb_overrides=profile.orb_overrides,
            source_label=manifest.calibration_path,
            viewer_overrides=profile.viewer_overrides,
        )
        validate_orbslam3_monocular_settings_text(settings_text)
        output_path.write_text(settings_text, encoding="utf-8")
        outputs.append(
            CalibrationSmokeLensOutput(
                camera_label=calibration.cameras[profile.lens_id].camera_label,
                color_order=profile.color_order.upper(),
                fps=profile.fps,
                lens_id=profile.lens_id,
                output_path=output_path,
            )
        )

    blockers = list_full_rig_blockers(calibration)
    log_path = repo_root / manifest.log_path
    report_path = repo_root / manifest.report_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    outputs_tuple = tuple(outputs)
    log_path.write_text(
        _render_calibration_config_smoke_log(
            calibration_path=calibration_path,
            outputs=outputs_tuple,
            repo_root=repo_root,
            blockers=blockers,
            notes=manifest.notes,
        ),
        encoding="utf-8",
    )
    report_path.write_text(
        _render_calibration_config_smoke_report(
            calibration_path=calibration_path,
            outputs=outputs_tuple,
            repo_root=repo_root,
            blockers=blockers,
            notes=manifest.notes,
            rig_extrinsics=calibration.rig_extrinsics,
            source_camera_model=calibration.source_camera_model,
            source_reference=calibration.source_reference,
        ),
        encoding="utf-8",
    )

    return CalibrationConfigSmokeRun(
        blockers=blockers,
        calibration_path=calibration_path,
        log_path=log_path,
        notes=manifest.notes,
        outputs=outputs_tuple,
        report_path=report_path,
        rig_extrinsics=calibration.rig_extrinsics,
        source_camera_model=calibration.source_camera_model,
        source_reference=calibration.source_reference,
    )
