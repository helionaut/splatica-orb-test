#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.local_tooling import (  # noqa: E402
    resolve_headless_display_prefix,
    resolve_repo_local_boost_runtime_library_paths,
    resolve_repo_local_opencv_runtime_library_paths,
    resolve_repo_local_pangolin_runtime_library_paths,
)
from splatica_orb_test.monocular_inputs import compute_file_sha256  # noqa: E402
from splatica_orb_test.rgbd_tum_baseline import (  # noqa: E402
    apply_rgbd_tum_output_tag,
    build_rgbd_tum_command,
    compute_tum_trajectory_metrics,
    load_rgbd_tum_associations,
    load_rgbd_tum_baseline_manifest,
    load_tum_trajectory_points,
    render_tum_trajectory_svg,
    resolve_rgbd_tum_baseline_paths,
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


def relative_from(path: Path, base_file: Path) -> str:
    return os.path.relpath(path, start=base_file.parent)


def build_runtime_environment() -> dict[str, str]:
    env = os.environ.copy()
    runtime_paths: list[str] = []
    for path in resolve_repo_local_opencv_runtime_library_paths(REPO_ROOT):
        runtime_paths.append(str(path))
    for path in resolve_repo_local_boost_runtime_library_paths(REPO_ROOT):
        runtime_paths.append(str(path))
    for path in resolve_repo_local_pangolin_runtime_library_paths(REPO_ROOT):
        runtime_paths.append(str(path))
    if runtime_paths:
        existing = env.get("LD_LIBRARY_PATH")
        unique_runtime_paths = list(dict.fromkeys(runtime_paths))
        env["LD_LIBRARY_PATH"] = ":".join(
            unique_runtime_paths + ([existing] if existing else [])
        )
    return env


def resolve_repo_head_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
    ).strip()


