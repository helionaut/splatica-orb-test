#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.monocular_baseline import (  # noqa: E402
    apply_monocular_orb_overrides,
    apply_monocular_output_tag,
    build_monocular_tum_vi_command,
    load_monocular_baseline_manifest,
    load_monocular_calibration,
    prepare_monocular_sequence,
    render_monocular_settings_yaml,
    resolve_monocular_trajectory_outputs,
    resolve_monocular_baseline_paths,
)
from splatica_orb_test.local_tooling import (  # noqa: E402
    resolve_headless_display_prefix,
    resolve_repo_local_boost_runtime_library_paths,
    resolve_repo_local_opencv_runtime_library_paths,
    resolve_repo_local_pangolin_runtime_library_paths,
)


FRAME_START_PATTERN = re.compile(
    r"HEL-68 diagnostic: frame (\d+) TrackMonocular start timestamp="
)
FRAME_COMPLETED_PATTERN = re.compile(
    r"HEL-68 diagnostic: frame (\d+) TrackMonocular completed"
)
NEW_MAP_CREATED_PATTERN = re.compile(r"New Map created with (\d+) points")
RESET_ACTIVE_MAP_PATTERN = re.compile(r"SYSTEM-> Reseting active map in monocular case")
SAVE_TRAJECTORY_PATTERN = re.compile(r"Saving trajectory to (\S+) \.\.\.")
SAVE_KEYFRAME_TRAJECTORY_PATTERN = re.compile(
    r"Saving keyframe trajectory to (\S+) \.\.\."
)
ASAN_SUMMARY_PATTERN = re.compile(r"SUMMARY: AddressSanitizer: (.+)")
DEFAULT_PROGRESS_ARTIFACT = os.environ.get("ORB_SLAM3_PROGRESS_ARTIFACT", "")
DEFAULT_PROGRESS_ISSUE = os.environ.get("ORB_SLAM3_PROGRESS_ISSUE_ID", "")
DEFAULT_CHANGED_VARIABLE = os.environ.get("ORB_SLAM3_RUN_CHANGED_VARIABLE", "")
DEFAULT_HYPOTHESIS = os.environ.get("ORB_SLAM3_RUN_HYPOTHESIS", "")
DEFAULT_SUCCESS_CRITERION = os.environ.get("ORB_SLAM3_RUN_SUCCESS_CRITERION", "")
DEFAULT_ABORT_CONDITION = os.environ.get("ORB_SLAM3_RUN_ABORT_CONDITION", "")
DEFAULT_EXPECTED_ARTIFACT = os.environ.get("ORB_SLAM3_RUN_EXPECTED_ARTIFACT", "")


@dataclass(frozen=True)
class RuntimeLogSummary:
    map_points: tuple[int, ...]
    reset_count: int
    frame_trajectory_save_path: str | None
    frame_trajectory_save_completed: bool
    keyframe_trajectory_save_path: str | None
    keyframe_trajectory_save_completed: bool
    keyframe_trajectory_skipped: bool
    asan_summary: str | None


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


def render_report(
    *,
    command: list[str],
    execution_mode: str,
    exit_code: int | None,
    manifest_notes: str,
    prepared_frame_count: int,
    report_path: Path,
    result_details: list[str],
    run_workdir: Path,
    resolved,
    trajectory_outputs,
) -> str:
    command_text = shlex.join(command)
    exit_line = "not executed" if exit_code is None else str(exit_code)
    detail_lines = "\n".join(f"- {detail}" for detail in result_details) or "- none recorded"

    return f"""# Monocular baseline report: {resolved.report.stem}

## Result

- Execution mode: `{execution_mode}`
- Exit code: `{exit_line}`
- Prepared frames: `{prepared_frame_count}`

## Baseline

- ORB-SLAM3 checkout: `{relative_to_repo(resolved.baseline_root)}`
- Executable: `{relative_to_repo(resolved.executable)}`
- Vocabulary: `{relative_to_repo(resolved.vocabulary)}`

## Inputs

- Calibration JSON: `{relative_to_repo(resolved.calibration)}`
- Frame index CSV: `{relative_to_repo(resolved.frame_index)}`

## Generated artifacts

- Settings YAML: `{relative_to_repo(resolved.settings)}`
- Prepared image directory: `{relative_to_repo(resolved.image_dir)}`
- Prepared timestamps file: `{relative_to_repo(resolved.timestamps)}`
- Trajectory stem: `{relative_to_repo(resolved.trajectory_stem)}`
- Trajectory working directory: `{relative_to_repo(run_workdir)}`
- Expected frame trajectory: `{relative_to_repo(trajectory_outputs.frame_trajectory)}`
- Expected keyframe trajectory: `{relative_to_repo(trajectory_outputs.keyframe_trajectory)}`
- Log path: `{relative_to_repo(resolved.log)}`
- Report path: `{relative_to_repo(report_path)}`

## Planned command

`{command_text}`

## Result details

{detail_lines}

## Notes

{manifest_notes}
"""


