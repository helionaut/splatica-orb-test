from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class ResolvedTool:
    path: Path
    detail: str
    uses_repo_local_runtime: bool = False
    runtime_library_path: Path | None = None


@dataclass(frozen=True)
class ResolvedPrefix:
    prefix: Path
    detail: str


def resolve_repo_local_cmake_paths(repo_root: Path) -> tuple[Path, Path]:
    tool_root = repo_root / "build/local-tools/cmake-root/usr"
    return (
        tool_root / "bin/cmake",
        tool_root / "lib/x86_64-linux-gnu",
    )


def resolve_cmake_tool(repo_root: Path) -> ResolvedTool | None:
    resolved = shutil.which("cmake")
    if resolved is not None:
        return ResolvedTool(
            path=Path(resolved),
            detail=resolved,
        )

    local_bin, local_lib = resolve_repo_local_cmake_paths(repo_root)
    if local_bin.exists():
        return ResolvedTool(
            path=local_bin,
            detail=f"{local_bin} (repo-local bootstrap)",
            uses_repo_local_runtime=True,
            runtime_library_path=local_lib,
        )

    return None


def resolve_repo_local_eigen3_paths(repo_root: Path) -> tuple[Path, Path]:
    prefix = repo_root / "build/local-tools/eigen-root/usr"
    return (
        prefix / "share/eigen3/cmake/Eigen3Config.cmake",
        prefix / "share/pkgconfig/eigen3.pc",
    )


def resolve_eigen3_prefix(repo_root: Path) -> ResolvedPrefix | None:
    config_path, pkgconfig_path = resolve_repo_local_eigen3_paths(repo_root)
    if config_path.exists() or pkgconfig_path.exists():
        prefix = repo_root / "build/local-tools/eigen-root/usr"
        return ResolvedPrefix(
            prefix=prefix,
            detail=f"{prefix} (repo-local bootstrap)",
        )

    return None


def resolve_repo_local_ffmpeg_paths(repo_root: Path) -> tuple[Path, Path]:
    tool_root = repo_root / "build/local-tools/ffmpeg-root"
    return (
        tool_root / "bin/ffmpeg",
        tool_root / "bin/ffprobe",
    )


def resolve_ffmpeg_tool(repo_root: Path) -> ResolvedTool | None:
    resolved = shutil.which("ffmpeg")
    if resolved is not None:
        return ResolvedTool(
            path=Path(resolved),
            detail=resolved,
        )

    local_ffmpeg, _local_ffprobe = resolve_repo_local_ffmpeg_paths(repo_root)
    if local_ffmpeg.exists():
        return ResolvedTool(
            path=local_ffmpeg,
            detail=f"{local_ffmpeg} (repo-local bootstrap)",
        )

    return None


def resolve_ffprobe_tool(repo_root: Path) -> ResolvedTool | None:
    resolved = shutil.which("ffprobe")
    if resolved is not None:
        return ResolvedTool(
            path=Path(resolved),
            detail=resolved,
        )

    _local_ffmpeg, local_ffprobe = resolve_repo_local_ffmpeg_paths(repo_root)
    if local_ffprobe.exists():
        return ResolvedTool(
            path=local_ffprobe,
            detail=f"{local_ffprobe} (repo-local bootstrap)",
        )

    return None
