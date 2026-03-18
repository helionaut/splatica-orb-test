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