def format_metric(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def summarize_artifact(path: Path) -> dict[str, object]:
    exists = path.exists()
    summary: dict[str, object] = {
        "path": relative_to_repo(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
        "sha256": compute_file_sha256(path) if exists and path.is_file() else None,
    }
    return summary


def assess_known_good_baseline(
    *,
    final_exit_code: int,
    association_count: int,
    camera_point_count: int,
    keyframe_point_count: int,
) -> tuple[str, str]:
    if (
        final_exit_code == 0
        and association_count > 0
        and camera_point_count > 0
        and keyframe_point_count > 0
    ):
        return (
            "useful",
            "Pinned upstream rgbd_tum completed with non-empty camera and keyframe trajectories.",
        )
    if camera_point_count > 0 and keyframe_point_count == 0:
        return (
            "partial",
            "The lane produced camera motion evidence but not a complete keyframe trajectory baseline.",
        )
    return (
        "not_useful",
        "The run did not finish with the full non-empty trajectory evidence required for a known-good baseline.",
    )


def build_run_summary(
    *,
    args,
    association_count: int,
    camera_points: list[tuple[float, float, float, float]],
    command: list[str],
    final_exit_code: int,
    keyframe_points: list[tuple[float, float, float, float]],
    manifest,
    raw_exit_code: int,
    resolved,
    result_details: list[str],
    sample_images: list[Path],
) -> dict[str, object]:
    camera_metrics = compute_tum_trajectory_metrics(camera_points)
    keyframe_metrics = compute_tum_trajectory_metrics(keyframe_points)
    camera_ratio = (
        camera_metrics["point_count"] / association_count if association_count else None
    )
    keyframe_ratio = (
        keyframe_metrics["point_count"] / association_count if association_count else None
    )
    verdict, verdict_reason = assess_known_good_baseline(
        final_exit_code=final_exit_code,
        association_count=association_count,
        camera_point_count=int(camera_metrics["point_count"]),
        keyframe_point_count=int(keyframe_metrics["point_count"]),
    )
    summary: dict[str, object] = {
        "repo": {
            "head_sha": resolve_repo_head_sha(),
        },
        "baseline": {
            "name": manifest.baseline_name,
            "repo_url": manifest.repo_url,
            "commit": manifest.baseline_commit,
            "checkout_path": relative_to_repo(resolved.baseline_root),
            "executable_path": relative_to_repo(resolved.executable),
            "vocabulary_path": relative_to_repo(resolved.vocabulary),
            "settings_path": relative_to_repo(resolved.settings),
        },
        "sequence": {
            "name": manifest.sequence_name,
            "dataset_name": manifest.dataset_name,
            "archive_url": manifest.archive_url,
            "archive_path": manifest.archive_path,
            "dataset_root": relative_to_repo(resolved.dataset_root),
            "association_path": relative_to_repo(resolved.association),
            "association_count": association_count,
            "sample_frame_paths": [relative_to_repo(path) for path in sample_images],
        },
        "run": {
            "manifest_path": args.manifest,
            "launch_script": manifest.launch_script,
            "command": command,
            "command_display": shlex.join(command),
            "diagnostic_toggles": {
                "max_frames": args.max_frames,
                "disable_viewer": args.disable_viewer,
                "skip_frame_trajectory_save": args.skip_frame_trajectory_save,
                "skip_keyframe_trajectory_save": args.skip_keyframe_trajectory_save,
            },
        },
        "result": {
            "raw_exit_code": raw_exit_code,
            "final_exit_code": final_exit_code,
            "known_good_baseline_verdict": verdict,
            "known_good_baseline_reason": verdict_reason,
            "details": result_details,
        },
        "metrics": {
            "camera_trajectory": camera_metrics,
            "keyframe_trajectory": keyframe_metrics,
            "camera_to_association_ratio": round(camera_ratio, 6)
            if camera_ratio is not None
            else None,
            "keyframe_to_association_ratio": round(keyframe_ratio, 6)
            if keyframe_ratio is not None
            else None,
        },
        "artifacts": {
            "camera_trajectory": summarize_artifact(resolved.camera_trajectory),
            "keyframe_trajectory": summarize_artifact(resolved.keyframe_trajectory),
            "log": summarize_artifact(resolved.log),
            "markdown_report": summarize_artifact(resolved.report),
            "summary_json": {
                "path": relative_to_repo(resolved.summary_json),
                "exists": False,
                "size_bytes": 0,
                "sha256": None,
            },
            "trajectory_plot": summarize_artifact(resolved.trajectory_plot),
            "visual_report": summarize_artifact(resolved.visual_report),
        },
        "notes": manifest.notes,
    }
    return summary


def render_markdown_report(*, resolved, summary: dict[str, object]) -> str:
    result = summary["result"]
    metrics = summary["metrics"]
    camera_metrics = metrics["camera_trajectory"]
    keyframe_metrics = metrics["keyframe_trajectory"]
    detail_lines = "\n".join(f"- {detail}" for detail in result["details"]) or "- none recorded"
    artifact_lines = "\n".join(
        (
            f"- {label.replace('_', ' ').title()}: "
            f"`{artifact['path']}` "
            f"(exists: `{artifact['exists']}`, size: `{artifact['size_bytes']}` bytes, sha256: `{artifact['sha256']}`)"
        )
        for label, artifact in summary["artifacts"].items()
    )
    return f"""# RGB-D TUM baseline report: {resolved.report.stem}

## Result

- Final exit code: `{result["final_exit_code"]}`
- Raw process exit code: `{result["raw_exit_code"]}`
- Known-good baseline verdict: `{result["known_good_baseline_verdict"]}`
- Verdict reason: {result["known_good_baseline_reason"]}

## Run Metadata

- Producing repo commit: `{summary["repo"]["head_sha"]}`
- Manifest: `{summary["run"]["manifest_path"]}`
- Launch script: `{summary["run"]["launch_script"]}`
- Command: `{summary["run"]["command_display"]}`
- ORB-SLAM3 baseline: `{summary["baseline"]["repo_url"]}` @ `{summary["baseline"]["commit"]}`
- Executable: `{summary["baseline"]["executable_path"]}`
- Vocabulary: `{summary["baseline"]["vocabulary_path"]}`
- Settings bundle: `{summary["baseline"]["settings_path"]}`
- Dataset root: `{summary["sequence"]["dataset_root"]}`
- Dataset name: `{summary["sequence"]["dataset_name"]}`
- Association file: `{summary["sequence"]["association_path"]}`
- Associations loaded: `{summary["sequence"]["association_count"]}`
- Diagnostic toggles: `{json.dumps(summary["run"]["diagnostic_toggles"], sort_keys=True)}`

## Summary Metrics

- Camera trajectory points: `{camera_metrics["point_count"]}`
- Keyframe trajectory points: `{keyframe_metrics["point_count"]}`
- Camera / association coverage: `{format_percent(metrics["camera_to_association_ratio"])}`
- Keyframe / association coverage: `{format_percent(metrics["keyframe_to_association_ratio"])}`
- Camera path length (m): `{format_metric(camera_metrics["path_length_meters"])}`
- Camera displacement (m): `{format_metric(camera_metrics["displacement_meters"])}`
- Camera timestamp span (s): `{format_metric(camera_metrics["duration_seconds"])}`
- Keyframe path length (m): `{format_metric(keyframe_metrics["path_length_meters"])}`
- Keyframe displacement (m): `{format_metric(keyframe_metrics["displacement_meters"])}`
- Keyframe timestamp span (s): `{format_metric(keyframe_metrics["duration_seconds"])}`
- Camera x/y/z ranges: `x={format_metric(camera_metrics["min_x"])}..{format_metric(camera_metrics["max_x"])}`, `y={format_metric(camera_metrics["min_y"])}..{format_metric(camera_metrics["max_y"])}`, `z={format_metric(camera_metrics["min_z"])}..{format_metric(camera_metrics["max_z"])}`

## Generated Artifacts

{artifact_lines}

## Result Details

{detail_lines}

## Notes

{summary["notes"]}
"""


def render_visual_report(*, resolved, summary: dict[str, object]) -> str:
    metrics = summary["metrics"]
    camera_metrics = metrics["camera_trajectory"]
    keyframe_metrics = metrics["keyframe_trajectory"]
    result = summary["result"]
    sample_images = summary["sequence"]["sample_frame_paths"]
    image_markup = "\n".join(
        (
            f'<img alt="TUM RGB-D sample frame" '
            f'src="{html.escape(relative_from(REPO_ROOT / image_path, resolved.visual_report))}" />'
        )
        for image_path in sample_images
    )
    detail_markup = "\n".join(
        f"<li>{html.escape(detail)}</li>" for detail in result["details"]
    )
    artifact_markup = "\n".join(
        (
            "<li><a href=\""
            f"{html.escape(relative_from(REPO_ROOT / artifact['path'], resolved.visual_report))}"
            "\"><code>"
            f"{html.escape(artifact['path'])}"
            "</code></a>"
            f" <span class=\"muted\">({artifact['size_bytes']} bytes)</span></li>"
        )
        for artifact in summary["artifacts"].values()
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>TUM RGB-D sanity report</title>
  <style>
    :root {{
      color-scheme: light;
      --paper: #f6f2e8;
      --ink: #1f1f1f;
      --muted: #57534e;
      --accent: #19647e;
      --panel: #fffdf8;
      --border: #d6d3d1;
      --good: #2a9d8f;
      --warn: #b7791f;
      --bad: #c44536;
    }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(25,100,126,0.18), transparent 32%),
        linear-gradient(180deg, #f8f5ee 0%, var(--paper) 100%);
      color: var(--ink);
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 24px 56px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
      font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 12px;
      margin: 20px 0 28px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 12px 28px rgba(31,31,31,0.08);
    }}
    .label {{
      color: var(--muted);
      font-size: 0.85rem;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .value {{
      font-size: 1.25rem;
      font-weight: 600;
      word-break: break-word;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 20px;
      align-items: start;
    }}
    .media {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    img {{
      width: 100%;
      display: block;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: #000;
    }}
    .trajectory img {{
      background: var(--panel);
      padding: 8px;
    }}
    code {{
      font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
      word-break: break-all;
    }}
    ul {{
      margin: 12px 0 0;
      padding-left: 20px;
    }}
    .muted {{
      color: var(--muted);
    }}
    .verdict-useful {{
      color: var(--good);
    }}
    .verdict-partial {{
      color: var(--warn);
    }}
    .verdict-not_useful {{
      color: var(--bad);
    }}
    @media (max-width: 860px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
      .media {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>TUM RGB-D fr1/xyz clean-room sanity</h1>
    <p>
      Verdict:
      <strong class="verdict-{html.escape(result["known_good_baseline_verdict"])}">
        {html.escape(result["known_good_baseline_verdict"])}
      </strong>.
      {html.escape(result["known_good_baseline_reason"])}
    </p>
    <section class="summary">
      <div class="card"><div class="label">Final Exit Code</div><div class="value">{result["final_exit_code"]}</div></div>
      <div class="card"><div class="label">Associations</div><div class="value">{summary["sequence"]["association_count"]}</div></div>
      <div class="card"><div class="label">Camera Points</div><div class="value">{camera_metrics["point_count"]}</div></div>
      <div class="card"><div class="label">Keyframe Points</div><div class="value">{keyframe_metrics["point_count"]}</div></div>
      <div class="card"><div class="label">Camera Coverage</div><div class="value">{html.escape(format_percent(metrics["camera_to_association_ratio"]))}</div></div>
      <div class="card"><div class="label">Path Length</div><div class="value">{html.escape(format_metric(camera_metrics["path_length_meters"]))} m</div></div>
    </section>
    <section class="grid">
      <div class="card">
        <h2>Sample Frames</h2>
        <div class="media">
          {image_markup}
        </div>
      </div>
      <div class="card trajectory">
        <h2>Trajectory Plot</h2>
        <img alt="Trajectory plot" src="{html.escape(relative_from(resolved.trajectory_plot, resolved.visual_report))}" />
      </div>
    </section>
    <section class="grid" style="margin-top: 20px;">
      <div class="card">
        <h2>Run Metadata</h2>
        <ul>
          <li><code>{html.escape(summary["repo"]["head_sha"])}</code></li>
          <li><code>{html.escape(summary["run"]["manifest_path"])}</code></li>
          <li><code>{html.escape(summary["baseline"]["commit"])}</code></li>
          <li><code>{html.escape(summary["baseline"]["settings_path"])}</code></li>
          <li><code>{html.escape(summary["sequence"]["association_path"])}</code></li>
          <li><code>{html.escape(summary["run"]["command_display"])}</code></li>
        </ul>
      </div>
      <div class="card">
        <h2>Summary Metrics</h2>
        <ul>
          <li>Camera displacement: <strong>{html.escape(format_metric(camera_metrics["displacement_meters"]))} m</strong></li>
          <li>Camera span: <strong>{html.escape(format_metric(camera_metrics["duration_seconds"]))} s</strong></li>
          <li>Keyframe span: <strong>{html.escape(format_metric(keyframe_metrics["duration_seconds"]))} s</strong></li>
          <li>X range: <strong>{html.escape(format_metric(camera_metrics["min_x"]))} .. {html.escape(format_metric(camera_metrics["max_x"]))}</strong></li>
          <li>Y range: <strong>{html.escape(format_metric(camera_metrics["min_y"]))} .. {html.escape(format_metric(camera_metrics["max_y"]))}</strong></li>
          <li>Z range: <strong>{html.escape(format_metric(camera_metrics["min_z"]))} .. {html.escape(format_metric(camera_metrics["max_z"]))}</strong></li>
        </ul>
      </div>
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Result Details</h2>
      <ul>{detail_markup}</ul>
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Artifacts</h2>
      <ul>{artifact_markup}</ul>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-tag")
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--disable-viewer", action="store_true")
    parser.add_argument("--skip-frame-trajectory-save", action="store_true")
    parser.add_argument("--skip-keyframe-trajectory-save", action="store_true")
    args = parser.parse_args()
    if args.max_frames is not None and args.max_frames <= 0:
        raise SystemExit("--max-frames must be a positive integer.")

    manifest = load_rgbd_tum_baseline_manifest(resolve_repo_path(args.manifest))
    resolved = apply_rgbd_tum_output_tag(
        resolve_rgbd_tum_baseline_paths(REPO_ROOT, manifest),
        args.output_tag,
    )

    if not resolved.dataset_root.exists():
        subprocess.run(
            [
                str(REPO_ROOT / "scripts/fetch_tum_rgbd_dataset.py"),
                "--manifest",
                args.manifest,
            ],
            check=True,
            cwd=REPO_ROOT,
        )

    missing = [
        path
        for path in (
            resolved.executable,
            resolved.vocabulary,
            resolved.settings,
            resolved.association,
            resolved.dataset_root,
        )
        if not path.exists()
    ]
    if missing:
        missing_text = ", ".join(relative_to_repo(path) for path in missing)
        raise SystemExit(
            "Missing RGB-D baseline assets: "
            f"{missing_text}. Run ./scripts/fetch_orbslam3_baseline.sh, "
            "./scripts/fetch_tum_rgbd_dataset.py --manifest manifests/tum_rgbd_fr1_xyz_sanity.json, "
            "and ORB_SLAM3_BUILD_TARGET=rgbd_tum ./scripts/build_orbslam3_baseline.sh first."
        )

    associations = load_rgbd_tum_associations(resolved.association)
    command = [
        *resolve_headless_display_prefix(),
        *build_rgbd_tum_command(resolved),
    ]

    resolved.trajectory_dir.mkdir(parents=True, exist_ok=True)
    resolved.log.parent.mkdir(parents=True, exist_ok=True)
    for artifact_path in (
        resolved.camera_trajectory,
        resolved.keyframe_trajectory,
        resolved.report,
        resolved.summary_json,
        resolved.trajectory_plot,
        resolved.visual_report,
    ):
        if artifact_path.exists():
            artifact_path.unlink()

    with resolved.log.open("w", encoding="utf-8") as log_handle:
        log_handle.write(
            f"Working directory: {relative_to_repo(resolved.trajectory_dir)}\n"
        )
        log_handle.write(f"Dataset root: {relative_to_repo(resolved.dataset_root)}\n")
        log_handle.write(
            f"Association file: {relative_to_repo(resolved.association)}\n"
        )
        log_handle.write(f"Command: {shlex.join(command)}\n")
        log_handle.write(f"Repo commit: {resolve_repo_head_sha()}\n\n")
        log_handle.write(
            "Diagnostic toggles: "
            f"max_frames={args.max_frames}, "
            f"disable_viewer={args.disable_viewer}, "
            f"skip_frame_save={args.skip_frame_trajectory_save}, "
            f"skip_keyframe_save={args.skip_keyframe_trajectory_save}\n\n"
        )
        run_env = build_runtime_environment()
        if args.max_frames is not None:
            run_env["ORB_SLAM3_HEL63_MAX_FRAMES"] = str(args.max_frames)
        if args.disable_viewer:
            run_env["ORB_SLAM3_DISABLE_VIEWER"] = "1"
        if args.skip_frame_trajectory_save:
            run_env["ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE"] = "1"
        if args.skip_keyframe_trajectory_save:
            run_env["ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE"] = "1"
        result = subprocess.run(
            command,
            check=False,
            cwd=resolved.trajectory_dir,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=run_env,
            text=True,
        )

    result_details = [
        f"Raw process exit code: {result.returncode}",
        "Diagnostic toggles: "
        f"max_frames={args.max_frames}, "
        f"disable_viewer={args.disable_viewer}, "
        f"skip_frame_save={args.skip_frame_trajectory_save}, "
        f"skip_keyframe_save={args.skip_keyframe_trajectory_save}",
    ]
    final_exit_code = result.returncode
    for label, trajectory_path in (
        ("Camera trajectory", resolved.camera_trajectory),
        ("Keyframe trajectory", resolved.keyframe_trajectory),
    ):
        if not trajectory_path.exists():
            result_details.append(
                f"{label}: missing at {relative_to_repo(trajectory_path)}"
            )
            final_exit_code = 2
            continue

        size_bytes = trajectory_path.stat().st_size
        result_details.append(
            f"{label}: {relative_to_repo(trajectory_path)} ({size_bytes} bytes)"
        )
        if size_bytes == 0:
            final_exit_code = 2

    camera_points = (
        load_tum_trajectory_points(resolved.camera_trajectory)
        if resolved.camera_trajectory.exists()
        and resolved.camera_trajectory.stat().st_size > 0
        else []
    )
    keyframe_points = (
        load_tum_trajectory_points(resolved.keyframe_trajectory)
        if resolved.keyframe_trajectory.exists()
        and resolved.keyframe_trajectory.stat().st_size > 0
        else []
    )
    result_details.append(f"Camera trajectory points: {len(camera_points)}")
    result_details.append(f"Keyframe trajectory points: {len(keyframe_points)}")

    resolved.trajectory_plot.parent.mkdir(parents=True, exist_ok=True)
    resolved.trajectory_plot.write_text(
        render_tum_trajectory_svg(
            camera_points,
            title="TUM RGB-D fr1/xyz camera trajectory",
        ),
        encoding="utf-8",
    )

    sample_images: list[Path] = []
    if associations:
        sample_images.append(resolved.dataset_root / associations[0].rgb_path)
        sample_images.append(
            resolved.dataset_root / associations[len(associations) // 2].rgb_path
        )

    if final_exit_code == 0 and len(camera_points) == 0:
        final_exit_code = 2
        result_details.append("Camera trajectory was empty after a zero exit code.")

    if final_exit_code == 0 and len(keyframe_points) == 0:
        final_exit_code = 2
        result_details.append("Keyframe trajectory was empty after a zero exit code.")

    if final_exit_code != 0:
        result_details.append(
            "ORB-SLAM3 did not finish with both non-empty trajectory outputs."
        )

    summary = build_run_summary(
        args=args,
        association_count=len(associations),
        camera_points=camera_points,
        command=command,
        final_exit_code=final_exit_code,
        keyframe_points=keyframe_points,
        manifest=manifest,
        raw_exit_code=result.returncode,
        resolved=resolved,
        result_details=result_details,
        sample_images=sample_images,
    )

    resolved.summary_json.parent.mkdir(parents=True, exist_ok=True)
    resolved.summary_json.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    summary["artifacts"]["summary_json"] = summarize_artifact(resolved.summary_json)
    resolved.summary_json.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    resolved.report.parent.mkdir(parents=True, exist_ok=True)
    resolved.report.write_text(
        render_markdown_report(
            resolved=resolved,
            summary=summary,
        ),
        encoding="utf-8",
    )

    summary["artifacts"]["markdown_report"] = summarize_artifact(resolved.report)

    resolved.visual_report.parent.mkdir(parents=True, exist_ok=True)
    resolved.visual_report.write_text(
        render_visual_report(
            resolved=resolved,
            summary=summary,
        ),
        encoding="utf-8",
    )

    summary["artifacts"]["visual_report"] = summarize_artifact(resolved.visual_report)
    resolved.report.write_text(
        render_markdown_report(
            resolved=resolved,
            summary=summary,
        ),
        encoding="utf-8",
    )
    summary["artifacts"]["markdown_report"] = summarize_artifact(resolved.report)
    resolved.visual_report.write_text(
        render_visual_report(
            resolved=resolved,
            summary=summary,
        ),
        encoding="utf-8",
    )
    summary["artifacts"]["visual_report"] = summarize_artifact(resolved.visual_report)
    resolved.summary_json.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote log: {relative_to_repo(resolved.log)}")
    print(f"Wrote report: {relative_to_repo(resolved.report)}")
    print(f"Wrote summary: {relative_to_repo(resolved.summary_json)}")
    print(f"Wrote visual report: {relative_to_repo(resolved.visual_report)}")
    return final_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
