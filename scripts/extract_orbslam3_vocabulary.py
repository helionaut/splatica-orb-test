#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.orbslam3_baseline_assets import (  # noqa: E402
    ensure_orbslam3_vocabulary_text,
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
    parser.add_argument(
        "--checkout-dir",
        default="third_party/orbslam3/upstream",
    )
    args = parser.parse_args()

    vocabulary_path = ensure_orbslam3_vocabulary_text(
        resolve_repo_path(args.checkout_dir)
    )
    print(f"Prepared vocabulary: {relative_to_repo(vocabulary_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
