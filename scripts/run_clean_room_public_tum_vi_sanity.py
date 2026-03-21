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

from splatica_orb_test.clean_room_public_tum_vi import (  # noqa: E402
    TOTAL_PHASES,
    build_progress_payload,
    fresh_execution_paths,
    write_progress_artifact,
)
from splatica_orb_test.public_tum_vi import (  # noqa: E402
    load_public_tum_vi_manifest,
)


DEFAULT_PROGRESS_ARTIFACT = REPO_ROOT / ".symphony/progress/HEL-67.json"
DEFAULT_ORCHESTRATION_LOG = REPO_ROOT / "logs/out/tum_vi_room1_512_16_orchestration.log"
DEFAULT_BUILD_ATTEMPT_LATEST = REPO_ROOT / ".symphony/build-attempts/orbslam3-build-latest.json"
DEFAULT_BUILD_LOG_LATEST = REPO_ROOT / ".symphony/build-attempts/orbslam3-build-latest.log"
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
        "fetching public TUM-VI room1_512_16 archive",
        (str(REPO_ROOT / "scripts/fetch_tum_vi_dataset.py"), "--manifest"),
    ),
    (
        "materializing public TUM-VI cam0 calibration and frame index",
        (str(REPO_ROOT / "scripts/materialize_public_tum_vi_sequence.py"), "--manifest"),
    ),
    (
        "building upstream ORB-SLAM3 mono_tum_vi target",
        (str(REPO_ROOT / "scripts/build_orbslam3_baseline.sh"),),
    ),
    (
        "running upstream ORB-SLAM3 mono_tum_vi on public TUM-VI room1_512_16 cam0",
        (
            str(REPO_ROOT / "scripts/run_orbslam3_sequence.sh"),
            "--manifest",
        ),
    ),
)

