#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.private_host_inputs import (  # noqa: E402
    DEFAULT_OPENCLAW_DOWNLOADS_ROOT,
    DEFAULT_OPENCLAW_MEDIA_INBOUND_ROOT,
    discover_openclaw_calibration_inputs,
    discover_openclaw_video_inputs,
)
DEFAULT_PROGRESS_ARTIFACT = REPO_ROOT / ".symphony/progress/HEL-77.json"
DEFAULT_DELEGATE_PROGRESS_ARTIFACT = REPO_ROOT / ".symphony/progress/HEL-77-private-run.json"
DEFAULT_ORCHESTRATION_LOG = REPO_ROOT / "logs/out/hel-77_private_save_comparison_followup.log"
DEFAULT_STATUS_REPORT = REPO_ROOT / "reports/out/hel-77_private_save_comparison_followup.md"
DEFAULT_DELEGATE_STATUS_REPORT = REPO_ROOT / "reports/out/hel-77_private_monocular_followup.md"
DEFAULT_OUTPUT_TAG = "orb_aggressive_asan_no_static_alignment_hel77_save_compare"
DEFAULT_PUBLIC_REFERENCE_REPORT = REPO_ROOT / "docs/hel-75-public-save-path-follow-up.md"

STATUS_PATTERN = re.compile(r"- Status: `([^`]+)`")
MISSING_SOURCE_PATTERN = re.compile(r"- (Source [^:]+): \*\*missing\*\* \(`([^`]+)`\)")
DELEGATE_REPORT_PATTERN = re.compile(r"- Delegate monocular report: `([^`]+)`")
DELEGATE_LOG_PATTERN = re.compile(r"- Orchestration log: `([^`]+)`")
SAVE_CWD_PATTERN = re.compile(r"- Trajectory save cwd reported: (.+)")
FRAME_POST_CLOSE_PATTERN = re.compile(
    r"- Frame trajectory post-close visibility: open=(True|False), bytes=(-?\d+)"
)
FRAME_POST_RETURN_PATTERN = re.compile(
    r"- Frame trajectory after-return visibility: open=(True|False), bytes=(-?\d+)"
)
KEYFRAME_POST_CLOSE_PATTERN = re.compile(
    r"- Keyframe trajectory post-close visibility: open=(True|False), bytes=(-?\d+)"
)
KEYFRAME_POST_RETURN_PATTERN = re.compile(
    r"- Keyframe trajectory after-return visibility: open=(True|False), bytes=(-?\d+)"
)
INITIALIZATION_MAPS_PATTERN = re.compile(
    r"- Initialization maps created: (\d+) \(points=([^)]+)\)"
)
ACTIVE_MAP_RESETS_PATTERN = re.compile(r"- Active map resets observed: (\d+)")
RESET_PRE_CLEAR_PATTERN = re.compile(r"- Active map reset pre-clear states: (.+)")
RESET_POST_CLEAR_PATTERN = re.compile(r"- Active map reset post-clear states: (.+)")
FRAME_SAVE_ATLAS_STATE_PATTERN = re.compile(r"- Frame trajectory save atlas state: (.+)")
KEYFRAME_SAVE_ATLAS_STATE_PATTERN = re.compile(
    r"- Keyframe trajectory save atlas state: (.+)"
)
ASAN_SUMMARY_PATTERN = re.compile(r"- AddressSanitizer summary: (.+)")
FRAME_SKIP_PATTERN = re.compile(
    r"- Frame trajectory save skipped because no keyframes were recorded"
)
FRAME_SAVE_MISSING_PATTERN = re.compile(
    r"- Frame trajectory save completed in the log, but the expected frame trajectory file is still missing"
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
    frame_post_return_open: bool | None
    frame_post_return_bytes: int | None
    frame_skipped: bool
    keyframe_post_close_open: bool | None
    keyframe_post_close_bytes: int | None
    keyframe_post_return_open: bool | None
    keyframe_post_return_bytes: int | None
    delegate_report_path: Path | None
    delegate_log_path: Path | None
    initialization_maps: int | None
    initialization_map_points: str | None
    active_map_resets: int | None
    reset_pre_clear_states: str | None
    reset_post_clear_states: str | None
    frame_save_atlas_state: str | None
    keyframe_save_atlas_state: str | None
    asan_summary: str | None
    missing_frame_after_save: bool


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
    unit: str = "phases",
    progress_percent: int | None = None,
) -> dict[str, object]:
    clamped_completed = max(0, min(completed, total))
    resolved_progress_percent = (
        progress_percent
        if progress_percent is not None
        else (round((clamped_completed / total) * 100) if total else 100)
    )
    return {
        "status": status,
        "current_step": current_step,
        "completed": clamped_completed,
        "total": total,
        "unit": unit,
        "progress_percent": resolved_progress_percent,
        "metrics": metrics,
        "artifacts": artifacts,
        "experiment": experiment,
    }


