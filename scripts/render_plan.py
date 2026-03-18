#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.harness import load_smoke_manifest, render_build_plan, validate_layout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    missing = validate_layout(REPO_ROOT)
    if missing:
        raise SystemExit(f"Missing required repository paths: {', '.join(missing)}")

    manifest = load_smoke_manifest(REPO_ROOT / args.manifest)
    output_path = REPO_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_build_plan(manifest), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