EXPECTED_BUILD_OUTPUTS = (
    REPO_ROOT / "third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi",
    REPO_ROOT / "third_party/orbslam3/upstream/lib/libORB_SLAM3.so",
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
        default="manifests/tum_vi_room1_512_16_cam0_sanity.json",
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

    manifest = load_public_tum_vi_manifest(resolve_repo_path(args.manifest))
    progress_artifact = resolve_repo_path(args.progress_artifact)
    orchestration_log = resolve_repo_path(args.orchestration_log)
    artifacts = {
        "manifest": str(Path(args.manifest)),
        "runner": "scripts/run_clean_room_public_tum_vi_sanity.py",
        "orchestration_log": os.path.relpath(orchestration_log, REPO_ROOT),
        "build_attempt_latest": os.path.relpath(DEFAULT_BUILD_ATTEMPT_LATEST, REPO_ROOT),
        "build_log_latest": os.path.relpath(DEFAULT_BUILD_LOG_LATEST, REPO_ROOT),
    }

    for path in fresh_execution_paths(
        REPO_ROOT,
        manifest,
        orchestration_log=orchestration_log,
    ):
        remove_path(path)

    orchestration_log.parent.mkdir(parents=True, exist_ok=True)
    with orchestration_log.open("w", encoding="utf-8") as log_handle:
        log_handle.write("Starting fresh clean-room public TUM-VI sanity run.\n")
        log_handle.write(f"Manifest: {args.manifest}\n")
        log_handle.write(f"Progress artifact: {progress_artifact}\n\n")
        log_handle.flush()

        try:
            for phase_index, (current_step, base_command) in enumerate(PHASES, start=1):
                command = list(base_command)
                env_overrides: dict[str, str] | None = None
                if "--manifest" in command:
                    command.append(args.manifest)
                if command[0].endswith("build_orbslam3_baseline.sh"):
                    env_overrides = {
                        "ORB_SLAM3_BUILD_TARGET": "mono_tum_vi",
                        "ORB_SLAM3_APPEND_MARCH_NATIVE": os.environ.get(
                            "ORB_SLAM3_APPEND_MARCH_NATIVE", "OFF"
                        ),
                        "ORB_SLAM3_BUILD_PARALLELISM": os.environ.get(
                            "ORB_SLAM3_BUILD_PARALLELISM", "1"
                        ),
                        "ORB_SLAM3_BUILD_TYPE": os.environ.get(
                            "ORB_SLAM3_BUILD_TYPE", ""
                        ),
                        "ORB_SLAM3_ENABLE_ASAN": os.environ.get(
                            "ORB_SLAM3_ENABLE_ASAN", "0"
                        ),
                        "ORB_SLAM3_ASAN_COMPILE_FLAGS": os.environ.get(
                            "ORB_SLAM3_ASAN_COMPILE_FLAGS",
                            " -fsanitize=address -fno-omit-frame-pointer -g -O1",
                        ),
                        "ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT": os.environ.get(
                            "ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT", "0"
                        ),
                        "ORB_SLAM3_BUILD_EXPERIMENT": os.environ.get(
                            "ORB_SLAM3_BUILD_EXPERIMENT",
                            "clean-room-tum-vi-room1-portable-build",
                        ),
                        "ORB_SLAM3_BUILD_CHANGED_VARIABLE": os.environ.get(
                            "ORB_SLAM3_BUILD_CHANGED_VARIABLE",
                            "prove the public mono_tum_vi lane on room1_512_16 with a fresh checkout, repo-local bootstraps, and a single-job build"
                        ),
                        "ORB_SLAM3_BUILD_HYPOTHESIS": os.environ.get(
                            "ORB_SLAM3_BUILD_HYPOTHESIS",
                            "the pinned upstream checkout plus repo-local dependency prefixes will either build mono_tum_vi for a public room1_512_16 replay or surface a concrete compiler/linker blocker"
                        ),
                        "ORB_SLAM3_BUILD_SUCCESS_CRITERION": os.environ.get(
                            "ORB_SLAM3_BUILD_SUCCESS_CRITERION",
                            "mono_tum_vi and libORB_SLAM3.so both exist after the build phase"
                        ),
                    }

                write_progress_artifact(
                    progress_artifact,
                    build_progress_payload(
                        artifacts=artifacts,
                        current_step=current_step,
                        completed=phase_index - 1,
                        total=TOTAL_PHASES,
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
                            total=TOTAL_PHASES,
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

                if command[0].endswith("build_orbslam3_baseline.sh"):
                    missing_outputs = [
                        str(path.relative_to(REPO_ROOT))
                        for path in EXPECTED_BUILD_OUTPUTS
                        if not path.exists()
                    ]
                    if missing_outputs:
                        raise RuntimeError(
                            "build phase completed without expected outputs: "
                            + ", ".join(missing_outputs)
                        )

                write_progress_artifact(
                    progress_artifact,
                    build_progress_payload(
                        artifacts=artifacts,
                        current_step=current_step,
                        completed=phase_index,
                        total=TOTAL_PHASES,
                        status="in_progress",
                        metrics={"phase": phase_index, "result": "completed"},
                    ),
                )
        except (subprocess.CalledProcessError, RuntimeError) as error:
            if isinstance(error, subprocess.CalledProcessError):
                failed_command = command_display(error.cmd)
                exit_code = error.returncode
            else:
                failed_command = str(error)
                exit_code = 1
            log_handle.write(
                f"\nCommand failed with exit code {exit_code}: {failed_command}\n"
            )
            log_handle.flush()
            write_progress_artifact(
                progress_artifact,
                build_progress_payload(
                    artifacts=artifacts,
                    current_step=f"failed: {failed_command}",
                    completed=max(0, phase_index - 1),
                    total=TOTAL_PHASES,
                    status="failed",
                    metrics={
                        "phase": phase_index,
                        "exit_code": exit_code,
                        "failed_command": failed_command,
                    },
                ),
            )
            return exit_code

    write_progress_artifact(
        progress_artifact,
        build_progress_payload(
            artifacts=artifacts,
            current_step="completed clean-room public TUM-VI sanity run",
            completed=TOTAL_PHASES,
            total=TOTAL_PHASES,
            status="completed",
            metrics={"result": "success"},
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
