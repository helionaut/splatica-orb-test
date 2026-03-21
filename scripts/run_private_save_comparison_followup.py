#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROGRESS_ARTIFACT = REPO_ROOT / ".symphony/progress/HEL-76.json"
DEFAULT_DELEGATE_PROGRESS_ARTIFACT = REPO_ROOT / ".symphony/progress/HEL-76-private-run.json"
DEFAULT_ORCHESTRATION_LOG = REPO_ROOT / "logs/out/hel-76_private_save_comparison_followup.log"
DEFAULT_STATUS_REPORT = REPO_ROOT / "reports/out/hel-76_private_save_comparison_followup.md"
DEFAULT_DELEGATE_STATUS_REPORT = REPO_ROOT / "reports/out/hel-76_private_monocular_followup.md"
DEFAULT_OUTPUT_TAG = "orb_aggressive_asan_no_static_alignment_hel76_save_compare"
DEFAULT_PUBLIC_REFERENCE_REPORT = REPO_ROOT / "docs/hel-75-public-save-path-follow-up.md"
DEFAULT_OPENCLAW_DOWNLOADS_ROOT = Path("/home/helionaut/.openclaw/workspace/downloads")

STATUS_PATTERN = re.compile(r"- Status: `([^`]+)`")
MISSING_SOURCE_PATTERN = re.compile(r"- (Source [^:]+): \*\*missing\*\* \(`([^`]+)`\)")
DELEGATE_REPORT_PATTERN = re.compile(r"- Delegate monocular report: `([^`]+)`")
DELEGATE_LOG_PATTERN = re.compile(r"- Orchestration log: `([^`]+)`")
SAVE_CWD_PATTERN = re.compile(r"- Trajectory save cwd reported: (.+)")
FRAME_POST_CLOSE_PATTERN = re.compile(
    r"- Frame trajectory post-close visibility: open=(True|False), bytes=(-?\d+)"
)
KEYFRAME_POST_CLOSE_PATTERN = re.compile(
    r"- Keyframe trajectory post-close visibility: open=(True|False), bytes=(-?\d+)"
)


@dataclass(frozen=True)
class PublicSaveReference:
    issue_identifier: str
    report_path: Path
    save_cwd: str
    frame_bytes: int
    keyframe_bytes: int


@dataclass(frozen=True)
class PrivateRunEvidence:
    status: str
    missing_sources: tuple[str, ...]
    save_cwd: str | None
    frame_post_close_open: bool | None
    frame_post_close_bytes: int | None
    keyframe_post_close_open: bool | None
    keyframe_post_close_bytes: int | None
    delegate_report_path: Path | None
    delegate_log_path: Path | None


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


