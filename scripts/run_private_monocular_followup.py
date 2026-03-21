#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.monocular_baseline import (  # noqa: E402
    apply_monocular_output_tag,
    load_monocular_baseline_manifest,
    resolve_monocular_baseline_paths,
    resolve_monocular_trajectory_outputs,
)
from splatica_orb_test.monocular_inputs import (  # noqa: E402
    RAW_EXTRINSICS_FILENAME,
    resolve_lens_input_layout,
)
from splatica_orb_test.monocular_prereqs import (  # noqa: E402
    MonocularBaselinePrerequisites,
    PrerequisiteCheck,
    inspect_monocular_baseline_prerequisites,
)


DEFAULT_PROGRESS_ARTIFACT = REPO_ROOT / ".symphony/progress/HEL-73.json"
DEFAULT_ORCHESTRATION_LOG = (
    REPO_ROOT / "logs/out/hel-73_private_monocular_followup.log"
)
DEFAULT_STATUS_REPORT = (
    REPO_ROOT / "reports/out/hel-73_private_monocular_followup.md"
)
DEFAULT_OUTPUT_TAG = "orb_aggressive_asan_no_static_alignment"
TOTAL_PHASES = 5


@dataclass(frozen=True)
class SourceInputPaths:
    extrinsics: Path
    video_00: Path
    video_10: Path
    calibration_00: Path
    calibration_10: Path


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


def build_progress_payload(
    *,
    artifacts: dict[str, str],
    current_step: str,
    completed: int,
    status: str,
    metrics: dict[str, object] | None = None,
    experiment: dict[str, object] | None = None,
) -> dict[str, object]:
    clamped_completed = max(0, min(completed, TOTAL_PHASES))
    payload = {
        "status": status,
        "current_step": current_step,
        "progress_percent": round((clamped_completed / TOTAL_PHASES) * 100),
        "completed": clamped_completed,
        "total": TOTAL_PHASES,
        "unit": "phases",
        "metrics": metrics or {},
        "artifacts": artifacts,
    }
    if experiment:
        payload["experiment"] = experiment
    return payload


