from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .rgbd_tum_baseline import (
    RgbdTumBaselineManifest,
    resolve_rgbd_tum_baseline_paths,
)


TOTAL_PHASES = 8


@dataclass(frozen=True)
class ProgressPhase:
    completed: int
    current_step: str
    total: int = TOTAL_PHASES
    unit: str = "phases"


def build_progress_payload(
    *,
    artifacts: dict[str, str],
    current_step: str,
    completed: int,
    total: int = TOTAL_PHASES,
    status: str,
    metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    clamped_completed = max(0, min(completed, total))
    progress_percent = round((clamped_completed / total) * 100) if total else 100
    payload: dict[str, object] = {
        "status": status,
        "current_step": current_step,
        "progress_percent": progress_percent,
        "completed": clamped_completed,
        "total": total,
        "unit": "phases",
        "metrics": metrics or {},
        "artifacts": artifacts,
    }
    return payload


def write_progress_artifact(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def fresh_execution_paths(
    repo_root: Path,
    manifest: RgbdTumBaselineManifest,
    *,
    orchestration_log: Path,
) -> tuple[Path, ...]:
    resolved = resolve_rgbd_tum_baseline_paths(repo_root, manifest)
    return (
        resolved.baseline_root,
        resolved.dataset_root,
        resolved.trajectory_dir,
        resolved.camera_trajectory,
        resolved.keyframe_trajectory,
        resolved.log,
        resolved.report,
        resolved.summary_json,
        resolved.trajectory_plot,
        resolved.visual_report,
        orchestration_log,
    )