def write_progress_artifact(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_progress_payload(
    *,
    status: str,
    current_step: str,
    completed: int,
    total: int,
    artifacts: dict[str, str],
    metrics: dict[str, object],
    experiment: dict[str, object],
) -> dict[str, object]:
    clamped_completed = max(0, min(completed, total))
    progress_percent = round((clamped_completed / total) * 100) if total else 100
    return {
        "status": status,
        "current_step": current_step,
        "completed": clamped_completed,
        "total": total,
        "unit": "phases",
        "progress_percent": progress_percent,
        "metrics": metrics,
        "artifacts": artifacts,
        "experiment": experiment,
    }


def discover_openclaw_video_inputs(downloads_root: Path) -> tuple[Path | None, Path | None]:
    if not downloads_root.exists():
        return None, None

    candidate_pairs: list[tuple[Path, Path]] = []
    for video_00 in sorted(downloads_root.glob("insta360-*/00.mp4")):
        video_10 = video_00.with_name("10.mp4")
        if video_10.exists():
            candidate_pairs.append((video_00, video_10))

    if not candidate_pairs:
        return None, None

    return candidate_pairs[-1]


def load_public_reference(report_path: Path) -> PublicSaveReference:
    if not report_path.exists():
        raise SystemExit(
            f"Missing HEL-75 public reference report at {relative_to_repo(report_path)}."
        )

    return PublicSaveReference(
        issue_identifier="HEL-75",
        report_path=report_path,
        save_cwd="build/tum_vi_room1_512_16/monocular/trajectory_hel75_save_probe_140",
        frame_bytes=5437,
        keyframe_bytes=924,
    )


def parse_private_run_evidence(status_report_path: Path) -> PrivateRunEvidence:
    if not status_report_path.exists():
        return PrivateRunEvidence(
            status="missing",
            missing_sources=(),
            save_cwd=None,
            frame_post_close_open=None,
            frame_post_close_bytes=None,
            keyframe_post_close_open=None,
            keyframe_post_close_bytes=None,
            delegate_report_path=None,
            delegate_log_path=None,
        )

    text = status_report_path.read_text(encoding="utf-8")
    status_match = STATUS_PATTERN.search(text)
    status = status_match.group(1) if status_match else "unknown"
    missing_sources = tuple(
        match.group(1) for match in MISSING_SOURCE_PATTERN.finditer(text)
    )

    delegate_report_match = DELEGATE_REPORT_PATTERN.search(text)
    delegate_log_match = DELEGATE_LOG_PATTERN.search(text)
    delegate_report_path = (
        resolve_repo_path(delegate_report_match.group(1))
        if delegate_report_match
        else None
    )
    delegate_log_path = (
        resolve_repo_path(delegate_log_match.group(1))
        if delegate_log_match
        else None
    )

    delegate_text = (
        delegate_report_path.read_text(encoding="utf-8")
        if delegate_report_path is not None and delegate_report_path.exists()
        else ""
    )
    save_cwd_match = SAVE_CWD_PATTERN.search(delegate_text)
    frame_match = FRAME_POST_CLOSE_PATTERN.search(delegate_text)
    keyframe_match = KEYFRAME_POST_CLOSE_PATTERN.search(delegate_text)
    return PrivateRunEvidence(
        status=status,
        missing_sources=missing_sources,
        save_cwd=save_cwd_match.group(1) if save_cwd_match else None,
        frame_post_close_open=(
            frame_match.group(1) == "True" if frame_match else None
        ),
        frame_post_close_bytes=int(frame_match.group(2)) if frame_match else None,
        keyframe_post_close_open=(
            keyframe_match.group(1) == "True" if keyframe_match else None
        ),
        keyframe_post_close_bytes=(
            int(keyframe_match.group(2)) if keyframe_match else None
        ),
        delegate_report_path=delegate_report_path,
        delegate_log_path=delegate_log_path,
    )


def render_comparison_lines(
    *,
    public_reference: PublicSaveReference,
    private_evidence: PrivateRunEvidence,
) -> list[str]:
    lines = [
        (
            "Public reference: "
            f"{public_reference.issue_identifier} save cwd `{public_reference.save_cwd}`, "
            f"frame bytes `{public_reference.frame_bytes}`, "
            f"keyframe bytes `{public_reference.keyframe_bytes}`."
        )
    ]
    if private_evidence.save_cwd is not None:
        lines.append(f"Private save cwd observed: `{private_evidence.save_cwd}`.")
    else:
        lines.append("Private save cwd observed: unavailable in the current host evidence.")

    if private_evidence.frame_post_close_bytes is not None:
        lines.append(
            "Private frame post-close bytes: "
            f"`{private_evidence.frame_post_close_bytes}` "
            f"(open={private_evidence.frame_post_close_open})."
        )
    else:
        lines.append("Private frame post-close bytes: unavailable.")

    if private_evidence.keyframe_post_close_bytes is not None:
        lines.append(
            "Private keyframe post-close bytes: "
            f"`{private_evidence.keyframe_post_close_bytes}` "
            f"(open={private_evidence.keyframe_post_close_open})."
        )
    else:
        lines.append("Private keyframe post-close bytes: unavailable.")

    if private_evidence.missing_sources:
        lines.append(
            "Current blocker: the private rerun is still blocked before save comparison "
            "because these source inputs are missing: "
            + ", ".join(f"`{label}`" for label in private_evidence.missing_sources)
            + "."
        )
    elif private_evidence.frame_post_close_bytes is None:
        lines.append(
            "Current blocker: the rerun produced no post-close frame-byte evidence yet, "
            "so the remaining boundary is still before a full HEL-75-style save comparison."
        )
    else:
        lines.append(
            "Current comparison: the private lane reached save diagnostics and can now be "
            "judged directly against the HEL-75 byte counts before any manifest promotion."
        )
    return lines


def render_status_report(
    *,
    command: str,
    delegate_exit_code: int,
    downloads_root: Path,
    public_reference: PublicSaveReference,
    private_evidence: PrivateRunEvidence,
    discovered_video_00: Path | None,
    discovered_video_10: Path | None,
    orchestration_log: Path,
    status_report: Path,
    delegate_status_report: Path,
) -> str:
    result_status = "blocked" if delegate_exit_code != 0 else "completed"
    discovered_videos = [
        (
            f"- Raw video 00: `{discovered_video_00}`"
            if discovered_video_00 is not None
            else "- Raw video 00: not found"
        ),
        (
            f"- Raw video 10: `{discovered_video_10}`"
            if discovered_video_10 is not None
            else "- Raw video 10: not found"
        ),
    ]
    delegate_report_line = (
        f"`{relative_to_repo(private_evidence.delegate_report_path)}`"
        if private_evidence.delegate_report_path is not None
        else "`unavailable`"
    )
    delegate_log_line = (
        f"`{relative_to_repo(private_evidence.delegate_log_path)}`"
        if private_evidence.delegate_log_path is not None
        else "`unavailable`"
    )
    comparison_lines = "\n".join(
        f"- {line}" for line in render_comparison_lines(
            public_reference=public_reference,
            private_evidence=private_evidence,
        )
    )
    missing_lines = (
        "\n".join(f"- `{label}`" for label in private_evidence.missing_sources)
        if private_evidence.missing_sources
        else "- none"
    )
    return f"""# HEL-76 Private Save Comparison Follow-up

Issue: HEL-76

## Result

- Status: `{result_status}`
- Delegate exit code: `{delegate_exit_code}`
- Orchestration log: `{relative_to_repo(orchestration_log)}`
- Status report: `{relative_to_repo(status_report)}`
- Delegate status report: `{relative_to_repo(delegate_status_report)}`
- Delegate monocular report: {delegate_report_line}
- Delegate orchestration log: {delegate_log_line}

## Experiment Contract

- Changed variable: keep the HEL-74 aggressive private lane as the runtime baseline, but compare its save cwd and post-close byte counts directly against the HEL-75 public save proof before promoting any tuned settings
- Hypothesis: the HEL-75 diagnostics will show whether the private lane is still blocked before save, reaches save without reopening a file, or writes measurable bytes that can be compared against the public probe
- Success criterion: the current host evidence leaves either a successful private save comparison or a narrower blocker than the generic HEL-74 shutdown/save boundary
- Abort condition: required private sidecars are still missing, the delegated rerun fails before save diagnostics, or the comparison report cannot recover the relevant byte counts

## Public Reference

- Reference issue: `{public_reference.issue_identifier}`
- Reference report: `{relative_to_repo(public_reference.report_path)}`
- Reference save cwd: `{public_reference.save_cwd}`
- Reference frame post-close bytes: `{public_reference.frame_bytes}`
- Reference keyframe post-close bytes: `{public_reference.keyframe_bytes}`

## Host Input Discovery

- Downloads root: `{downloads_root}`
{chr(10).join(discovered_videos)}

## Missing Source Inputs

{missing_lines}

## Comparison

{comparison_lines}

## Command

`{command}`
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="manifests/insta360_x3_lens10_monocular_baseline.json",
    )
    parser.add_argument("--progress-issue", default="HEL-76")
    parser.add_argument("--progress-artifact", default=str(DEFAULT_PROGRESS_ARTIFACT))
    parser.add_argument(
        "--delegate-progress-artifact",
        default=str(DEFAULT_DELEGATE_PROGRESS_ARTIFACT),
    )
    parser.add_argument("--orchestration-log", default=str(DEFAULT_ORCHESTRATION_LOG))
    parser.add_argument("--status-report", default=str(DEFAULT_STATUS_REPORT))
    parser.add_argument(
        "--delegate-status-report",
        default=str(DEFAULT_DELEGATE_STATUS_REPORT),
    )
    parser.add_argument("--output-tag", default=DEFAULT_OUTPUT_TAG)
    parser.add_argument(
        "--public-reference-report",
        default=str(DEFAULT_PUBLIC_REFERENCE_REPORT),
    )
    parser.add_argument(
        "--video-downloads-root",
        default=str(DEFAULT_OPENCLAW_DOWNLOADS_ROOT),
    )
    parser.add_argument("--video-00")
    parser.add_argument("--video-10")
    parser.add_argument("--calibration-00")
    parser.add_argument("--calibration-10")
    parser.add_argument("--extrinsics")
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--max-frames", type=int)
    args = parser.parse_args()

    progress_artifact = resolve_repo_path(args.progress_artifact)
    delegate_progress_artifact = resolve_repo_path(args.delegate_progress_artifact)
    orchestration_log = resolve_repo_path(args.orchestration_log)
    status_report = resolve_repo_path(args.status_report)
    delegate_status_report = resolve_repo_path(args.delegate_status_report)
    public_reference = load_public_reference(resolve_repo_path(args.public_reference_report))
    downloads_root = Path(args.video_downloads_root)

    discovered_video_00, discovered_video_10 = discover_openclaw_video_inputs(downloads_root)
    video_00 = resolve_repo_path(args.video_00) if args.video_00 else discovered_video_00
    video_10 = resolve_repo_path(args.video_10) if args.video_10 else discovered_video_10

    experiment = {
        "changed_variable": (
            "keep the HEL-74 aggressive private lane, but require an explicit "
            "comparison against the HEL-75 public save-path byte counts"
        ),
        "hypothesis": (
            "the current host evidence will either reproduce private save-byte "
            "counts or narrow the blocker to the exact inputs still missing before rerun"
        ),
        "success_criterion": (
            "the HEL-76 report records both the HEL-75 public reference numbers and "
            "the current private-lane save evidence or prerequisite blocker"
        ),
        "abort_condition": (
            "the delegated private rerun leaves no auditable report or the current host "
            "still lacks the sidecars needed to start the comparison"
        ),
        "expected_artifact": relative_to_repo(status_report),
    }
    artifacts = {
        "manifest": args.manifest,
        "runner": "scripts/run_private_save_comparison_followup.py",
        "delegate_runner": "scripts/run_private_monocular_followup.py",
        "status_report": relative_to_repo(status_report),
        "orchestration_log": relative_to_repo(orchestration_log),
        "delegate_status_report": relative_to_repo(delegate_status_report),
        "delegate_progress_artifact": relative_to_repo(delegate_progress_artifact),
        "public_reference_report": relative_to_repo(public_reference.report_path),
    }

    orchestration_log.parent.mkdir(parents=True, exist_ok=True)
    status_report.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/run_private_monocular_followup.py"),
        "--manifest",
        args.manifest,
        "--progress-issue",
        args.progress_issue,
        "--progress-artifact",
        str(delegate_progress_artifact),
        "--orchestration-log",
        str(orchestration_log.with_name("hel-76_private_monocular_followup.log")),
        "--status-report",
        str(delegate_status_report),
        "--output-tag",
        args.output_tag,
        "--frame-stride",
        str(args.frame_stride),
    ]
    if args.max_frames is not None:
        command.extend(["--max-frames", str(args.max_frames)])
    if video_00 is not None:
        command.extend(["--video-00", str(video_00)])
    if video_10 is not None:
        command.extend(["--video-10", str(video_10)])
    if args.calibration_00:
        command.extend(["--calibration-00", args.calibration_00])
    if args.calibration_10:
        command.extend(["--calibration-10", args.calibration_10])
    if args.extrinsics:
        command.extend(["--extrinsics", args.extrinsics])

    write_progress_artifact(
        progress_artifact,
        build_progress_payload(
            status="in_progress",
            current_step="running HEL-74 private baseline under the HEL-76 comparison wrapper",
            completed=0,
            total=2,
            artifacts=artifacts,
            metrics={
                "delegate_command": subprocess.list2cmdline(command),
                "reference_frame_bytes": public_reference.frame_bytes,
                "reference_keyframe_bytes": public_reference.keyframe_bytes,
            },
            experiment=experiment,
        ),
    )

    with orchestration_log.open("w", encoding="utf-8") as log_handle:
        log_handle.write("Starting HEL-76 private save comparison follow-up.\n")
        log_handle.write(
            f"Delegate command: {subprocess.list2cmdline(command)}\n"
        )
        log_handle.write(
            f"Public reference report: {relative_to_repo(public_reference.report_path)}\n"
        )
        log_handle.write(
            f"Discovered raw video 00: {video_00 if video_00 is not None else 'not found'}\n"
        )
        log_handle.write(
            f"Discovered raw video 10: {video_10 if video_10 is not None else 'not found'}\n\n"
        )
        log_handle.flush()
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            check=False,
            text=True,
        )

    private_evidence = parse_private_run_evidence(delegate_status_report)
    status_report.write_text(
        render_status_report(
            command=subprocess.list2cmdline(command),
            delegate_exit_code=result.returncode,
            downloads_root=downloads_root,
            public_reference=public_reference,
            private_evidence=private_evidence,
            discovered_video_00=video_00,
            discovered_video_10=video_10,
            orchestration_log=orchestration_log,
            status_report=status_report,
            delegate_status_report=delegate_status_report,
        ),
        encoding="utf-8",
    )

    write_progress_artifact(
        progress_artifact,
        build_progress_payload(
            status="completed" if result.returncode == 0 else "blocked",
            current_step=(
                "HEL-76 save comparison completed"
                if result.returncode == 0
                else "HEL-76 save comparison blocked with auditable evidence"
            ),
            completed=2,
            total=2,
            artifacts=artifacts,
            metrics={
                "delegate_exit_code": result.returncode,
                "missing_sources": list(private_evidence.missing_sources),
                "private_save_cwd": private_evidence.save_cwd,
                "private_frame_post_close_bytes": private_evidence.frame_post_close_bytes,
                "private_keyframe_post_close_bytes": private_evidence.keyframe_post_close_bytes,
                "reference_frame_bytes": public_reference.frame_bytes,
                "reference_keyframe_bytes": public_reference.keyframe_bytes,
            },
            experiment=experiment,
        ),
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
