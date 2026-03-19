#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.monocular_baseline import (  # noqa: E402
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()

    manifest = load_monocular_baseline_manifest(resolve_repo_path(args.manifest))
    resolved = resolve_monocular_baseline_paths(REPO_ROOT, manifest)

    calibration = load_monocular_calibration(resolved.calibration)
    resolved.settings.parent.mkdir(parents=True, exist_ok=True)
    resolved.settings.write_text(
        render_monocular_settings_yaml(calibration),
        encoding="utf-8",
    )

    prepared = prepare_monocular_sequence(
        resolved.frame_index,
        resolved.image_dir,
        resolved.timestamps,
    )
    run_workdir = resolved.trajectory_stem.parent
    run_workdir.mkdir(parents=True, exist_ok=True)
    trajectory_outputs = resolve_monocular_trajectory_outputs(resolved)
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
        result = subprocess.run(
            command,
            check=False,
            cwd=run_workdir,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=build_runtime_environment(),
            text=True,
        )

    final_exit_code = result.returncode
    result_details = [f"Raw process exit code: {result.returncode}"]
    missing_or_empty_outputs: list[Path] = []
    for label, trajectory_path in (
        ("Frame trajectory", trajectory_outputs.frame_trajectory),
        ("Keyframe trajectory", trajectory_outputs.keyframe_trajectory),
    ):
        if not trajectory_path.exists():
            result_details.append(
                f"{label}: missing at {relative_to_repo(trajectory_path)}"
            )
            missing_or_empty_outputs.append(trajectory_path)
            continue

        size_bytes = trajectory_path.stat().st_size
        result_details.append(
            f"{label}: {relative_to_repo(trajectory_path)} ({size_bytes} bytes)"
        )
        if size_bytes == 0:
            missing_or_empty_outputs.append(trajectory_path)

    if result.returncode == 0 and missing_or_empty_outputs:
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
