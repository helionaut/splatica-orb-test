#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys
import time


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.monocular_runtime_progress import (  # noqa: E402
    build_monocular_progress_payload,
    summarize_monocular_runtime_log,
    write_progress_snapshot,
)


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def relative_to_repo(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_total_frames(timestamps_path: Path) -> int:
    with timestamps_path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def pid_is_alive(pid: int) -> bool:
    return Path(f"/proc/{pid}").exists()


def build_experiment(args: argparse.Namespace) -> dict[str, object]:
    return {
        key: value
        for key, value in {
            "changed_variable": args.changed_variable,
            "hypothesis": args.hypothesis,
            "success_criterion": args.success_criterion,
            "abort_condition": args.abort_condition,
            "expected_artifact": args.expected_artifact,
        }.items()
        if value
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-path", required=True)
    parser.add_argument("--timestamps-path", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--issue")
    parser.add_argument("--runner", default="scripts/monitor_monocular_progress.py")
    parser.add_argument("--report-path")
    parser.add_argument("--trajectory-dir")
    parser.add_argument("--command")
    parser.add_argument("--pid", type=int)
    parser.add_argument("--poll-seconds", type=float, default=60.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--changed-variable", default="")
    parser.add_argument("--hypothesis", default="")
    parser.add_argument("--success-criterion", default="")
    parser.add_argument("--abort-condition", default="")
    parser.add_argument("--expected-artifact", default="")
    args = parser.parse_args()

    log_path = resolve_repo_path(args.log_path)
    timestamps_path = resolve_repo_path(args.timestamps_path)
    artifact_path = resolve_repo_path(args.artifact)
    report_path = resolve_repo_path(args.report_path) if args.report_path else None
    trajectory_dir = (
        resolve_repo_path(args.trajectory_dir) if args.trajectory_dir else None
    )
    issue = args.issue or artifact_path.stem or "monocular-progress"
    experiment = build_experiment(args)
    artifacts = {
        "runner": args.runner,
        "log_path": relative_to_repo(log_path),
        "timestamps_path": relative_to_repo(timestamps_path),
    }
    if report_path is not None:
        artifacts["report_path"] = relative_to_repo(report_path)
    if trajectory_dir is not None:
        artifacts["trajectory_dir"] = relative_to_repo(trajectory_dir)

    if args.poll_seconds <= 0:
        raise SystemExit("--poll-seconds must be positive")

    while True:
        total_frames = read_total_frames(timestamps_path)
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        summary = summarize_monocular_runtime_log(lines, total_frames=total_frames)
        log_stat = log_path.stat()
        metrics: dict[str, object] = {
            "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "latest_started_frame": summary.latest_started_frame,
            "latest_completed_frame": summary.latest_completed_frame,
            "local_map_failure_count": summary.local_map_failure_count,
            "map_creation_count": summary.map_creation_count,
            "stored_map_count": summary.stored_map_count,
            "latest_map_id": summary.latest_map_id,
            "latest_stored_map_id": summary.latest_stored_map_id,
            "latest_map_last_kf_id": summary.latest_map_last_kf_id,
            "latest_map_first_kf": summary.latest_map_first_kf,
            "latest_map_init_kf": summary.latest_map_init_kf,
            "latest_map_points": summary.latest_map_points,
            "latest_changed_map_id": summary.latest_changed_map_id,
            "merge_detected_count": summary.merge_detected_count,
            "merge_finished_count": summary.merge_finished_count,
            "local_mapping_release_count": summary.local_mapping_release_count,
            "local_mapping_stop_count": summary.local_mapping_stop_count,
            "log_size_bytes": log_stat.st_size,
            "seconds_since_log_update": round(time.time() - log_stat.st_mtime, 1),
            "shutdown_started": summary.shutdown_started,
            "shutdown_completed": summary.shutdown_completed,
        }
        if args.command:
            metrics["command"] = args.command
        if trajectory_dir is not None:
            metrics["trajectory_files"] = sorted(
                path.name for path in trajectory_dir.glob("*") if path.is_file()
            )

        status = "in_progress"
        if args.pid is not None and not pid_is_alive(args.pid):
            status = "completed" if summary.shutdown_completed else "failed"
            metrics["pid_exited"] = True
        elif args.pid is not None:
            metrics["pid_exited"] = False

        payload = build_monocular_progress_payload(
            issue=issue,
            status=status,
            summary=summary,
            artifacts=artifacts,
            metrics=metrics,
            experiment=experiment,
        )
        write_progress_snapshot(artifact_path, payload)
        print(
            f"[{metrics['observed_at']}] {status} "
            f"completed={summary.completed_frames}/{summary.total_frames} "
            f"step={summary.current_step}",
            flush=True,
        )

        if args.once or status != "in_progress":
            return 0

        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
