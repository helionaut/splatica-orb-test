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


def resolve_repo_local_opencv_paths(repo_root: Path) -> tuple[Path, Path, Path]:
    prefix = repo_root / "build/local-tools/opencv-root/usr"
    return (
        prefix / "lib/x86_64-linux-gnu/cmake/opencv4/OpenCVConfig.cmake",
        prefix / "lib/x86_64-linux-gnu/pkgconfig/opencv4.pc",
        prefix / "lib/x86_64-linux-gnu",
    )


def resolve_opencv_prefix(repo_root: Path) -> ResolvedPrefix | None:
    config_path, pkgconfig_path, _library_path = resolve_repo_local_opencv_paths(repo_root)
    if config_path.exists() or pkgconfig_path.exists():
        prefix = repo_root / "build/local-tools/opencv-root/usr"
        return ResolvedPrefix(
            prefix=prefix,
            detail=f"{prefix} (repo-local bootstrap)",
        )

    return None


def resolve_repo_local_boost_paths(repo_root: Path) -> tuple[Path, Path]:
    prefix = repo_root / "build/local-tools/boost-root/usr"
    return (
        prefix / "include/boost/serialization/serialization.hpp",
        prefix / "lib/x86_64-linux-gnu",
    )


def resolve_boost_prefix(repo_root: Path) -> ResolvedPrefix | None:
    header_path, library_path = resolve_repo_local_boost_paths(repo_root)
    if header_path.exists() and any(library_path.glob("libboost_serialization.so*")):
        prefix = repo_root / "build/local-tools/boost-root/usr"
        return ResolvedPrefix(
            prefix=prefix,
            detail=f"{prefix} (repo-local bootstrap)",
        )

    return None


def resolve_repo_local_pangolin_paths(repo_root: Path) -> tuple[Path, Path]:
    prefix = repo_root / "build/local-tools/pangolin-root/usr/local"
    return (
        prefix / "lib/cmake/Pangolin/PangolinConfig.cmake",
        prefix / "lib/pkgconfig/pangolin.pc",
    )


def resolve_pangolin_prefix(repo_root: Path) -> ResolvedPrefix | None:
    config_path, pkgconfig_path = resolve_repo_local_pangolin_paths(repo_root)
    if config_path.exists() or pkgconfig_path.exists():
        prefix = repo_root / "build/local-tools/pangolin-root/usr/local"
        return ResolvedPrefix(
            prefix=prefix,
            detail=f"{prefix} (repo-local install)",
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
