from __future__ import annotations

from dataclasses import dataclass, replace
import html
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class RgbdTumAssociationEntry:
    depth_path: str
    depth_timestamp: float
    rgb_path: str
    rgb_timestamp: float


@dataclass(frozen=True)
class RgbdTumBaselineManifest:
    archive_path: str
    archive_url: str
    association_path: str
    baseline_commit: str
    baseline_name: str
    camera_trajectory_path: str
    checkout_path: str
    dataset_name: str
    dataset_root: str
    executable_path: str
    keyframe_trajectory_path: str
    launch_script: str
    log_path: str
    notes: str
    repo_url: str
    report_path: str
    sequence_name: str
    settings_path: str
    summary_json_path: str
    trajectory_dir: str
    trajectory_plot_path: str
    visual_report_path: str
    vocabulary_path: str


@dataclass(frozen=True)
class ResolvedRgbdTumBaselinePaths:
    archive: Path
    association: Path
    baseline_root: Path
    camera_trajectory: Path
    dataset_root: Path
    executable: Path
    keyframe_trajectory: Path
    log: Path
    report: Path
    settings: Path
    summary_json: Path
    trajectory_dir: Path
    trajectory_plot: Path
    visual_report: Path
    vocabulary: Path


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rgbd_tum_baseline_manifest(path: Path) -> RgbdTumBaselineManifest:
    raw = _load_json(path)

    try:
        baseline = raw["baseline"]
        sequence = raw["sequence"]
        outputs = raw["outputs"]
        launch = raw["launch"]
        notes = raw["notes"]
    except KeyError as error:
        raise ValueError(f"Missing manifest section: {error.args[0]}") from error

    if not all(
        isinstance(section, dict)
        for section in (baseline, sequence, outputs, launch)
    ):
        raise ValueError(
            "Manifest sections baseline, sequence, outputs, and launch must be objects."
        )

    return RgbdTumBaselineManifest(
        archive_path=str(sequence["archive_path"]),
        archive_url=str(sequence["archive_url"]),
        association_path=str(sequence["association_path"]),
        baseline_commit=str(baseline["commit"]),
        baseline_name=str(baseline["name"]),
        camera_trajectory_path=str(outputs["camera_trajectory_path"]),
        checkout_path=str(baseline["checkout_path"]),
        dataset_name=str(sequence["dataset_name"]),
        dataset_root=str(sequence["dataset_root"]),
        executable_path=str(baseline["executable_path"]),
        keyframe_trajectory_path=str(outputs["keyframe_trajectory_path"]),
        launch_script=str(launch["script"]),
        log_path=str(outputs["log_path"]),
        notes=str(notes),
        repo_url=str(baseline["repo_url"]),
        report_path=str(outputs["report_path"]),
        sequence_name=str(sequence["name"]),
        settings_path=str(sequence["settings_path"]),
        summary_json_path=str(outputs["summary_json_path"]),
        trajectory_dir=str(outputs["trajectory_dir"]),
        trajectory_plot_path=str(outputs["trajectory_plot_path"]),
        visual_report_path=str(outputs["visual_report_path"]),
        vocabulary_path=str(baseline["vocabulary_path"]),
    )


def resolve_rgbd_tum_baseline_paths(
    repo_root: Path,
    manifest: RgbdTumBaselineManifest,
) -> ResolvedRgbdTumBaselinePaths:
    baseline_root = repo_root / manifest.checkout_path
    return ResolvedRgbdTumBaselinePaths(
        archive=repo_root / manifest.archive_path,
        association=repo_root / manifest.association_path,
        baseline_root=baseline_root,
        camera_trajectory=repo_root / manifest.camera_trajectory_path,
        dataset_root=repo_root / manifest.dataset_root,
        executable=baseline_root / manifest.executable_path,
        keyframe_trajectory=repo_root / manifest.keyframe_trajectory_path,
        log=repo_root / manifest.log_path,
        report=repo_root / manifest.report_path,
        settings=repo_root / manifest.settings_path,
        summary_json=repo_root / manifest.summary_json_path,
        trajectory_dir=repo_root / manifest.trajectory_dir,
        trajectory_plot=repo_root / manifest.trajectory_plot_path,
        visual_report=repo_root / manifest.visual_report_path,
        vocabulary=baseline_root / manifest.vocabulary_path,
    )


def apply_rgbd_tum_output_tag(
    resolved: ResolvedRgbdTumBaselinePaths,
    output_tag: str | None,
) -> ResolvedRgbdTumBaselinePaths:
    if not output_tag:
        return resolved

    normalized_tag = output_tag.strip()
    if not normalized_tag:
        return resolved

    suffix = f"_{normalized_tag}"
    trajectory_dir = resolved.trajectory_dir.parent / f"{resolved.trajectory_dir.name}{suffix}"
    return replace(
        resolved,
        camera_trajectory=trajectory_dir / resolved.camera_trajectory.name,
        keyframe_trajectory=trajectory_dir / resolved.keyframe_trajectory.name,
        log=resolved.log.with_name(f"{resolved.log.stem}{suffix}{resolved.log.suffix}"),
        report=resolved.report.with_name(
            f"{resolved.report.stem}{suffix}{resolved.report.suffix}"
        ),
        trajectory_dir=trajectory_dir,
        summary_json=resolved.summary_json.with_name(
            f"{resolved.summary_json.stem}{suffix}{resolved.summary_json.suffix}"
        ),
        trajectory_plot=resolved.trajectory_plot.with_name(
            f"{resolved.trajectory_plot.stem}{suffix}{resolved.trajectory_plot.suffix}"
        ),
        visual_report=resolved.visual_report.with_name(
            f"{resolved.visual_report.stem}{suffix}{resolved.visual_report.suffix}"
        ),
    )


