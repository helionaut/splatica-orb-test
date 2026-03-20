from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .public_tum_vi import PublicTumViManifest, resolve_public_tum_vi_paths


TOTAL_PHASES = 10


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
    return {
        "status": status,
        "current_step": current_step,
        "progress_percent": progress_percent,
        "completed": clamped_completed,
        "total": total,
        "unit": "phases",
        "metrics": metrics or {},
        "artifacts": artifacts,
    }


def write_progress_artifact(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def fresh_execution_paths(
    repo_root: Path,
    manifest: PublicTumViManifest,
    *,
    orchestration_log: Path,
) -> tuple[Path, ...]:
    resolved = resolve_public_tum_vi_paths(repo_root, manifest)
    return (
        resolved.baseline_root,
        resolved.dataset_root,
        resolved.calibration,
        resolved.frame_index,
        resolved.image_dir,
        resolved.trajectory_stem.parent,
        resolved.log,
        resolved.report,
        resolved.summary_json,
        resolved.trajectory_plot,
        resolved.visual_report,
        orchestration_log,
    )
