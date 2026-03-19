#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
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
from splatica_orb_test.rgbd_tum_baseline import (  # noqa: E402
    build_rgbd_tum_command,
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


def render_markdown_report(
    *,
    association_count: int,
    command: list[str],
    exit_code: int,
    manifest_notes: str,
    resolved,
    result_details: list[str],
) -> str:
    detail_lines = "\n".join(f"- {detail}" for detail in result_details) or "- none recorded"
    return f"""# RGB-D TUM baseline report: {resolved.report.stem}

## Result

- Exit code: `{exit_code}`
- Associations loaded: `{association_count}`

## Baseline

- ORB-SLAM3 checkout: `{relative_to_repo(resolved.baseline_root)}`
- Executable: `{relative_to_repo(resolved.executable)}`
- Vocabulary: `{relative_to_repo(resolved.vocabulary)}`
- Settings bundle: `{relative_to_repo(resolved.settings)}`

## Inputs

- Dataset root: `{relative_to_repo(resolved.dataset_root)}`
- Association file: `{relative_to_repo(resolved.association)}`

## Generated artifacts

- Camera trajectory: `{relative_to_repo(resolved.camera_trajectory)}`
- Keyframe trajectory: `{relative_to_repo(resolved.keyframe_trajectory)}`
- Log path: `{relative_to_repo(resolved.log)}`
- Markdown report: `{relative_to_repo(resolved.report)}`
- Trajectory plot: `{relative_to_repo(resolved.trajectory_plot)}`
- Visual report: `{relative_to_repo(resolved.visual_report)}`

## Command

`{shlex.join(command)}`

## Result details

{detail_lines}

## Notes

{manifest_notes}
"""


def render_visual_report(
    *,
    association_count: int,
    command: list[str],
    exit_code: int,
    resolved,
    result_details: list[str],
    sample_images: list[Path],
) -> str:
    image_markup = "\n".join(
        f'<img alt="TUM RGB-D sample frame" src="{html.escape(relative_from(path, resolved.visual_report))}" />'
        for path in sample_images
    )
    detail_markup = "\n".join(
        f"<li>{html.escape(detail)}</li>" for detail in result_details
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
    <p>Exit code <strong>{exit_code}</strong>. Public upstream run using the pinned ORB-SLAM3 checkout, upstream <code>TUM1.yaml</code>, and the upstream <code>fr1_xyz.txt</code> association file.</p>
    <section class="summary">
      <div class="card"><div class="label">Associations</div><div class="value">{association_count}</div></div>
      <div class="card"><div class="label">Camera trajectory</div><div class="value">{html.escape(relative_to_repo(resolved.camera_trajectory))}</div></div>
      <div class="card"><div class="label">Keyframe trajectory</div><div class="value">{html.escape(relative_to_repo(resolved.keyframe_trajectory))}</div></div>
      <div class="card"><div class="label">Command</div><div class="value"><code>{html.escape(shlex.join(command))}</code></div></div>
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
    <section class="card" style="margin-top: 20px;">
      <h2>Result Details</h2>
      <ul>{detail_markup}</ul>
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Artifacts</h2>
      <ul>
        <li><code>{html.escape(relative_to_repo(resolved.log))}</code></li>
        <li><code>{html.escape(relative_to_repo(resolved.report))}</code></li>
        <li><code>{html.escape(relative_to_repo(resolved.visual_report))}</code></li>
      </ul>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest = load_rgbd_tum_baseline_manifest(resolve_repo_path(args.manifest))
    resolved = resolve_rgbd_tum_baseline_paths(REPO_ROOT, manifest)

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
    for trajectory_path in (
        resolved.camera_trajectory,
        resolved.keyframe_trajectory,
    ):
        if trajectory_path.exists():
            trajectory_path.unlink()

    with resolved.log.open("w", encoding="utf-8") as log_handle:
        log_handle.write(
            f"Working directory: {relative_to_repo(resolved.trajectory_dir)}\n"
        )
        log_handle.write(f"Dataset root: {relative_to_repo(resolved.dataset_root)}\n")
        log_handle.write(
            f"Association file: {relative_to_repo(resolved.association)}\n"
        )
        log_handle.write(f"Command: {shlex.join(command)}\n\n")
        result = subprocess.run(
            command,
            check=False,
            cwd=resolved.trajectory_dir,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=build_runtime_environment(),
            text=True,
        )

    result_details = [f"Raw process exit code: {result.returncode}"]
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
    result_details.append(f"Camera trajectory points: {len(camera_points)}")

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

    if final_exit_code != 0:
        result_details.append(
            "ORB-SLAM3 did not finish with both non-empty trajectory outputs."
        )

    resolved.report.parent.mkdir(parents=True, exist_ok=True)
    resolved.report.write_text(
        render_markdown_report(
            association_count=len(associations),
            command=command,
            exit_code=final_exit_code,
            manifest_notes=manifest.notes,
            resolved=resolved,
            result_details=result_details,
        ),
        encoding="utf-8",
    )

    resolved.visual_report.parent.mkdir(parents=True, exist_ok=True)
    resolved.visual_report.write_text(
        render_visual_report(
            association_count=len(associations),
            command=command,
            exit_code=final_exit_code,
            resolved=resolved,
            result_details=result_details,
            sample_images=sample_images,
        ),
        encoding="utf-8",
    )

    print(f"Wrote log: {relative_to_repo(resolved.log)}")
    print(f"Wrote report: {relative_to_repo(resolved.report)}")
    print(f"Wrote visual report: {relative_to_repo(resolved.visual_report)}")
    return final_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
