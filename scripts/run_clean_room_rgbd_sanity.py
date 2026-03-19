#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.clean_room_rgbd_sanity import (  # noqa: E402
    TOTAL_PHASES,
    build_progress_payload,
    fresh_execution_paths,
    write_progress_artifact,
)
from splatica_orb_test.rgbd_tum_baseline import (  # noqa: E402
    load_rgbd_tum_baseline_manifest,
)


DEFAULT_PROGRESS_ARTIFACT = REPO_ROOT / ".symphony/progress/HEL-61.json"
DEFAULT_ORCHESTRATION_LOG = REPO_ROOT / "logs/out/tum_rgbd_fr1_xyz_orchestration.log"
PHASES: tuple[tuple[str, Sequence[str]], ...] = (
    (
        "fetching fresh upstream ORB-SLAM3 checkout",
        (str(REPO_ROOT / "scripts/fetch_orbslam3_baseline.sh"),),
    ),
    (
        "bootstrapping repo-local cmake toolchain",
        (str(REPO_ROOT / "scripts/bootstrap_local_cmake.sh"),),
    ),
    (
        "bootstrapping repo-local Eigen3 prefix",
        (str(REPO_ROOT / "scripts/bootstrap_local_eigen.sh"),),
    ),
    (
        "bootstrapping repo-local OpenCV prefix",
        (str(REPO_ROOT / "scripts/bootstrap_local_opencv.sh"),),
    ),
    (
        "bootstrapping repo-local Boost serialization prefix",
        (str(REPO_ROOT / "scripts/bootstrap_local_boost.sh"),),
    ),
    (
        "bootstrapping repo-local Pangolin prefix",
        (str(REPO_ROOT / "scripts/bootstrap_local_pangolin.sh"),),
    ),
    (
        "building upstream ORB-SLAM3 rgbd_tum target",
        (str(REPO_ROOT / "scripts/build_orbslam3_baseline.sh"),),
    ),
    (
        "running upstream ORB-SLAM3 rgbd_tum on TUM fr1/xyz",
        (
            str(REPO_ROOT / "scripts/run_orbslam3_sequence.sh"),
            "--manifest",
        ),
    ),
)


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    if path.is_dir():
        shutil.rmtree(path)


def command_display(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(list(command))


def run_command(
    *,
    command: Sequence[str],
    cwd: Path,
    env_overrides: Mapping[str, str] | None,
    log_handle,
    on_progress,
) -> None:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None

    output_queue: queue.Queue[str | None] = queue.Queue()

    def reader() -> None:
        for line in process.stdout:
            output_queue.put(line)
        output_queue.put(None)

    threading.Thread(target=reader, daemon=True).start()

    line_count = 0
    start_time = time.monotonic()
    last_output_time = start_time
    last_progress_time = 0.0

    while True:
        try:
            item = output_queue.get(timeout=5.0)
        except queue.Empty:
            item = ""

        now = time.monotonic()
        if item is None:
            if process.poll() is not None:
                break
        elif item:
            log_handle.write(item)
            log_handle.flush()
            line_count += 1
            last_output_time = now

        if now - last_progress_time >= 30.0:
            on_progress(
                {
                    "command": command_display(command),
                    "elapsed_seconds": round(now - start_time, 1),
                    "output_lines": line_count,
                    "seconds_since_output": round(now - last_output_time, 1),
                }
            )
            last_progress_time = now

        if process.poll() is not None and item is None:
            break

    exit_code = process.wait()
    if exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, list(command))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="manifests/tum_rgbd_fr1_xyz_sanity.json",
    )
    parser.add_argument(
        "--progress-artifact",
        default=str(DEFAULT_PROGRESS_ARTIFACT),
    )
    parser.add_argument(
        "--orchestration-log",
        default=str(DEFAULT_ORCHESTRATION_LOG),
    )
    args = parser.parse_args()

    manifest = load_rgbd_tum_baseline_manifest(resolve_repo_path(args.manifest))
    progress_artifact = resolve_repo_path(args.progress_artifact)
    orchestration_log = resolve_repo_path(args.orchestration_log)
    artifacts = {
        "manifest": str(Path(args.manifest)),
        "runner": "scripts/run_clean_room_rgbd_sanity.sh",
        "orchestration_log": os.path.relpath(orchestration_log, REPO_ROOT),
    }

    for path in fresh_execution_paths(
        REPO_ROOT,
        manifest,
        orchestration_log=orchestration_log,
    ):
        remove_path(path)

    orchestration_log.parent.mkdir(parents=True, exist_ok=True)
    with orchestration_log.open("w", encoding="utf-8") as log_handle:
        log_handle.write("Starting fresh clean-room RGB-D sanity run.\n")
        log_handle.write(f"Manifest: {args.manifest}\n")
        log_handle.write(f"Progress artifact: {progress_artifact}\n\n")
        log_handle.flush()

        try:
            for phase_index, (current_step, base_command) in enumerate(PHASES, start=1):
                command = list(base_command)
                env_overrides: dict[str, str] | None = None
                if command[0].endswith("build_orbslam3_baseline.sh"):
                    env_overrides = {"ORB_SLAM3_BUILD_TARGET": "rgbd_tum"}
                if command[0].endswith("run_orbslam3_sequence.sh"):
                    command.append(args.manifest)

                write_progress_artifact(
                    progress_artifact,
                    build_progress_payload(
                        artifacts=artifacts,
                        current_step=current_step,
                        completed=phase_index - 1,
                        status="in_progress",
                        metrics={},
                    ),
                )
                log_handle.write(f"$ {command_display(command)}\n")
                log_handle.flush()

                def on_progress(metrics: dict[str, object]) -> None:
                    write_progress_artifact(
                        progress_artifact,
                        build_progress_payload(
                            artifacts=artifacts,
                            current_step=current_step,
                            completed=phase_index - 1,
                            status="in_progress",
                            metrics={"phase": phase_index, **metrics},
                        ),
                    )

                run_command(
                    command=command,
                    cwd=REPO_ROOT,
                    env_overrides=env_overrides,
                    log_handle=log_handle,
                    on_progress=on_progress,
                )

                write_progress_artifact(
                    progress_artifact,
                    build_progress_payload(
                        artifacts=artifacts,
                        current_step=current_step,
                        completed=phase_index,
                        status="in_progress",
                        metrics={"phase": phase_index, "result": "completed"},
                    ),
                )
        except subprocess.CalledProcessError as error:
            failed_command = command_display(error.cmd)
            log_handle.write(
                f"\nCommand failed with exit code {error.returncode}: {failed_command}\n"
            )
            log_handle.flush()
            write_progress_artifact(
                progress_artifact,
                build_progress_payload(
                    artifacts=artifacts,
                    current_step=f"failed: {failed_command}",
                    completed=phase_index - 1,
                    status="failed",
                    metrics={
                        "phase": phase_index,
                        "exit_code": error.returncode,
                        "failed_command": failed_command,
                    },
                ),
            )
            return error.returncode

    write_progress_artifact(
        progress_artifact,
        build_progress_payload(
            artifacts=artifacts,
            current_step="completed clean-room RGB-D sanity run",
            completed=TOTAL_PHASES,
            status="completed",
            metrics={"result": "success"},
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
