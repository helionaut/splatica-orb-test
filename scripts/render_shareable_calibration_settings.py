#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.calibration_translation import (  # noqa: E402
    load_shareable_rig_calibration,
    render_shareable_monocular_settings_yaml,
)


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--lens", required=True)
    parser.add_argument("--fps", required=True, type=float)
    parser.add_argument("--color-order", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    calibration_path = resolve_repo_path(args.calibration)
    output_path = resolve_repo_path(args.output)
    calibration = load_shareable_rig_calibration(calibration_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_shareable_monocular_settings_yaml(
            calibration,
            color_order=args.color_order,
            fps=args.fps,
            lens_id=args.lens,
            source_label=str(calibration_path.relative_to(REPO_ROOT)),
        ),
        encoding="utf-8",
    )

    print(f"Wrote settings: {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
