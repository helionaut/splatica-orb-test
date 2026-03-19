from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


TEST_FIRST_EXPECTATION = (
    "Behavior changes should begin with a failing test in tests/, or land with "
    "the implementation in the same change when the behavior is brand new."
)
PRODUCTION_VERIFICATION_COMMAND = (
    "make verify-production ARTIFACT_URL=https://<published-artifact-url>"
)


@dataclass(frozen=True)
class RepositoryArea:
    details: str
    path: str


REPOSITORY_LAYOUT = (
    RepositoryArea(
        path="configs/calibration",
        details="Camera intrinsics, extrinsics, and IMU parameters.",
    ),
    RepositoryArea(
        path="configs/orbslam3",
        details="ORB-SLAM3 settings bundles and launch-specific config.",
    ),
    RepositoryArea(
        path="datasets/fixtures",
        details="Small reproducible smoke fixtures safe to share.",
    ),
    RepositoryArea(
        path="datasets/public",
        details="Public datasets that the repo can redownload for clean-room runs.",
    ),
    RepositoryArea(
        path="datasets/user",
        details="Local-only user recordings and larger private inputs.",
    ),
    RepositoryArea(
        path="logs/out",
        details="Generated dry-run or real-run logs.",
    ),
    RepositoryArea(
        path="reports/out",
        details="Generated validation reports and publishable artifacts.",
    ),
    RepositoryArea(
        path="scripts",
        details="Build, smoke-run, and verification entrypoints.",
    ),
    RepositoryArea(
        path="tests",
        details="Automated harness and behavior tests.",
    ),
    RepositoryArea(
        path="third_party/orbslam3",
        details="Pinned ORB-SLAM3 baseline or maintained fork checkout.",
    ),
)


@dataclass(frozen=True)
class SmokeManifest:
    baseline_commit: str
    baseline_name: str
    launch_script: str
    notes: str
    repo_url: str
    sequence_name: str
    dataset_path: str
    settings_path: str
    log_path: str
    report_path: str


def load_smoke_manifest(path: Path) -> SmokeManifest:
    raw = json.loads(path.read_text(encoding="utf-8"))

    try:
        baseline = raw["baseline"]
        sequence = raw["sequence"]
        outputs = raw["outputs"]
        launch = raw["launch"]
        notes = raw["notes"]
    except KeyError as error:
        raise ValueError(f"Missing manifest section: {error.args[0]}") from error

    return SmokeManifest(
        baseline_commit=baseline["commit"],
        baseline_name=baseline["name"],
        launch_script=launch["script"],
        notes=notes,
        repo_url=baseline["repo_url"],
        sequence_name=sequence["name"],
        dataset_path=sequence["dataset_path"],
        settings_path=sequence["settings_path"],
        log_path=outputs["log_path"],
        report_path=outputs["report_path"],
    )


def validate_layout(repo_root: Path) -> list[str]:
    missing = []

    for area in REPOSITORY_LAYOUT:
        if not (repo_root / area.path).exists():
            missing.append(area.path)

    return missing


def build_smoke_command(manifest_path: str) -> str:
    return f"./scripts/run_orbslam3_sequence.sh --manifest {manifest_path} --dry-run"


def resolve_manifest_paths(repo_root: Path, manifest: SmokeManifest) -> dict[str, Path]:
    return {
        "dataset": repo_root / manifest.dataset_path,
        "log": repo_root / manifest.log_path,
        "report": repo_root / manifest.report_path,
        "settings": repo_root / manifest.settings_path,
    }


def render_build_plan(manifest: SmokeManifest) -> str:
    return f"""# HEL-43 smoke plan

## Baseline

- Name: `{manifest.baseline_name}`
- Upstream repo: `{manifest.repo_url}`
- Commit status: `{manifest.baseline_commit}`

## Commands

- Build plan artifact: `make build`
- Smoke dry-run: `make smoke`
- Aggregate validation: `make check`
- Production verification: `{PRODUCTION_VERIFICATION_COMMAND}`

## Inputs and outputs

- Settings bundle: `{manifest.settings_path}`
- Fixture dataset path: `{manifest.dataset_path}`
- Smoke log output: `{manifest.log_path}`
- Smoke report output: `{manifest.report_path}`

## Testing expectation

{TEST_FIRST_EXPECTATION}

## Notes

{manifest.notes}
"""


def render_smoke_log(manifest: SmokeManifest, smoke_command: str) -> str:
    return f"""Dry-run smoke execution for {manifest.sequence_name}
Baseline: {manifest.baseline_name}
Repo: {manifest.repo_url}
Commit: {manifest.baseline_commit}
Command: {smoke_command}
Status: no ORB-SLAM3 process launched; harness-only dry run.
Notes: {manifest.notes}
"""


def render_smoke_report(manifest: SmokeManifest, smoke_command: str) -> str:
    return f"""# Dry-run smoke report: {manifest.sequence_name}

## Result

The HEL-43 harness completed a dry run without attempting a real ORB-SLAM3 launch.

## Planned command

`{smoke_command}`

## Planned inputs

- Settings bundle: `{manifest.settings_path}`
- Fixture dataset path: `{manifest.dataset_path}`

## Planned outputs

- Log file: `{manifest.log_path}`
- Report file: `{manifest.report_path}`

## Next step

Pin the ORB-SLAM3 baseline commit, add a representative smoke fixture, and replace the dry-run placeholder with a real launcher path.
"""
