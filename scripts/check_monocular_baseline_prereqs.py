#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.monocular_prereqs import (  # noqa: E402
    inspect_monocular_baseline_prerequisites,
    render_monocular_baseline_prerequisite_report,
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
    parser.add_argument("--report")
    args = parser.parse_args()

    manifest_path = resolve_repo_path(args.manifest)
    prerequisites = inspect_monocular_baseline_prerequisites(REPO_ROOT, manifest_path)
    report_text = render_monocular_baseline_prerequisite_report(prerequisites)

    if args.report:
        report_path = resolve_repo_path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")
        print(f"Wrote report: {relative_to_repo(report_path)}")
    else:
        print(report_text)

    print(
        f"Ready for --prepare-only: {str(prerequisites.ready_for_prepare_only).lower()}"
    )
    print(f"Ready for full execution: {str(prerequisites.ready_for_execute).lower()}")
    return 0 if prerequisites.ready_for_execute else 1


if __name__ == "__main__":
    raise SystemExit(main())
