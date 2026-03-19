#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.rgbd_tum_publish import publish_rgbd_tum_bundle  # noqa: E402


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        default="reports/out/tum_rgbd_fr1_xyz_summary.json",
    )
    parser.add_argument(
        "--publish-dir",
        default="reports/published/tum_rgbd_fr1_xyz_sanity",
    )
    args = parser.parse_args()

    manifest = publish_rgbd_tum_bundle(
        publish_dir=resolve_repo_path(args.publish_dir),
        repo_root=REPO_ROOT,
        summary_path=resolve_repo_path(args.summary),
    )
    print(f"Published entrypoint: {manifest['published_entrypoint']}")
    print(f"Published visual report: {manifest['published_visual_report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
