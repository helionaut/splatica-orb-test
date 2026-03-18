#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.stereo_imu_normalization import (  # noqa: E402
    load_stereo_imu_normalization_manifest,
    normalize_stereo_imu_sequence,
    render_stereo_imu_normalization_report,
    resolve_stereo_imu_normalization_paths,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest = load_stereo_imu_normalization_manifest(resolve_repo_path(args.manifest))
    resolved = resolve_stereo_imu_normalization_paths(REPO_ROOT, manifest)
    summary = normalize_stereo_imu_sequence(
        resolved.raw_root,
        resolved.normalized_root,
    )

    resolved.report.parent.mkdir(parents=True, exist_ok=True)
    resolved.report.write_text(
        render_stereo_imu_normalization_report(
            notes=manifest.notes,
            raw_root=relative_to_repo(resolved.raw_root),
            report_path=relative_to_repo(resolved.report),
            summary=summary,
            normalized_root=relative_to_repo(resolved.normalized_root),
        ),
        encoding="utf-8",
    )

    print(f"Normalized sequence: {summary.sequence_id}")
    print(f"Stereo pairs: {summary.stereo_pair_count}")
    print(f"IMU samples: {summary.imu_sample_count}")
    print(f"First stereo timestamp: {summary.first_timestamp_ns}")
    print(f"Last stereo timestamp: {summary.last_timestamp_ns}")
    print(f"Normalized root: {relative_to_repo(summary.normalized_root)}")
    print(f"Stereo timestamps: {relative_to_repo(summary.timestamps_path)}")
    print(f"IMU samples: {relative_to_repo(summary.imu_path)}")
    print(f"Report: {relative_to_repo(resolved.report)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