def build_rgbd_tum_command(
    resolved: ResolvedRgbdTumBaselinePaths,
) -> list[str]:
    return [
        str(resolved.executable),
        str(resolved.vocabulary),
        str(resolved.settings),
        str(resolved.dataset_root),
        str(resolved.association),
    ]


def load_rgbd_tum_associations(path: Path) -> list[RgbdTumAssociationEntry]:
    entries: list[RgbdTumAssociationEntry] = []
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(
                f"Association line {index} in {path} did not contain four fields."
            )
        rgb_timestamp, rgb_path, depth_timestamp, depth_path = parts
        entries.append(
            RgbdTumAssociationEntry(
                depth_path=depth_path,
                depth_timestamp=float(depth_timestamp),
                rgb_path=rgb_path,
                rgb_timestamp=float(rgb_timestamp),
            )
        )
    return entries


def load_tum_trajectory_points(path: Path) -> list[tuple[float, float, float, float]]:
    points: list[tuple[float, float, float, float]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        timestamp, tx, ty, tz = parts[:4]
        points.append((float(timestamp), float(tx), float(ty), float(tz)))
    return points


def compute_tum_trajectory_metrics(
    points: list[tuple[float, float, float, float]],
) -> dict[str, float | int | None]:
    if not points:
        return {
            "point_count": 0,
            "start_timestamp": None,
            "end_timestamp": None,
            "duration_seconds": 0.0,
            "path_length_meters": 0.0,
            "displacement_meters": 0.0,
            "min_x": None,
            "max_x": None,
            "min_y": None,
            "max_y": None,
            "min_z": None,
            "max_z": None,
        }

    xs = [point[1] for point in points]
    ys = [point[2] for point in points]
    zs = [point[3] for point in points]
    path_length = 0.0
    for start, end in zip(points, points[1:]):
        path_length += math.dist(start[1:], end[1:])

    displacement = math.dist(points[0][1:], points[-1][1:])
    start_timestamp = points[0][0]
    end_timestamp = points[-1][0]
    return {
        "point_count": len(points),
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "duration_seconds": round(end_timestamp - start_timestamp, 6),
        "path_length_meters": round(path_length, 6),
        "displacement_meters": round(displacement, 6),
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "min_z": min(zs),
        "max_z": max(zs),
    }


def render_tum_trajectory_svg(
    points: list[tuple[float, float, float, float]],
    *,
    title: str,
) -> str:
    width = 960
    height = 640
    margin = 70
    plot_width = width - (margin * 2)
    plot_height = height - (margin * 2)

    if not points:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#f6f2e8" />
  <text x="{margin}" y="{margin}" font-family="monospace" font-size="28" fill="#1f1f1f">{html.escape(title)}</text>
  <text x="{margin}" y="{margin + 48}" font-family="monospace" font-size="22" fill="#4c4c4c">No trajectory points available.</text>
</svg>
"""

    xs = [point[1] for point in points]
    zs = [point[3] for point in points]
    min_x = min(xs)
    max_x = max(xs)
    min_z = min(zs)
    max_z = max(zs)
    if min_x == max_x:
        min_x -= 0.5
        max_x += 0.5
    if min_z == max_z:
        min_z -= 0.5
        max_z += 0.5

    def project(point: tuple[float, float, float, float]) -> tuple[float, float]:
        x_ratio = (point[1] - min_x) / (max_x - min_x)
        z_ratio = (point[3] - min_z) / (max_z - min_z)
        x = margin + (x_ratio * plot_width)
        y = height - margin - (z_ratio * plot_height)
        return (x, y)

    polyline = " ".join(f"{x:.2f},{y:.2f}" for x, y in map(project, points))
    start_x, start_y = project(points[0])
    end_x, end_y = project(points[-1])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#f6f2e8" />
  <text x="{margin}" y="42" font-family="monospace" font-size="28" fill="#1f1f1f">{html.escape(title)}</text>
  <text x="{margin}" y="74" font-family="monospace" font-size="18" fill="#4c4c4c">Projection: x/z, points: {len(points)}</text>
  <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#8e8e8e" stroke-width="2" />
  <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#8e8e8e" stroke-width="2" />
  <polyline fill="none" stroke="#19647e" stroke-width="4" points="{polyline}" />
  <circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="7" fill="#2a9d8f" />
  <circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="7" fill="#e76f51" />
  <text x="{margin}" y="{height - 22}" font-family="monospace" font-size="18" fill="#4c4c4c">x range: {min_x:.3f} .. {max_x:.3f}</text>
  <text x="{width - 320}" y="{height - 22}" font-family="monospace" font-size="18" fill="#4c4c4c">z range: {min_z:.3f} .. {max_z:.3f}</text>
</svg>
"""
