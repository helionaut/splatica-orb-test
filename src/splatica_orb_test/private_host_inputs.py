from __future__ import annotations

from pathlib import Path


DEFAULT_OPENCLAW_DOWNLOADS_ROOT = Path("/home/helionaut/.openclaw/workspace/downloads")
DEFAULT_OPENCLAW_MEDIA_INBOUND_ROOT = Path("/home/helionaut/.openclaw/media/inbound")


def _discover_latest_matching_file(root: Path, *patterns: str) -> Path | None:
    if not root.exists():
        return None

    candidates: set[Path] = set()
    for pattern in patterns:
        candidates.update(root.rglob(pattern))
    if not candidates:
        return None
    return sorted(candidates)[-1]


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


def discover_openclaw_calibration_inputs(
    inbound_root: Path,
) -> tuple[Path | None, Path | None, Path | None]:
    return (
        _discover_latest_matching_file(inbound_root, "*insta360_x3_kb4_00_calib*.txt"),
        _discover_latest_matching_file(inbound_root, "*insta360_x3_kb4_10_calib*.txt"),
        _discover_latest_matching_file(inbound_root, "*insta360_x3_extr_rigs_calib*.json"),
    )
