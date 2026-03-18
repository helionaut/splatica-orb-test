#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.calibration_translation import (  # noqa: E402
    load_calibration_config_smoke_manifest,
    run_calibration_config_smoke,
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

    manifest = load_calibration_config_smoke_manifest(resolve_repo_path(args.manifest))
    run = run_calibration_config_smoke(REPO_ROOT, manifest)

    print(f"Wrote log: {run.log_path.relative_to(REPO_ROOT)}")
    print(f"Wrote report: {run.report_path.relative_to(REPO_ROOT)}")
    for output in run.outputs:
        print(
            "Validated settings: "
            f"{output.output_path.relative_to(REPO_ROOT)} "
            f"(lens={output.lens_id}, fps={output.fps}, color_order={output.color_order})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
