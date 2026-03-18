#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.harness import (
    build_smoke_command,
    load_smoke_manifest,
    render_smoke_log,
    render_smoke_report,
    resolve_manifest_paths,
    validate_layout,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    missing = validate_layout(REPO_ROOT)
    if missing:
        raise SystemExit(f"Missing required repository paths: {', '.join(missing)}")

    manifest_path = REPO_ROOT / args.manifest
    manifest = load_smoke_manifest(manifest_path)
    resolved = resolve_manifest_paths(REPO_ROOT, manifest)

    resolved["log"].parent.mkdir(parents=True, exist_ok=True)
    resolved["report"].parent.mkdir(parents=True, exist_ok=True)

    resolved["log"].write_text(
        render_smoke_log(manifest, build_smoke_command(args.manifest)),
        encoding="utf-8",
    )
    resolved["report"].write_text(
        render_smoke_report(manifest, build_smoke_command(args.manifest)),
        encoding="utf-8",
    )

    print(f"Dry-run log: {resolved['log'].relative_to(REPO_ROOT)}")
    print(f"Dry-run report: {resolved['report'].relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
