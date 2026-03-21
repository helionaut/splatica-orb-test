from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable


FRAME_START_PATTERN = re.compile(
    r"HEL-68 diagnostic: frame (\d+) TrackMonocular start timestamp="
)
FRAME_COMPLETED_PATTERN = re.compile(
    r"HEL-68 diagnostic: frame (\d+) TrackMonocular completed"
)
MAP_CREATION_PATTERN = re.compile(r"Creation of new map with id: (\d+)")
STORED_MAP_PATTERN = re.compile(r"Stored map with ID: (\d+)")
MAP_LAST_KF_PATTERN = re.compile(r"Creation of new map with last KF id: (\d+)")
MAP_INIT_PATTERN = re.compile(r"First KF:(\d+); Map init KF:(\d+)")
MAP_POINTS_PATTERN = re.compile(r"New Map created with (\d+) points")
LOCAL_MAP_FAILURE_MARKER = "Fail to track local map!"
SHUTDOWN_START_MARKER = "HEL-63 diagnostic: entering SLAM shutdown"
SHUTDOWN_COMPLETED_MARKER = "HEL-63 diagnostic: SLAM shutdown completed"


@dataclass(frozen=True)
class MonocularRuntimeSummary:
    current_step: str
    completed_frames: int
    total_frames: int
    latest_started_frame: int | None
    latest_completed_frame: int | None
    last_line: str
    shutdown_started: bool
    shutdown_completed: bool
    local_map_failure_count: int
    map_creation_count: int
    stored_map_count: int
    latest_map_id: int | None
    latest_stored_map_id: int | None
    latest_map_last_kf_id: int | None
    latest_map_first_kf: int | None
    latest_map_init_kf: int | None
    latest_map_points: int | None


def summarize_monocular_runtime_log(
    lines: Iterable[str],
    *,
    total_frames: int,
) -> MonocularRuntimeSummary:
    latest_started_frame: int | None = None
    latest_completed_frame: int | None = None
    last_line = ""
    current_step = "launching mono_tum_vi"
    shutdown_started = False
    shutdown_completed = False
    local_map_failure_count = 0
    map_creation_count = 0
    stored_map_count = 0
    latest_map_id: int | None = None
    latest_stored_map_id: int | None = None
    latest_map_last_kf_id: int | None = None
    latest_map_first_kf: int | None = None
    latest_map_init_kf: int | None = None
    latest_map_points: int | None = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue

        last_line = stripped
        if stripped == LOCAL_MAP_FAILURE_MARKER:
            local_map_failure_count += 1
            current_step = stripped
            continue

        if match := FRAME_START_PATTERN.search(stripped):
            latest_started_frame = int(match.group(1))
            current_step = f"frame {latest_started_frame} TrackMonocular start"
            continue

        if match := FRAME_COMPLETED_PATTERN.search(stripped):
            latest_completed_frame = max(
                latest_completed_frame or -1,
                int(match.group(1)),
            )
            current_step = f"completed frame {latest_completed_frame + 1}"
            continue

        if match := MAP_CREATION_PATTERN.search(stripped):
            map_creation_count += 1
            latest_map_id = int(match.group(1))
            current_step = stripped
            continue

        if match := STORED_MAP_PATTERN.search(stripped):
            stored_map_count += 1
            latest_stored_map_id = int(match.group(1))
            current_step = stripped
            continue

        if match := MAP_LAST_KF_PATTERN.search(stripped):
            latest_map_last_kf_id = int(match.group(1))
            current_step = stripped
            continue

        if match := MAP_INIT_PATTERN.search(stripped):
            latest_map_first_kf = int(match.group(1))
            latest_map_init_kf = int(match.group(2))
            current_step = stripped
            continue

        if match := MAP_POINTS_PATTERN.search(stripped):
            latest_map_points = int(match.group(1))
            current_step = stripped
            continue

        if SHUTDOWN_START_MARKER in stripped:
            shutdown_started = True
            current_step = "entering SLAM shutdown"
            continue

        if SHUTDOWN_COMPLETED_MARKER in stripped:
            shutdown_completed = True
            current_step = "SLAM shutdown completed"
            continue

        if "HEL-68 diagnostic: stopping after " in stripped:
            current_step = stripped
            continue

        current_step = stripped

    completed_frames = (
        0 if latest_completed_frame is None else latest_completed_frame + 1
    )
    return MonocularRuntimeSummary(
        current_step=current_step,
        completed_frames=completed_frames,
        total_frames=total_frames,
        latest_started_frame=latest_started_frame,
        latest_completed_frame=latest_completed_frame,
        last_line=last_line,
        shutdown_started=shutdown_started,
        shutdown_completed=shutdown_completed,
        local_map_failure_count=local_map_failure_count,
        map_creation_count=map_creation_count,
        stored_map_count=stored_map_count,
        latest_map_id=latest_map_id,
        latest_stored_map_id=latest_stored_map_id,
        latest_map_last_kf_id=latest_map_last_kf_id,
        latest_map_first_kf=latest_map_first_kf,
        latest_map_init_kf=latest_map_init_kf,
        latest_map_points=latest_map_points,
    )


def build_monocular_progress_payload(
    *,
    issue: str,
    status: str,
    summary: MonocularRuntimeSummary,
    artifacts: dict[str, str],
    metrics: dict[str, object],
    experiment: dict[str, object] | None = None,
) -> dict[str, object]:
    progress_percent = (
        round((summary.completed_frames / summary.total_frames) * 100)
        if summary.total_frames
        else 100
    )
    payload: dict[str, object] = {
        "status": status,
        "current_step": summary.current_step,
        "progress_percent": progress_percent,
        "completed": summary.completed_frames,
        "total": summary.total_frames,
        "unit": "frames",
        "issue": issue,
        "metrics": metrics,
        "artifacts": artifacts,
    }
    if experiment:
        payload["experiment"] = experiment
    return payload


def write_progress_snapshot(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".jsonl":
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return

    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
