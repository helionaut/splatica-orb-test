#!/usr/bin/env python3

from __future__ import annotations

import argparse
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
    resolve_monocular_baseline_paths,
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
    resolved,
) -> str:
    command_text = shlex.join(command)
    exit_line = "not executed" if exit_code is None else str(exit_code)

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
- Log path: `{relative_to_repo(resolved.log)}`
- Report path: `{relative_to_repo(report_path)}`

## Planned command

`{command_text}`

## Notes

{manifest_notes}
"""


def write_prepare_only_log(
    *,
    command: list[str],
    manifest_notes: str,
    prepared_frame_count: int,
    resolved,
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
                f"Command: {shlex.join(command)}",
                f"Notes: {manifest_notes}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


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
    resolved.trajectory_stem.parent.mkdir(parents=True, exist_ok=True)
    command = build_monocular_tum_vi_command(resolved)

    if args.prepare_only:
        write_prepare_only_log(
            command=command,
            manifest_notes=manifest.notes,
            prepared_frame_count=prepared.frame_count,
            resolved=resolved,
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
                resolved=resolved,
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
    with resolved.log.open("w", encoding="utf-8") as log_handle:
        log_handle.write(f"Command: {shlex.join(command)}\n")
        log_handle.write(f"Calibration: {relative_to_repo(resolved.calibration)}\n")
        log_handle.write(f"Frame index: {relative_to_repo(resolved.frame_index)}\n\n")
        result = subprocess.run(
            command,
            check=False,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )

    resolved.report.parent.mkdir(parents=True, exist_ok=True)
    resolved.report.write_text(
        render_report(
            command=command,
            execution_mode="execute",
            exit_code=result.returncode,
            manifest_notes=manifest.notes,
            prepared_frame_count=prepared.frame_count,
            report_path=resolved.report,
            resolved=resolved,
        ),
        encoding="utf-8",
    )

    print(f"Wrote log: {relative_to_repo(resolved.log)}")
    print(f"Wrote report: {relative_to_repo(resolved.report)}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
