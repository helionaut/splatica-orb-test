#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.monocular_baseline import prepare_monocular_sequence  # noqa: E402


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame-index", required=True)
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--timestamps-path", required=True)
    args = parser.parse_args()

    prepared = prepare_monocular_sequence(
        resolve_repo_path(args.frame_index),
        resolve_repo_path(args.image_dir),
        resolve_repo_path(args.timestamps_path),
    )

    print(f"Prepared frames: {prepared.frame_count}")
    print(f"First timestamp: {prepared.first_timestamp_ns}")
    print(f"Last timestamp: {prepared.last_timestamp_ns}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