def write_progress_artifact(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def command_display(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(list(command))


def render_check_lines(checks: Sequence[PrerequisiteCheck]) -> list[str]:
    rendered: list[str] = []
    for check in checks:
        status = "ready" if check.ready else "missing"
        rendered.append(f"- {check.label}: **{status}** (`{check.detail}`)")
    return rendered


def resolve_source_inputs(
    dataset_root: Path,
    *,
    video_00: str | None,
    video_10: str | None,
    calibration_00: str | None,
    calibration_10: str | None,
    extrinsics: str | None,
) -> SourceInputPaths:
    lens00_layout = resolve_lens_input_layout(dataset_root, lens_id="00")
    lens10_layout = resolve_lens_input_layout(dataset_root, lens_id="10")
    return SourceInputPaths(
        video_00=resolve_repo_path(video_00) if video_00 else lens00_layout.raw_video_path,
        video_10=resolve_repo_path(video_10) if video_10 else lens10_layout.raw_video_path,
        calibration_00=(
            resolve_repo_path(calibration_00)
            if calibration_00
            else lens00_layout.raw_calibration_path
        ),
        calibration_10=(
            resolve_repo_path(calibration_10)
            if calibration_10
            else lens10_layout.raw_calibration_path
        ),
        extrinsics=(
            resolve_repo_path(extrinsics)
            if extrinsics
            else dataset_root / "raw" / "calibration" / RAW_EXTRINSICS_FILENAME
        ),
    )


def inspect_source_inputs(source_inputs: SourceInputPaths) -> tuple[PrerequisiteCheck, ...]:
    return (
        PrerequisiteCheck(
            label="Source video 00",
            ready=source_inputs.video_00.exists(),
            detail=str(source_inputs.video_00),
        ),
        PrerequisiteCheck(
            label="Source video 10",
            ready=source_inputs.video_10.exists(),
            detail=str(source_inputs.video_10),
        ),
        PrerequisiteCheck(
            label="Source calibration 00",
            ready=source_inputs.calibration_00.exists(),
            detail=str(source_inputs.calibration_00),
        ),
        PrerequisiteCheck(
            label="Source calibration 10",
            ready=source_inputs.calibration_10.exists(),
            detail=str(source_inputs.calibration_10),
        ),
        PrerequisiteCheck(
            label="Source stereo extrinsics",
            ready=source_inputs.extrinsics.exists(),
            detail=str(source_inputs.extrinsics),
        ),
    )


def render_status_report(
    *,
    command: str,
    dataset_root: Path,
    execution_blocked: bool,
    execution_details: list[str],
    experiment: Mapping[str, object],
    issue_identifier: str,
    prerequisites: MonocularBaselinePrerequisites,
    report_path: Path,
    run_log_path: Path,
    run_report_path: Path,
    source_checks: Sequence[PrerequisiteCheck],
    trajectory_path: Path,
) -> str:
    result_status = "blocked" if execution_blocked else "ready"
    detail_lines = "\n".join(f"- {detail}" for detail in execution_details) or "- none"
    experiment_lines = "\n".join(
        f"- {label}: `{value}`"
        for label, value in (
            ("Changed variable", experiment.get("changed_variable")),
            ("Hypothesis", experiment.get("hypothesis")),
            ("Success criterion", experiment.get("success_criterion")),
            ("Abort condition", experiment.get("abort_condition")),
            ("Expected artifact", experiment.get("expected_artifact")),
        )
        if value
    )
    return f"""# {issue_identifier} Private Monocular Follow-up Status

Issue: {issue_identifier}

## Result

- Status: `{result_status}`
- Dataset root: `{relative_to_repo(dataset_root)}`
- Orchestration log: `{relative_to_repo(run_log_path)}`
- Status report: `{relative_to_repo(report_path)}`
- Delegate monocular report: `{relative_to_repo(run_report_path)}`
- Expected trajectory artifact: `{relative_to_repo(trajectory_path)}`

## Experiment Contract

{experiment_lines}

## Source Input Contract

{os.linesep.join(render_check_lines(source_checks))}

## Repo Prerequisites

### Raw import prerequisites

{os.linesep.join(render_check_lines(prerequisites.raw_input_checks))}

### Prepare-only prerequisites

{os.linesep.join(render_check_lines(prerequisites.prepare_checks))}

### Execution prerequisites

{os.linesep.join(render_check_lines(prerequisites.execute_checks))}

## Command

`{command}`

## Execution Details

{detail_lines}
"""


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
        default="manifests/insta360_x3_lens10_monocular_baseline.json",
    )
    parser.add_argument("--video-00")
    parser.add_argument("--video-10")
    parser.add_argument("--calibration-00")
    parser.add_argument("--calibration-10")
    parser.add_argument("--extrinsics")
    parser.add_argument("--progress-artifact", default=str(DEFAULT_PROGRESS_ARTIFACT))
    parser.add_argument("--progress-issue", default="HEL-73")
    parser.add_argument("--orchestration-log", default=str(DEFAULT_ORCHESTRATION_LOG))
    parser.add_argument("--status-report", default=str(DEFAULT_STATUS_REPORT))
    parser.add_argument("--output-tag", default=DEFAULT_OUTPUT_TAG)
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--max-frames", type=int)
    args = parser.parse_args()

    manifest_path = resolve_repo_path(args.manifest)
    progress_artifact = resolve_repo_path(args.progress_artifact)
    orchestration_log = resolve_repo_path(args.orchestration_log)
    status_report = resolve_repo_path(args.status_report)
    issue_identifier = args.progress_issue

    manifest = load_monocular_baseline_manifest(manifest_path)
    resolved = apply_monocular_output_tag(
        resolve_monocular_baseline_paths(REPO_ROOT, manifest),
        args.output_tag,
    )
    trajectory_outputs = resolve_monocular_trajectory_outputs(resolved)
    dataset_root = resolved.calibration.parents[2]
    prerequisites = inspect_monocular_baseline_prerequisites(REPO_ROOT, manifest_path)
    source_inputs = resolve_source_inputs(
        dataset_root,
        video_00=args.video_00,
        video_10=args.video_10,
        calibration_00=args.calibration_00,
        calibration_10=args.calibration_10,
        extrinsics=args.extrinsics,
    )
    source_checks = inspect_source_inputs(source_inputs)

    experiment = {
        "changed_variable": (
            "replay the HEL-57 aggressive ORB lens-10 baseline after rebuilding "
            "mono_tum_vi with AddressSanitizer and disabled Eigen static alignment"
        ),
        "hypothesis": (
            "the combined HEL-72 build toggles will either let the private "
            "aggressive baseline save trajectories or surface a narrower post-init boundary"
        ),
        "success_criterion": (
            "the aggressive private rerun writes non-empty trajectory artifacts "
            "or leaves a more specific runtime boundary than HEL-57"
        ),
        "abort_condition": (
            "required source sidecars are missing, the build fails, or the rerun "
            "still aborts before trajectory save"
        ),
        "expected_artifact": relative_to_repo(trajectory_outputs.frame_trajectory),
    }
    artifacts = {
        "manifest": relative_to_repo(manifest_path),
        "runner": "scripts/run_private_monocular_followup.py",
        "orchestration_log": relative_to_repo(orchestration_log),
        "status_report": relative_to_repo(status_report),
        "delegate_log_path": relative_to_repo(resolved.log),
        "delegate_report_path": relative_to_repo(resolved.report),
        "expected_artifact": relative_to_repo(trajectory_outputs.frame_trajectory),
    }

    execution_details = [
        "Default lane: HEL-57 aggressive ORB settings plus HEL-72 ASan/no-static-alignment build toggles.",
        f"Frame stride: {args.frame_stride}",
        f"Max frames: {args.max_frames if args.max_frames is not None else 'full sequence'}",
    ]
    orchestration_log.parent.mkdir(parents=True, exist_ok=True)
    status_report.parent.mkdir(parents=True, exist_ok=True)
    with orchestration_log.open("w", encoding="utf-8") as log_handle:
        log_handle.write(f"Starting {issue_identifier} private monocular follow-up.\n")
        log_handle.write(f"Issue: {issue_identifier}\n")
        log_handle.write(f"Manifest: {relative_to_repo(manifest_path)}\n")
        log_handle.write(f"Output tag: {args.output_tag}\n")
        log_handle.write(f"Progress artifact: {relative_to_repo(progress_artifact)}\n\n")
        log_handle.flush()

        if not prerequisites.ready_for_prepare_only and not all(
            check.ready for check in source_checks
        ):
            missing_sources = [check.label for check in source_checks if not check.ready]
            blocked_reason = (
                "awaiting private calibration/extrinsics sidecars"
                if any(
                    "calibration" in label.lower() or "extrinsics" in label.lower()
                    for label in missing_sources
                )
                else "awaiting private raw videos"
            )
            execution_details.append(
                "Missing source inputs: " + ", ".join(missing_sources)
            )
            execution_details.append(
                "Next action: provide the missing raw source files or import the prepared lens-10 bundle into datasets/user/insta360_x3_one_lens_baseline/."
            )
            write_progress_artifact(
                progress_artifact,
                build_progress_payload(
                    artifacts=artifacts,
                    current_step=blocked_reason,
                    completed=0,
                    status="blocked",
                    metrics={"missing_source_inputs": missing_sources},
                    experiment=experiment,
                ),
            )
            status_report.write_text(
                render_status_report(
                    command="not started",
                    dataset_root=dataset_root,
                    execution_blocked=True,
                    execution_details=execution_details,
                    experiment=experiment,
                    issue_identifier=issue_identifier,
                    prerequisites=prerequisites,
                    report_path=status_report,
                    run_log_path=orchestration_log,
                    run_report_path=resolved.report,
                    source_checks=source_checks,
                    trajectory_path=trajectory_outputs.frame_trajectory,
                ),
                encoding="utf-8",
            )
            return 1

        phases: list[tuple[str, list[str], dict[str, str] | None, Path]] = []
        if not prerequisites.ready_for_prepare_only:
            phases.append(
                (
                    "importing private lens-10 bundle from raw source files",
                    [
                        sys.executable,
                        str(REPO_ROOT / "scripts/import_monocular_video_inputs.py"),
                        "--video-00",
                        str(source_inputs.video_00),
                        "--video-10",
                        str(source_inputs.video_10),
                        "--calibration-00",
                        str(source_inputs.calibration_00),
                        "--calibration-10",
                        str(source_inputs.calibration_10),
                        "--extrinsics",
                        str(source_inputs.extrinsics),
                        "--lenses",
                        "10",
                    ],
                    None,
                    REPO_ROOT,
                )
            )

        phases.extend(
            [
                (
                    "fetching pinned ORB-SLAM3 baseline checkout",
                    [str(REPO_ROOT / "scripts/fetch_orbslam3_baseline.sh")],
                    None,
                    REPO_ROOT,
                ),
                (
                    "building mono_tum_vi with ASan and disabled Eigen static alignment",
                    [str(REPO_ROOT / "scripts/build_orbslam3_baseline.sh")],
                    {
                        "ORB_SLAM3_BUILD_TARGET": "mono_tum_vi",
                        "ORB_SLAM3_BUILD_PARALLELISM": "1",
                        "ORB_SLAM3_BUILD_TYPE": "RelWithDebInfo",
                        "ORB_SLAM3_ENABLE_ASAN": "1",
                        "ORB_SLAM3_ASAN_COMPILE_FLAGS": " -fsanitize=address -fno-omit-frame-pointer -g -O0",
                        "ORB_SLAM3_DISABLE_EIGEN_STATIC_ALIGNMENT": "1",
                        "ORB_SLAM3_BUILD_EXPERIMENT": "hel-73-private-aggressive-followup",
                        "ORB_SLAM3_BUILD_CHANGED_VARIABLE": str(
                            experiment["changed_variable"]
                        ),
                        "ORB_SLAM3_BUILD_HYPOTHESIS": str(experiment["hypothesis"]),
                        "ORB_SLAM3_BUILD_SUCCESS_CRITERION": (
                            "mono_tum_vi rebuilds with the HEL-72 sanitizer and "
                            "alignment toggles before the aggressive private rerun"
                        ),
                        "ORB_SLAM3_PROGRESS_ARTIFACT": str(progress_artifact),
                        "ORB_SLAM3_PROGRESS_ISSUE_ID": issue_identifier,
                    },
                    REPO_ROOT,
                ),
                (
                    "running the HEL-57 aggressive private monocular follow-up",
                    [
                        sys.executable,
                        str(REPO_ROOT / "scripts/run_monocular_baseline.py"),
                        "--manifest",
                        str(manifest_path),
                        "--output-tag",
                        args.output_tag,
                        "--frame-stride",
                        str(args.frame_stride),
                        "--progress-artifact",
                        str(progress_artifact),
                        "--progress-issue",
                        issue_identifier,
                        "--changed-variable",
                        str(experiment["changed_variable"]),
                        "--hypothesis",
                        str(experiment["hypothesis"]),
                        "--success-criterion",
                        str(experiment["success_criterion"]),
                        "--abort-condition",
                        str(experiment["abort_condition"]),
                        "--expected-artifact",
                        str(experiment["expected_artifact"]),
                        "--orb-n-features",
                        "4000",
                        "--orb-ini-fast",
                        "8",
                        "--orb-min-fast",
                        "3",
                    ]
                    + (
                        ["--max-frames", str(args.max_frames)]
                        if args.max_frames is not None
                        else []
                    ),
                    None,
                    REPO_ROOT,
                ),
            ]
        )

        try:
            for phase_index, (current_step, command, env_overrides, cwd) in enumerate(
                phases,
                start=1,
            ):
                write_progress_artifact(
                    progress_artifact,
                    build_progress_payload(
                        artifacts=artifacts,
                        current_step=current_step,
                        completed=phase_index - 1,
                        status="in_progress",
                        metrics={},
                        experiment=experiment,
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
                            experiment=experiment,
                        ),
                    )

                run_command(
                    command=command,
                    cwd=cwd,
                    env_overrides=env_overrides,
                    log_handle=log_handle,
                    on_progress=on_progress,
                )
                execution_details.append(f"Completed phase {phase_index}: {current_step}")
        except subprocess.CalledProcessError as error:
            execution_details.append(
                f"Command failed with exit code {error.returncode}: {command_display(error.cmd)}"
            )
            write_progress_artifact(
                progress_artifact,
                build_progress_payload(
                    artifacts=artifacts,
                    current_step="follow-up command failed",
                    completed=max(0, len(phases) - 1),
                    status="failed",
                    metrics={
                        "failed_command": command_display(error.cmd),
                        "exit_code": error.returncode,
                    },
                    experiment=experiment,
                ),
            )
            status_report.write_text(
                render_status_report(
                    command=command_display(error.cmd),
                    dataset_root=dataset_root,
                    execution_blocked=True,
                    execution_details=execution_details,
                    experiment=experiment,
                    issue_identifier=issue_identifier,
                    prerequisites=inspect_monocular_baseline_prerequisites(
                        REPO_ROOT, manifest_path
                    ),
                    report_path=status_report,
                    run_log_path=orchestration_log,
                    run_report_path=resolved.report,
                    source_checks=source_checks,
                    trajectory_path=trajectory_outputs.frame_trajectory,
                ),
                encoding="utf-8",
            )
            return error.returncode

    write_progress_artifact(
        progress_artifact,
        build_progress_payload(
            artifacts=artifacts,
            current_step=f"{issue_identifier} private follow-up completed",
            completed=TOTAL_PHASES,
            status="completed",
            metrics={"delegate_report_path": relative_to_repo(resolved.report)},
            experiment=experiment,
        ),
    )
    status_report.write_text(
        render_status_report(
            command=command_display(phases[-1][1]),
            dataset_root=dataset_root,
            execution_blocked=False,
            execution_details=execution_details,
            experiment=experiment,
            issue_identifier=issue_identifier,
            prerequisites=inspect_monocular_baseline_prerequisites(REPO_ROOT, manifest_path),
            report_path=status_report,
            run_log_path=orchestration_log,
            run_report_path=resolved.report,
            source_checks=source_checks,
            trajectory_path=trajectory_outputs.frame_trajectory,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
