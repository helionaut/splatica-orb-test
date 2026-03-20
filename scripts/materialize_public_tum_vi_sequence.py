#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.public_tum_vi import (  # noqa: E402
    load_public_tum_vi_manifest,
    materialize_public_tum_vi_sequence,
    resolve_public_tum_vi_paths,
)


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest = load_public_tum_vi_manifest(resolve_repo_path(args.manifest))
    resolved = resolve_public_tum_vi_paths(REPO_ROOT, manifest)
    materialized = materialize_public_tum_vi_sequence(
        manifest=manifest,
        resolved=resolved,
    )

    print(f"Wrote calibration: {resolved.calibration}")
    print(f"Wrote frame index: {resolved.frame_index}")
    print(
        "Materialized public TUM-VI inputs: "
        f"{materialized.frame_count} frames from {materialized.first_timestamp_ns} "
        f"to {materialized.last_timestamp_ns}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