def load_progress_artifact(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def coerce_progress_percent(value: object) -> int | None:
    if isinstance(value, int):
        return max(0, min(value, 99))
    if isinstance(value, float) and value.is_integer():
        return max(0, min(int(value), 99))
    return None


def build_delegate_heartbeat_payload(
    *,
    base_metrics: dict[str, object],
    delegate_progress_artifact: Path,
    delegate_payload: dict[str, object],
    artifacts: dict[str, str],
    experiment: dict[str, object],
) -> dict[str, object]:
    delegate_status = str(delegate_payload.get("status", "in_progress"))
    delegate_current_step = str(delegate_payload.get("current_step", "delegate running"))
    delegate_progress_percent = coerce_progress_percent(
        delegate_payload.get("progress_percent")
    )
    metrics = dict(base_metrics)
    metrics.update(
        {
            "delegate_status": delegate_status,
            "delegate_current_step": delegate_current_step,
            "delegate_progress_artifact": relative_to_repo(delegate_progress_artifact),
        }
    )
    for key in ("completed", "total", "unit"):
        if key in delegate_payload:
            metrics[f"delegate_{key}"] = delegate_payload[key]
    delegate_metrics = delegate_payload.get("metrics")
    if isinstance(delegate_metrics, dict):
        metrics["delegate_metrics"] = delegate_metrics
    return build_progress_payload(
        status="in_progress",
        current_step=f"delegate heartbeat: {delegate_current_step}",
        completed=delegate_progress_percent or 0,
        total=100,
        artifacts=artifacts,
        metrics=metrics,
        experiment=experiment,
        unit="percent",
        progress_percent=delegate_progress_percent or 0,
    )


def format_delegate_heartbeat_line(delegate_payload: dict[str, object]) -> str:
    delegate_status = str(delegate_payload.get("status", "in_progress"))
    delegate_current_step = str(delegate_payload.get("current_step", "delegate running"))
    delegate_progress_percent = delegate_payload.get("progress_percent")
    progress_text = (
        str(delegate_progress_percent)
        if isinstance(delegate_progress_percent, (int, float))
        else "unknown"
    )
    return (
        "[delegate-heartbeat] "
        f"status={delegate_status} progress_percent={progress_text} "
        f"current_step={delegate_current_step}\n"
    )


def build_delegate_env_overrides() -> dict[str, str]:
    # HEL-78 can legitimately restart the same build signature after wrapper-level
    # supervision failures; make that explicit instead of relying on hidden shell state.
    return {"ORB_SLAM3_ALLOW_IDENTICAL_RETRY": "1"}


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
            frame_post_return_open=None,
            frame_post_return_bytes=None,
            frame_skipped=False,
            keyframe_post_close_open=None,
            keyframe_post_close_bytes=None,
            keyframe_post_return_open=None,
            keyframe_post_return_bytes=None,
            delegate_report_path=None,
            delegate_log_path=None,
            initialization_maps=None,
            initialization_map_points=None,
            active_map_resets=None,
            reset_pre_clear_states=None,
            reset_post_clear_states=None,
            frame_save_atlas_state=None,
            keyframe_save_atlas_state=None,
            asan_summary=None,
            missing_frame_after_save=False,
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
    frame_post_return_match = FRAME_POST_RETURN_PATTERN.search(delegate_text)
    keyframe_match = KEYFRAME_POST_CLOSE_PATTERN.search(delegate_text)
    keyframe_post_return_match = KEYFRAME_POST_RETURN_PATTERN.search(delegate_text)
    initialization_maps_match = INITIALIZATION_MAPS_PATTERN.search(delegate_text)
    active_map_resets_match = ACTIVE_MAP_RESETS_PATTERN.search(delegate_text)
    reset_pre_clear_match = RESET_PRE_CLEAR_PATTERN.search(delegate_text)
    reset_post_clear_match = RESET_POST_CLEAR_PATTERN.search(delegate_text)
    frame_save_atlas_state_match = FRAME_SAVE_ATLAS_STATE_PATTERN.search(delegate_text)
    keyframe_save_atlas_state_match = KEYFRAME_SAVE_ATLAS_STATE_PATTERN.search(
        delegate_text
    )
    asan_summary_match = ASAN_SUMMARY_PATTERN.search(delegate_text)
    return PrivateRunEvidence(
        status=status,
        missing_sources=missing_sources,
        save_cwd=save_cwd_match.group(1) if save_cwd_match else None,
        frame_post_close_open=(
            frame_match.group(1) == "True" if frame_match else None
        ),
        frame_post_close_bytes=int(frame_match.group(2)) if frame_match else None,
        frame_post_return_open=(
            frame_post_return_match.group(1) == "True"
            if frame_post_return_match
            else None
        ),
        frame_post_return_bytes=(
            int(frame_post_return_match.group(2))
            if frame_post_return_match
            else None
        ),
        frame_skipped=bool(FRAME_SKIP_PATTERN.search(delegate_text)),
        keyframe_post_close_open=(
            keyframe_match.group(1) == "True" if keyframe_match else None
        ),
        keyframe_post_close_bytes=(
            int(keyframe_match.group(2)) if keyframe_match else None
        ),
        keyframe_post_return_open=(
            keyframe_post_return_match.group(1) == "True"
            if keyframe_post_return_match
            else None
        ),
        keyframe_post_return_bytes=(
            int(keyframe_post_return_match.group(2))
            if keyframe_post_return_match
            else None
        ),
        delegate_report_path=delegate_report_path,
        delegate_log_path=delegate_log_path,
        initialization_maps=(
            int(initialization_maps_match.group(1))
            if initialization_maps_match
            else None
        ),
        initialization_map_points=(
            initialization_maps_match.group(2)
            if initialization_maps_match
            else None
        ),
        active_map_resets=(
            int(active_map_resets_match.group(1))
            if active_map_resets_match
            else None
        ),
        reset_pre_clear_states=(
            reset_pre_clear_match.group(1) if reset_pre_clear_match else None
        ),
        reset_post_clear_states=(
            reset_post_clear_match.group(1) if reset_post_clear_match else None
        ),
        frame_save_atlas_state=(
            frame_save_atlas_state_match.group(1)
            if frame_save_atlas_state_match
            else None
        ),
        keyframe_save_atlas_state=(
            keyframe_save_atlas_state_match.group(1)
            if keyframe_save_atlas_state_match
            else None
        ),
        asan_summary=asan_summary_match.group(1) if asan_summary_match else None,
        missing_frame_after_save=bool(FRAME_SAVE_MISSING_PATTERN.search(delegate_text)),
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
    if private_evidence.frame_post_return_bytes is not None:
        lines.append(
            "Private frame after-return bytes: "
            f"`{private_evidence.frame_post_return_bytes}` "
            f"(open={private_evidence.frame_post_return_open})."
        )
    if private_evidence.frame_skipped:
        lines.append(
            "Private frame save skipped before file open because no keyframes were recorded."
        )

    if private_evidence.keyframe_post_close_bytes is not None:
        lines.append(
            "Private keyframe post-close bytes: "
            f"`{private_evidence.keyframe_post_close_bytes}` "
            f"(open={private_evidence.keyframe_post_close_open})."
        )
    else:
        lines.append("Private keyframe post-close bytes: unavailable.")
    if private_evidence.keyframe_post_return_bytes is not None:
        lines.append(
            "Private keyframe after-return bytes: "
            f"`{private_evidence.keyframe_post_return_bytes}` "
            f"(open={private_evidence.keyframe_post_return_open})."
        )
    if private_evidence.initialization_maps is not None:
        points = (
            f" (points={private_evidence.initialization_map_points})"
            if private_evidence.initialization_map_points
            else ""
        )
        lines.append(
            "Private runtime map cycles observed: "
            f"`{private_evidence.initialization_maps}`{points}."
        )
    if private_evidence.active_map_resets is not None:
        lines.append(
            "Private active-map resets observed: "
            f"`{private_evidence.active_map_resets}`."
        )
    if private_evidence.reset_pre_clear_states is not None:
        lines.append(
            "Private reset pre-clear states: "
            f"`{private_evidence.reset_pre_clear_states}`."
        )
    if private_evidence.reset_post_clear_states is not None:
        lines.append(
            "Private reset post-clear states: "
            f"`{private_evidence.reset_post_clear_states}`."
        )
    if private_evidence.frame_save_atlas_state is not None:
        lines.append(
            "Private frame-save atlas state: "
            f"`{private_evidence.frame_save_atlas_state}`."
        )
    if private_evidence.keyframe_save_atlas_state is not None:
        lines.append(
            "Private keyframe-save atlas state: "
            f"`{private_evidence.keyframe_save_atlas_state}`."
        )
    if private_evidence.asan_summary is not None:
        lines.append(
            "Private AddressSanitizer summary: "
            f"`{private_evidence.asan_summary}`."
        )
    if private_evidence.missing_frame_after_save:
        lines.append(
            "Private frame-save signal: the delegate log reached frame-trajectory save "
            "completion, but the expected frame trajectory file was still missing afterward."
        )

    if private_evidence.missing_sources:
        lines.append(
            "Current blocker: the private rerun is still blocked before save comparison "
            "because these source inputs are missing: "
            + ", ".join(f"`{label}`" for label in private_evidence.missing_sources)
            + "."
        )
    elif private_evidence.frame_skipped:
        lines.append(
            "Current blocker: the private rerun reached the save boundary, but "
            "System::SaveTrajectoryEuRoC reported no keyframes and skipped opening "
            "the frame trajectory file, so there is still no HEL-75-style byte comparison."
        )
        if (
            private_evidence.reset_pre_clear_states is not None
            and private_evidence.reset_post_clear_states is not None
        ):
            lines.append(
                "Narrowed cause: the last active-map reset explicitly cleared the "
                "current map before shutdown, leaving the save call to inspect an "
                "atlas/current-map state with zero keyframes."
            )
    elif private_evidence.missing_frame_after_save:
        details: list[str] = []
        if private_evidence.initialization_maps is not None:
            map_detail = str(private_evidence.initialization_maps)
            if private_evidence.initialization_map_points:
                map_detail += f" map cycles (points={private_evidence.initialization_map_points})"
            else:
                map_detail += " map cycles"
            details.append(map_detail)
        if private_evidence.active_map_resets is not None:
            details.append(f"{private_evidence.active_map_resets} active-map resets")
        if private_evidence.asan_summary is not None:
            details.append(f"LeakSanitizer exit `{private_evidence.asan_summary}`")
        detail_suffix = (
            " Observed: " + ", ".join(details) + "."
            if details
            else ""
        )
        if private_evidence.frame_post_return_open:
            lines.append(
                "Current blocker: the private rerun reached the late shutdown/save boundary, "
                "and the frame trajectory was visible immediately after SaveTrajectoryEuRoC "
                "returned, but the expected frame artifact was gone again by final inspection."
                + detail_suffix
            )
        else:
            lines.append(
                "Current blocker: the private rerun reached the late shutdown/save boundary, "
                "but still left no post-close frame-byte evidence because no frame trajectory "
                "file was visible immediately after the save call returned."
                + detail_suffix
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
    issue_identifier: str,
    command: str,
    delegate_exit_code: int,
    downloads_root: Path,
    public_reference: PublicSaveReference,
    private_evidence: PrivateRunEvidence,
    discovered_video_00: Path | None,
    discovered_video_10: Path | None,
    discovered_calibration_00: Path | None,
    discovered_calibration_10: Path | None,
    discovered_extrinsics: Path | None,
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
        (
            f"- Calibration 00: `{discovered_calibration_00}`"
            if discovered_calibration_00 is not None
            else "- Calibration 00: not found"
        ),
        (
            f"- Calibration 10: `{discovered_calibration_10}`"
            if discovered_calibration_10 is not None
            else "- Calibration 10: not found"
        ),
        (
            f"- Stereo extrinsics: `{discovered_extrinsics}`"
            if discovered_extrinsics is not None
            else "- Stereo extrinsics: not found"
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
    return f"""# {issue_identifier} Private Save Comparison Follow-up

Issue: {issue_identifier}

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


def run_delegate_command(
    *,
    command: Sequence[str],
    cwd: Path,
    delegate_progress_artifact: Path,
    progress_artifact: Path,
    artifacts: dict[str, str],
    base_metrics: dict[str, object],
    experiment: dict[str, object],
    env_overrides: dict[str, str] | None,
    log_handle,
) -> int:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None

    output_queue: queue.Queue[str | None] = queue.Queue()

    def reader() -> None:
        for line in process.stdout:
            output_queue.put(line)
        output_queue.put(None)

    threading.Thread(target=reader, daemon=True).start()

    last_heartbeat_time = 0.0
    while True:
        try:
            item = output_queue.get(timeout=5.0)
        except queue.Empty:
            item = ""

        now = time.monotonic()
        if item is None:
            if process.poll() is not None:
                break
        elif item:
            log_handle.write(item)
            log_handle.flush()

        if now - last_heartbeat_time >= 30.0:
            delegate_payload = load_progress_artifact(delegate_progress_artifact)
            if delegate_payload is not None:
                write_progress_artifact(
                    progress_artifact,
                    build_delegate_heartbeat_payload(
                        base_metrics=base_metrics,
                        delegate_progress_artifact=delegate_progress_artifact,
                        delegate_payload=delegate_payload,
                        artifacts=artifacts,
                        experiment=experiment,
                    ),
                )
                log_handle.write(format_delegate_heartbeat_line(delegate_payload))
                log_handle.flush()
            last_heartbeat_time = now

        if process.poll() is not None and item is None:
            break

    return process.wait()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="manifests/insta360_x3_lens10_monocular_baseline.json",
    )
    parser.add_argument("--progress-issue", default="HEL-77")
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
    parser.add_argument(
        "--media-inbound-root",
        default=str(DEFAULT_OPENCLAW_MEDIA_INBOUND_ROOT),
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
    inbound_root = Path(args.media_inbound_root)

    discovered_video_00, discovered_video_10 = discover_openclaw_video_inputs(downloads_root)
    (
        discovered_calibration_00,
        discovered_calibration_10,
        discovered_extrinsics,
    ) = discover_openclaw_calibration_inputs(inbound_root)
    video_00 = resolve_repo_path(args.video_00) if args.video_00 else discovered_video_00
    video_10 = resolve_repo_path(args.video_10) if args.video_10 else discovered_video_10
    calibration_00 = (
        resolve_repo_path(args.calibration_00)
        if args.calibration_00
        else discovered_calibration_00
    )
    calibration_10 = (
        resolve_repo_path(args.calibration_10)
        if args.calibration_10
        else discovered_calibration_10
    )
    extrinsics = (
        resolve_repo_path(args.extrinsics)
        if args.extrinsics
        else discovered_extrinsics
    )

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
            f"the {args.progress_issue} report records both the HEL-75 public reference numbers and "
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
        str(
            orchestration_log.with_name(
                f"{args.progress_issue.lower()}_private_monocular_followup.log"
            )
        ),
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
    if calibration_00 is not None:
        command.extend(["--calibration-00", str(calibration_00)])
    if calibration_10 is not None:
        command.extend(["--calibration-10", str(calibration_10)])
    if extrinsics is not None:
        command.extend(["--extrinsics", str(extrinsics)])
    delegate_env_overrides = build_delegate_env_overrides()
    base_metrics = {
        "delegate_command": subprocess.list2cmdline(command),
        "delegate_env_overrides": delegate_env_overrides,
        "reference_frame_bytes": public_reference.frame_bytes,
        "reference_keyframe_bytes": public_reference.keyframe_bytes,
    }

    write_progress_artifact(
        progress_artifact,
        build_progress_payload(
            status="in_progress",
            current_step=(
                f"running HEL-74 private baseline under the {args.progress_issue} "
                "save comparison wrapper"
            ),
            completed=0,
            total=100,
            artifacts=artifacts,
            metrics=base_metrics,
            experiment=experiment,
            unit="percent",
            progress_percent=0,
        ),
    )

    with orchestration_log.open("w", encoding="utf-8") as log_handle:
        log_handle.write(
            f"Starting {args.progress_issue} private save comparison follow-up.\n"
        )
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
        log_handle.write(
            "Discovered calibration 00: "
            f"{calibration_00 if calibration_00 is not None else 'not found'}\n"
        )
        log_handle.write(
            "Discovered calibration 10: "
            f"{calibration_10 if calibration_10 is not None else 'not found'}\n"
        )
        log_handle.write(
            "Discovered stereo extrinsics: "
            f"{extrinsics if extrinsics is not None else 'not found'}\n\n"
        )
        log_handle.write(
            "Delegate env overrides: "
            f"{json.dumps(delegate_env_overrides, sort_keys=True)}\n\n"
        )
        log_handle.flush()
        delegate_exit_code = run_delegate_command(
            command=command,
            cwd=REPO_ROOT,
            delegate_progress_artifact=delegate_progress_artifact,
            progress_artifact=progress_artifact,
            artifacts=artifacts,
            base_metrics=base_metrics,
            experiment=experiment,
            env_overrides=delegate_env_overrides,
            log_handle=log_handle,
        )

    private_evidence = parse_private_run_evidence(delegate_status_report)
    status_report.write_text(
        render_status_report(
            issue_identifier=args.progress_issue,
            command=subprocess.list2cmdline(command),
            delegate_exit_code=delegate_exit_code,
            downloads_root=downloads_root,
            public_reference=public_reference,
            private_evidence=private_evidence,
            discovered_video_00=video_00,
            discovered_video_10=video_10,
            discovered_calibration_00=calibration_00,
            discovered_calibration_10=calibration_10,
            discovered_extrinsics=extrinsics,
            orchestration_log=orchestration_log,
            status_report=status_report,
            delegate_status_report=delegate_status_report,
        ),
        encoding="utf-8",
    )

    write_progress_artifact(
        progress_artifact,
        build_progress_payload(
            status="completed" if delegate_exit_code == 0 else "blocked",
            current_step=(
                f"{args.progress_issue} save comparison completed"
                if delegate_exit_code == 0
                else f"{args.progress_issue} save comparison blocked with auditable evidence"
            ),
            completed=100,
            total=100,
            artifacts=artifacts,
            metrics={
                "delegate_exit_code": delegate_exit_code,
                "missing_sources": list(private_evidence.missing_sources),
                "private_save_cwd": private_evidence.save_cwd,
                "private_frame_post_close_bytes": private_evidence.frame_post_close_bytes,
                "private_keyframe_post_close_bytes": private_evidence.keyframe_post_close_bytes,
                "reference_frame_bytes": public_reference.frame_bytes,
                "reference_keyframe_bytes": public_reference.keyframe_bytes,
            },
            experiment=experiment,
            unit="percent",
            progress_percent=100,
        ),
    )
    return delegate_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