def write_prepare_only_log(
    *,
    command: list[str],
    manifest_notes: str,
    prepared_frame_count: int,
    run_workdir: Path,
    resolved,
    trajectory_outputs,
) -> None:
    resolved.log.parent.mkdir(parents=True, exist_ok=True)
    resolved.log.write_text(
        "\n".join(
            [
                f"Preparation-only run for {resolved.report.stem}",
                f"Prepared frames: {prepared_frame_count}",
                f"Settings YAML: {relative_to_repo(resolved.settings)}",
                f"Prepared image directory: {relative_to_repo(resolved.image_dir)}",
                f"Prepared timestamps file: {relative_to_repo(resolved.timestamps)}",
                f"Trajectory working directory: {relative_to_repo(run_workdir)}",
                f"Expected frame trajectory: {relative_to_repo(trajectory_outputs.frame_trajectory)}",
                f"Expected keyframe trajectory: {relative_to_repo(trajectory_outputs.keyframe_trajectory)}",
                f"Command: {shlex.join(command)}",
                f"Notes: {manifest_notes}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_runtime_environment() -> dict[str, str]:
    env = os.environ.copy()
    runtime_paths: list[str] = []
    for path in resolve_repo_local_opencv_runtime_library_paths(REPO_ROOT):
        runtime_paths.append(str(path))
    for path in resolve_repo_local_boost_runtime_library_paths(REPO_ROOT):
        runtime_paths.append(str(path))
    for path in resolve_repo_local_pangolin_runtime_library_paths(REPO_ROOT):
        runtime_paths.append(str(path))
    if runtime_paths:
        existing = env.get("LD_LIBRARY_PATH")
        unique_runtime_paths = list(dict.fromkeys(runtime_paths))
        env["LD_LIBRARY_PATH"] = ":".join(
            unique_runtime_paths + ([existing] if existing else [])
        )
    return env


def write_progress_artifact(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def render_runtime_progress(
    *,
    artifacts: dict[str, str],
    issue: str,
    status: str,
    current_step: str,
    completed: int,
    total: int,
    metrics: dict[str, object],
    experiment: dict[str, object],
) -> dict[str, object]:
    clamped_completed = max(0, min(completed, total))
    progress_percent = round((clamped_completed / total) * 100) if total else 100
    payload = {
        "status": status,
        "current_step": current_step,
        "progress_percent": progress_percent,
        "completed": clamped_completed,
        "total": total,
        "unit": "frames",
        "issue": issue,
        "metrics": metrics,
        "artifacts": artifacts,
    }
    if experiment:
        payload["experiment"] = experiment
    return payload


def inspect_trajectory_outputs(
    trajectory_outputs,
    *,
    skip_frame_trajectory_save: bool,
    skip_keyframe_trajectory_save: bool,
    path_renderer: Callable[[Path], str],
) -> tuple[list[str], list[Path]]:
    result_details: list[str] = []
    missing_or_empty_outputs: list[Path] = []

    for label, trajectory_path, skipped in (
        (
            "Frame trajectory",
            trajectory_outputs.frame_trajectory,
            skip_frame_trajectory_save,
        ),
        (
            "Keyframe trajectory",
            trajectory_outputs.keyframe_trajectory,
            skip_keyframe_trajectory_save,
        ),
    ):
        if skipped:
            result_details.append(
                f"{label}: intentionally skipped at {path_renderer(trajectory_path)}"
            )
            continue

        if not trajectory_path.exists():
            result_details.append(
                f"{label}: missing at {path_renderer(trajectory_path)}"
            )
            missing_or_empty_outputs.append(trajectory_path)
            continue

        size_bytes = trajectory_path.stat().st_size
        result_details.append(
            f"{label}: {path_renderer(trajectory_path)} ({size_bytes} bytes)"
        )
        if size_bytes == 0:
            missing_or_empty_outputs.append(trajectory_path)

    return result_details, missing_or_empty_outputs


def summarize_runtime_log(log_path: Path) -> RuntimeLogSummary:
    map_points: list[int] = []
    reset_count = 0
    frame_trajectory_save_path: str | None = None
    frame_trajectory_save_completed = False
    keyframe_trajectory_save_path: str | None = None
    keyframe_trajectory_save_completed = False
    keyframe_trajectory_skipped = False
    asan_summary: str | None = None

    if not log_path.exists():
        return RuntimeLogSummary(
            map_points=(),
            reset_count=0,
            frame_trajectory_save_path=None,
            frame_trajectory_save_completed=False,
            keyframe_trajectory_save_path=None,
            keyframe_trajectory_save_completed=False,
            keyframe_trajectory_skipped=False,
            asan_summary=None,
        )

    for raw_line in log_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if match := NEW_MAP_CREATED_PATTERN.search(line):
            map_points.append(int(match.group(1)))
        if RESET_ACTIVE_MAP_PATTERN.search(line):
            reset_count += 1
        if match := SAVE_TRAJECTORY_PATTERN.search(line):
            frame_trajectory_save_path = match.group(1)
        if match := SAVE_KEYFRAME_TRAJECTORY_PATTERN.search(line):
            keyframe_trajectory_save_path = match.group(1)
        if "HEL-63 diagnostic: SaveTrajectoryEuRoC completed" in line:
            frame_trajectory_save_completed = True
        if "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed" in line:
            keyframe_trajectory_save_completed = True
        if "No keyframes were recorded; skipping keyframe trajectory save." in line:
            keyframe_trajectory_skipped = True
        if match := ASAN_SUMMARY_PATTERN.search(line):
            asan_summary = match.group(1)

    return RuntimeLogSummary(
        map_points=tuple(map_points),
        reset_count=reset_count,
        frame_trajectory_save_path=frame_trajectory_save_path,
        frame_trajectory_save_completed=frame_trajectory_save_completed,
        keyframe_trajectory_save_path=keyframe_trajectory_save_path,
        keyframe_trajectory_save_completed=keyframe_trajectory_save_completed,
        keyframe_trajectory_skipped=keyframe_trajectory_skipped,
        asan_summary=asan_summary,
    )


def render_runtime_log_details(summary: RuntimeLogSummary) -> list[str]:
    details: list[str] = []

    if summary.map_points:
        point_list = ", ".join(str(points) for points in summary.map_points)
        details.append(
            f"Initialization maps created: {len(summary.map_points)} (points={point_list})"
        )
    if summary.reset_count:
        details.append(f"Active map resets observed: {summary.reset_count}")
    if summary.frame_trajectory_save_path:
        details.append(
            f"Frame trajectory save invoked for {summary.frame_trajectory_save_path}"
        )
    if summary.frame_trajectory_save_completed:
        details.append("Frame trajectory save call reached completion")
    if summary.keyframe_trajectory_save_path:
        details.append(
            f"Keyframe trajectory save invoked for {summary.keyframe_trajectory_save_path}"
        )
    if summary.keyframe_trajectory_save_completed:
        details.append("Keyframe trajectory save call reached completion")
    if summary.keyframe_trajectory_skipped:
        details.append(
            "Keyframe trajectory save skipped because no keyframes were recorded"
        )
    if summary.asan_summary:
        details.append(f"AddressSanitizer summary: {summary.asan_summary}")

    return details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--output-tag")
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--progress-artifact", default=DEFAULT_PROGRESS_ARTIFACT)
    parser.add_argument("--progress-issue", default=DEFAULT_PROGRESS_ISSUE)
    parser.add_argument("--changed-variable", default=DEFAULT_CHANGED_VARIABLE)
    parser.add_argument("--hypothesis", default=DEFAULT_HYPOTHESIS)
    parser.add_argument("--success-criterion", default=DEFAULT_SUCCESS_CRITERION)
    parser.add_argument("--abort-condition", default=DEFAULT_ABORT_CONDITION)
    parser.add_argument("--expected-artifact", default=DEFAULT_EXPECTED_ARTIFACT)
    parser.add_argument("--orb-n-features", type=int)
    parser.add_argument("--orb-ini-fast", type=int)
    parser.add_argument("--orb-min-fast", type=int)
    parser.add_argument("--skip-frame-trajectory-save", action="store_true")
    parser.add_argument("--skip-keyframe-trajectory-save", action="store_true")
    args = parser.parse_args()

    manifest = load_monocular_baseline_manifest(resolve_repo_path(args.manifest))
    resolved = apply_monocular_output_tag(
        resolve_monocular_baseline_paths(REPO_ROOT, manifest),
        args.output_tag,
    )

    calibration = apply_monocular_orb_overrides(
        load_monocular_calibration(resolved.calibration),
        n_features=args.orb_n_features,
        ini_fast=args.orb_ini_fast,
        min_fast=args.orb_min_fast,
    )
    resolved.settings.parent.mkdir(parents=True, exist_ok=True)
    resolved.settings.write_text(
        render_monocular_settings_yaml(calibration),
        encoding="utf-8",
    )

    prepared = prepare_monocular_sequence(
        resolved.frame_index,
        resolved.image_dir,
        resolved.timestamps,
        frame_stride=args.frame_stride,
    )
    run_workdir = resolved.trajectory_stem.parent
    run_workdir.mkdir(parents=True, exist_ok=True)
    trajectory_outputs = resolve_monocular_trajectory_outputs(resolved)
    progress_artifact = (
        resolve_repo_path(args.progress_artifact) if args.progress_artifact else None
    )
    progress_total = args.max_frames if args.max_frames is not None else prepared.frame_count
    progress_artifacts = {
        "manifest": args.manifest,
        "runner": "scripts/run_monocular_baseline.py",
        "log_path": relative_to_repo(resolved.log),
        "report_path": relative_to_repo(resolved.report),
        "settings_path": relative_to_repo(resolved.settings),
        "trajectory_stem": relative_to_repo(resolved.trajectory_stem),
    }
    expected_artifact = args.expected_artifact or relative_to_repo(
        trajectory_outputs.frame_trajectory
    )
    experiment = {
        key: value
        for key, value in {
            "changed_variable": args.changed_variable,
            "hypothesis": args.hypothesis,
            "success_criterion": args.success_criterion,
            "abort_condition": args.abort_condition,
            "expected_artifact": expected_artifact,
        }.items()
        if value
    }
    experiment_details = [
        detail
        for detail in [
            f"Changed variable: {args.changed_variable}",
            f"Hypothesis: {args.hypothesis}",
            f"Success criterion: {args.success_criterion}",
            f"Abort condition: {args.abort_condition}",
            f"Expected artifact: {expected_artifact}",
        ]
        if not detail.endswith(": ")
    ]
    command = [
        *resolve_headless_display_prefix(),
        *build_monocular_tum_vi_command(resolved),
    ]

    if args.prepare_only:
        write_prepare_only_log(
            command=command,
            manifest_notes=manifest.notes,
            prepared_frame_count=prepared.frame_count,
            run_workdir=run_workdir,
            resolved=resolved,
            trajectory_outputs=trajectory_outputs,
        )
        resolved.report.parent.mkdir(parents=True, exist_ok=True)
        resolved.report.write_text(
            render_report(
                command=command,
                execution_mode="prepare-only",
                exit_code=None,
                manifest_notes=manifest.notes,
                prepared_frame_count=prepared.frame_count,
                report_path=resolved.report,
                result_details=[
                    f"Execution is deferred; run from {relative_to_repo(run_workdir)}.",
                    "Trajectory outputs are only written during execute mode.",
                    f"Frame stride: {args.frame_stride}",
                    f"Max frames: {args.max_frames if args.max_frames is not None else 'full sequence'}",
                    "Aggressive ORB overrides: "
                    f"nFeatures={calibration.orb.n_features}, "
                    f"iniThFAST={calibration.orb.ini_fast}, "
                    f"minThFAST={calibration.orb.min_fast}",
                    "Save skip toggles: "
                    f"frame={args.skip_frame_trajectory_save}, "
                    f"keyframe={args.skip_keyframe_trajectory_save}",
                    *experiment_details,
                ],
                run_workdir=run_workdir,
                resolved=resolved,
                trajectory_outputs=trajectory_outputs,
            ),
            encoding="utf-8",
        )

        print(f"Prepared settings: {relative_to_repo(resolved.settings)}")
        print(f"Prepared dataset: {relative_to_repo(resolved.image_dir)}")
        print(f"Prepared timestamps: {relative_to_repo(resolved.timestamps)}")
        print(f"Planned command: {shlex.join(command)}")
        return 0

    missing = [
        path
        for path in (resolved.executable, resolved.vocabulary)
        if not path.exists()
    ]
    if missing:
        missing_text = ", ".join(relative_to_repo(path) for path in missing)
        raise SystemExit(
            "Missing ORB-SLAM3 baseline assets: "
            f"{missing_text}. Run ./scripts/fetch_orbslam3_baseline.sh and "
            "./scripts/build_orbslam3_baseline.sh first."
        )

    resolved.log.parent.mkdir(parents=True, exist_ok=True)
    for trajectory_path in (
        trajectory_outputs.frame_trajectory,
        trajectory_outputs.keyframe_trajectory,
    ):
        if trajectory_path.exists():
            trajectory_path.unlink()
    with resolved.log.open("w", encoding="utf-8") as log_handle:
        log_handle.write(f"Working directory: {relative_to_repo(run_workdir)}\n")
        log_handle.write(f"Command: {shlex.join(command)}\n")
        log_handle.write(f"Calibration: {relative_to_repo(resolved.calibration)}\n")
        log_handle.write(f"Frame index: {relative_to_repo(resolved.frame_index)}\n\n")
        log_handle.write(f"Frame stride: {args.frame_stride}\n")
        log_handle.write(
            "Max frames: "
            f"{args.max_frames if args.max_frames is not None else 'full sequence'}\n"
        )
        log_handle.write(
            "Aggressive ORB overrides: "
            f"nFeatures={calibration.orb.n_features}, "
            f"iniThFAST={calibration.orb.ini_fast}, "
            f"minThFAST={calibration.orb.min_fast}\n"
        )
        log_handle.write(
            "Save skip toggles: "
            f"frame={args.skip_frame_trajectory_save}, "
            f"keyframe={args.skip_keyframe_trajectory_save}\n\n"
        )
        if experiment_details:
            log_handle.write("\n".join(experiment_details) + "\n\n")
        run_env = build_runtime_environment()
        if args.max_frames is not None:
            run_env["ORB_SLAM3_HEL68_MAX_FRAMES"] = str(args.max_frames)
        if args.skip_frame_trajectory_save:
            run_env["ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE"] = "1"
        if args.skip_keyframe_trajectory_save:
            run_env["ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE"] = "1"
        progress_issue = args.progress_issue or "monocular-baseline"
        current_step = "launching mono_tum_vi"
        completed_frames = 0
        if progress_artifact:
            write_progress_artifact(
                progress_artifact,
                render_runtime_progress(
                    artifacts=progress_artifacts,
                    issue=progress_issue,
                    status="in_progress",
                    current_step=current_step,
                    completed=completed_frames,
                    total=progress_total,
                    metrics={
                        "frame_stride": args.frame_stride,
                        "max_frames": args.max_frames,
                        "skip_frame_trajectory_save": args.skip_frame_trajectory_save,
                        "skip_keyframe_trajectory_save": args.skip_keyframe_trajectory_save,
                        "command": shlex.join(command),
                    },
                    experiment=experiment,
                ),
            )
        process = subprocess.Popen(
            command,
            cwd=run_workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=run_env,
            text=True,
        )
        assert process.stdout is not None
        for line in process.stdout:
            log_handle.write(line)
            log_handle.flush()
            stripped = line.strip()
            if match := FRAME_START_PATTERN.search(stripped):
                current_step = f"frame {match.group(1)} TrackMonocular start"
            if match := FRAME_COMPLETED_PATTERN.search(stripped):
                completed_frames = max(completed_frames, int(match.group(1)) + 1)
                current_step = f"completed frame {completed_frames}"
            elif "HEL-68 diagnostic: stopping after " in stripped:
                current_step = stripped
            elif "HEL-63 diagnostic: entering SLAM shutdown" in stripped:
                current_step = "entering SLAM shutdown"
            elif "HEL-63 diagnostic: SLAM shutdown completed" in stripped:
                current_step = "SLAM shutdown completed"
            if progress_artifact:
                write_progress_artifact(
                    progress_artifact,
                    render_runtime_progress(
                        artifacts=progress_artifacts,
                        issue=progress_issue,
                        status="in_progress",
                        current_step=current_step,
                        completed=completed_frames,
                        total=progress_total,
                        metrics={
                            "frame_stride": args.frame_stride,
                            "max_frames": args.max_frames,
                            "skip_frame_trajectory_save": args.skip_frame_trajectory_save,
                            "skip_keyframe_trajectory_save": args.skip_keyframe_trajectory_save,
                            "command": shlex.join(command),
                        },
                        experiment=experiment,
                    ),
                )
        result = process.wait()

    final_exit_code = result
    result_details = [
        f"Raw process exit code: {result}",
        f"Frame stride: {args.frame_stride}",
        f"Max frames: {args.max_frames if args.max_frames is not None else 'full sequence'}",
        "Aggressive ORB overrides: "
        f"nFeatures={calibration.orb.n_features}, "
        f"iniThFAST={calibration.orb.ini_fast}, "
        f"minThFAST={calibration.orb.min_fast}",
        "Save skip toggles: "
        f"frame={args.skip_frame_trajectory_save}, "
        f"keyframe={args.skip_keyframe_trajectory_save}",
        *experiment_details,
    ]
    trajectory_result_details, missing_or_empty_outputs = inspect_trajectory_outputs(
        trajectory_outputs,
        skip_frame_trajectory_save=args.skip_frame_trajectory_save,
        skip_keyframe_trajectory_save=args.skip_keyframe_trajectory_save,
        path_renderer=relative_to_repo,
    )
    result_details.extend(trajectory_result_details)
    runtime_log_summary = summarize_runtime_log(resolved.log)
    result_details.extend(render_runtime_log_details(runtime_log_summary))

    if (
        runtime_log_summary.frame_trajectory_save_completed
        and trajectory_outputs.frame_trajectory in missing_or_empty_outputs
    ):
        result_details.append(
            "Frame trajectory save completed in the log, but the expected frame "
            "trajectory file is still missing at "
            f"{relative_to_repo(trajectory_outputs.frame_trajectory)}."
        )
    if (
        runtime_log_summary.keyframe_trajectory_skipped
        and trajectory_outputs.keyframe_trajectory in missing_or_empty_outputs
    ):
        missing_or_empty_outputs = [
            path
            for path in missing_or_empty_outputs
            if path != trajectory_outputs.keyframe_trajectory
        ]
    elif (
        runtime_log_summary.keyframe_trajectory_save_completed
        and trajectory_outputs.keyframe_trajectory in missing_or_empty_outputs
    ):
        result_details.append(
            "Keyframe trajectory save completed in the log, but the expected keyframe "
            "trajectory file is still missing at "
            f"{relative_to_repo(trajectory_outputs.keyframe_trajectory)}."
        )

    if result == 0 and missing_or_empty_outputs:
        final_exit_code = 2
        missing_paths = ", ".join(
            relative_to_repo(path) for path in missing_or_empty_outputs
        )
        summary = (
            "ORB-SLAM3 exited without writing non-empty trajectory artifacts: "
            f"{missing_paths}. This indicates the run never produced a savable track."
        )
        result_details.append(summary)
        with resolved.log.open("a", encoding="utf-8") as log_handle:
            log_handle.write(f"\n{summary}\n")
    if progress_artifact:
        write_progress_artifact(
            progress_artifact,
            render_runtime_progress(
                artifacts=progress_artifacts,
                issue=args.progress_issue or "monocular-baseline",
                status="completed" if final_exit_code == 0 else "failed",
                current_step=(
                    "mono_tum_vi completed"
                    if final_exit_code == 0
                    else f"mono_tum_vi failed with exit code {final_exit_code}"
                ),
                completed=progress_total if final_exit_code == 0 else completed_frames,
                total=progress_total,
                metrics={
                    "exit_code": final_exit_code,
                    "frame_stride": args.frame_stride,
                    "max_frames": args.max_frames,
                    "skip_frame_trajectory_save": args.skip_frame_trajectory_save,
                    "skip_keyframe_trajectory_save": args.skip_keyframe_trajectory_save,
                    "command": shlex.join(command),
                },
                experiment=experiment,
            ),
        )

    resolved.report.parent.mkdir(parents=True, exist_ok=True)
    resolved.report.write_text(
        render_report(
            command=command,
            execution_mode="execute",
            exit_code=final_exit_code,
            manifest_notes=manifest.notes,
            prepared_frame_count=prepared.frame_count,
            report_path=resolved.report,
            result_details=result_details,
            run_workdir=run_workdir,
            resolved=resolved,
            trajectory_outputs=trajectory_outputs,
        ),
        encoding="utf-8",
    )

    print(f"Wrote log: {relative_to_repo(resolved.log)}")
    print(f"Wrote report: {relative_to_repo(resolved.report)}")
    return final_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
