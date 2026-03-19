from __future__ import annotations

import json
from pathlib import Path
import shutil


def _load_summary(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_publish_sources(
    *,
    repo_root: Path,
    summary: dict[str, object],
) -> dict[str, Path]:
    artifacts = summary["artifacts"]
    sequence = summary["sequence"]
    sources = {
        name: repo_root / artifact["path"]
        for name, artifact in artifacts.items()
    }
    for index, sample_path in enumerate(sequence["sample_frame_paths"], start=1):
        sources[f"sample_frame_{index}"] = repo_root / sample_path
    return sources


def _format_metric(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def render_publish_index(
    *,
    published_report_path: Path,
    summary: dict[str, object],
) -> str:
    result = summary["result"]
    metrics = summary["metrics"]
    camera_metrics = metrics["camera_trajectory"]
    keyframe_metrics = metrics["keyframe_trajectory"]
    sample_images = summary["sequence"]["sample_frame_paths"]
    artifact_markup = "\n".join(
        (
            "<li>"
            + (
                f'<a href="{artifact["path"]}"><code>{artifact["path"]}</code></a>'
                if artifact.get("exists", True)
                else f'<code>{artifact["path"]}</code>'
            )
            + f" (exists: {artifact.get('exists', True)}, {artifact.get('size_bytes', 0)} bytes)</li>"
        )
        for artifact in summary["artifacts"].values()
    )
    sample_markup = "\n".join(
        f'<img alt="TUM RGB-D sample frame" src="{sample_path}" />'
        for sample_path in sample_images
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>TUM RGB-D published sanity run</title>
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
    <h1>splatica-orb-test TUM RGB-D published sanity run</h1>
    <p>
      Verdict:
      <strong class="verdict-{result["known_good_baseline_verdict"]}">
        {result["known_good_baseline_verdict"]}
      </strong>.
      {result["known_good_baseline_reason"]}
    </p>
    <section class="summary">
      <div class="card"><div class="label">Final Exit Code</div><div class="value">{result["final_exit_code"]}</div></div>
      <div class="card"><div class="label">Associations</div><div class="value">{summary["sequence"]["association_count"]}</div></div>
      <div class="card"><div class="label">Camera Points</div><div class="value">{camera_metrics["point_count"]}</div></div>
      <div class="card"><div class="label">Keyframe Points</div><div class="value">{keyframe_metrics["point_count"]}</div></div>
      <div class="card"><div class="label">Camera Coverage</div><div class="value">{_format_percent(metrics["camera_to_association_ratio"])}</div></div>
      <div class="card"><div class="label">Path Length</div><div class="value">{_format_metric(camera_metrics["path_length_meters"])} m</div></div>
    </section>
    <section class="grid">
      <div class="card">
        <h2>Sample Frames</h2>
        <div class="media">
          {sample_markup}
        </div>
      </div>
      <div class="card trajectory">
        <h2>Trajectory Plot</h2>
        <img alt="Trajectory plot" src="{summary["artifacts"]["trajectory_plot"]["path"]}" />
      </div>
    </section>
    <section class="grid" style="margin-top: 20px;">
      <div class="card">
        <h2>Run Metadata</h2>
        <ul>
          <li><code>{summary["repo"]["head_sha"]}</code></li>
          <li><code>{summary["run"]["manifest_path"]}</code></li>
          <li><code>{summary["baseline"]["commit"]}</code></li>
          <li><code>{summary["baseline"]["settings_path"]}</code></li>
          <li><code>{summary["sequence"]["association_path"]}</code></li>
          <li><code>{summary["run"]["command_display"]}</code></li>
        </ul>
      </div>
      <div class="card">
        <h2>Metrics</h2>
        <ul>
          <li>Camera displacement: <strong>{_format_metric(camera_metrics["displacement_meters"])} m</strong></li>
          <li>Camera span: <strong>{_format_metric(camera_metrics["duration_seconds"])} s</strong></li>
          <li>Keyframe span: <strong>{_format_metric(keyframe_metrics["duration_seconds"])} s</strong></li>
          <li>X range: <strong>{_format_metric(camera_metrics["min_x"])} .. {_format_metric(camera_metrics["max_x"])}</strong></li>
          <li>Y range: <strong>{_format_metric(camera_metrics["min_y"])} .. {_format_metric(camera_metrics["max_y"])}</strong></li>
          <li>Z range: <strong>{_format_metric(camera_metrics["min_z"])} .. {_format_metric(camera_metrics["max_z"])}</strong></li>
        </ul>
      </div>
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Artifacts</h2>
      <ul>{artifact_markup}</ul>
      <p>
        Secondary local visual report:
        <a href="{published_report_path.as_posix()}"><code>{published_report_path.as_posix()}</code></a>
      </p>
    </section>
  </main>
</body>
</html>
"""


def publish_rgbd_tum_bundle(
    *,
    publish_dir: Path,
    repo_root: Path,
    summary_path: Path,
) -> dict[str, object]:
    summary = _load_summary(summary_path)
    sources = collect_publish_sources(repo_root=repo_root, summary=summary)
    copied: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []

    if publish_dir.exists():
        shutil.rmtree(publish_dir)
    publish_dir.mkdir(parents=True, exist_ok=True)

    for name, source_path in sources.items():
        relative_path = source_path.relative_to(repo_root)
        if not source_path.exists():
            missing.append(
                {
                    "label": name,
                    "source_path": str(relative_path),
                }
            )
            continue
        destination_path = publish_dir / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        copied.append(
            {
                "label": name,
                "source_path": str(relative_path),
                "published_path": str(destination_path.relative_to(publish_dir)),
                "size_bytes": destination_path.stat().st_size,
            }
        )

    visual_report_relative = Path(summary["artifacts"]["visual_report"]["path"])
    (publish_dir / "index.html").write_text(
        render_publish_index(
            published_report_path=visual_report_relative,
            summary=summary,
        ),
        encoding="utf-8",
    )

    manifest = {
        "source_summary_path": str(summary_path.relative_to(repo_root)),
        "published_entrypoint": "index.html",
        "published_visual_report": str(visual_report_relative),
        "artifacts": copied,
        "missing_artifacts": missing,
    }
    (publish_dir / "artifact-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
