from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from .local_tooling import (
    resolve_boost_prefix,
    resolve_cmake_tool,
    resolve_eigen3_prefix,
    resolve_opencv_prefix,
    resolve_pangolin_prefix,
)
from .monocular_baseline import (
    load_monocular_baseline_manifest,
    resolve_monocular_baseline_paths,
)


@dataclass(frozen=True)
class PrerequisiteCheck:
    label: str
    ready: bool
    detail: str


@dataclass(frozen=True)
class MonocularBaselinePrerequisites:
    manifest_path: Path
    prepare_checks: tuple[PrerequisiteCheck, ...]
    execute_checks: tuple[PrerequisiteCheck, ...]

    @property
    def ready_for_prepare_only(self) -> bool:
        return all(check.ready for check in self.prepare_checks)

    @property
    def ready_for_execute(self) -> bool:
        return self.ready_for_prepare_only and all(
            check.ready for check in self.execute_checks
        )


def _detect_tool(name: str) -> PrerequisiteCheck:
    resolved = shutil.which(name)
    if resolved is None:
        return PrerequisiteCheck(
            label=f"Tool `{name}`",
            ready=False,
            detail="not found on PATH",
        )

    return PrerequisiteCheck(
        label=f"Tool `{name}`",
        ready=True,
        detail=resolved,
    )


def _read_baseline_commit(checkout_path: Path) -> str | None:
    if not (checkout_path / ".git").exists():
        return None

    result = subprocess.run(
        ["git", "-C", str(checkout_path), "rev-parse", "HEAD"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _detect_pkg_config_package(*names: str) -> tuple[str | None, str | None]:
    if shutil.which("pkg-config") is None:
        return None, None

    for name in names:
        result = subprocess.run(
            ["pkg-config", "--modversion", name],
            capture_output=True,
            check=False,
            text=True,
        )
        if result.returncode == 0:
            return name, result.stdout.strip()

    return None, None


def _parse_version(version_text: str) -> tuple[int, ...]:
    components: list[int] = []
    for part in version_text.split("."):
        digits = "".join(char for char in part if char.isdigit())
        if not digits:
            break
        components.append(int(digits))
    return tuple(components)


def _detect_versioned_pkg_config_package(
    *,
    label: str,
    names: tuple[str, ...],
    minimum_version: tuple[int, ...],
) -> PrerequisiteCheck:
    package_name, package_version = _detect_pkg_config_package(*names)
    if package_name is None or package_version is None:
        return PrerequisiteCheck(
            label=label,
            ready=False,
            detail="not detected via pkg-config",
        )

    is_ready = _parse_version(package_version) >= minimum_version
    minimum_text = ".".join(str(part) for part in minimum_version)
    status_detail = f"{package_name} {package_version} (requires >= {minimum_text})"
    return PrerequisiteCheck(
        label=label,
        ready=is_ready,
        detail=status_detail,
    )


def _detect_eigen3_prerequisite(repo_root: Path) -> PrerequisiteCheck:
    resolved_eigen = resolve_eigen3_prefix(repo_root)
    if resolved_eigen is not None:
        return PrerequisiteCheck(
            label="Eigen3 development package",
            ready=True,
            detail=resolved_eigen.detail,
        )

    return _detect_versioned_pkg_config_package(
        label="Eigen3 development package",
        names=("eigen3",),
        minimum_version=(3, 3, 0),
    )


def _detect_opencv_prerequisite(repo_root: Path) -> PrerequisiteCheck:
    resolved_opencv = resolve_opencv_prefix(repo_root)
    if resolved_opencv is not None:
        return PrerequisiteCheck(
            label="OpenCV development package",
            ready=True,
            detail=resolved_opencv.detail,
        )

    return _detect_versioned_pkg_config_package(
        label="OpenCV development package",
        names=("opencv4", "opencv"),
        minimum_version=(4, 4),
    )


def _system_boost_serialization_ready() -> bool:
    header_path = Path("/usr/include/boost/serialization/serialization.hpp")
    if not header_path.exists():
        return False

    library_roots = (
        Path("/usr/lib/x86_64-linux-gnu"),
        Path("/usr/lib64"),
        Path("/usr/lib"),
    )
    return any(
        library_root.exists()
        and any(library_root.glob("libboost_serialization.so*"))
        for library_root in library_roots
    )


def _detect_boost_serialization_prerequisite(repo_root: Path) -> PrerequisiteCheck:
    resolved_boost = resolve_boost_prefix(repo_root)
    if resolved_boost is not None:
        return PrerequisiteCheck(
            label="Boost serialization development package",
            ready=True,
            detail=resolved_boost.detail,
        )

    if _system_boost_serialization_ready():
        return PrerequisiteCheck(
            label="Boost serialization development package",
            ready=True,
            detail="/usr/include + /usr/lib (system install)",
        )

    return PrerequisiteCheck(
        label="Boost serialization development package",
        ready=False,
        detail="not detected on system paths or in build/local-tools/boost-root",
    )


def _detect_pangolin_prerequisite(repo_root: Path) -> PrerequisiteCheck:
    resolved_pangolin = resolve_pangolin_prefix(repo_root)
    if resolved_pangolin is not None:
        return PrerequisiteCheck(
            label="Pangolin development package",
            ready=True,
            detail=resolved_pangolin.detail,
        )

    pangolin_name, pangolin_version = _detect_pkg_config_package("pangolin")
    return PrerequisiteCheck(
        label="Pangolin development package",
        ready=pangolin_name is not None,
        detail=(
            "not detected via pkg-config or build/local-tools/pangolin-root; run make bootstrap-local-pangolin"
            if pangolin_name is None
            else f"{pangolin_name} {pangolin_version} (requires CMake-discoverable Pangolin)"
        ),
    )


def inspect_monocular_baseline_prerequisites(
    repo_root: Path,
    manifest_path: Path,
) -> MonocularBaselinePrerequisites:
    manifest = load_monocular_baseline_manifest(manifest_path)
    resolved = resolve_monocular_baseline_paths(repo_root, manifest)

    prepare_checks = (
        PrerequisiteCheck(
            label="Calibration JSON",
            ready=resolved.calibration.exists(),
            detail=str(resolved.calibration),
        ),
        PrerequisiteCheck(
            label="Frame index CSV",
            ready=resolved.frame_index.exists(),
            detail=str(resolved.frame_index),
        ),
    )

    checkout_exists = (resolved.baseline_root / ".git").exists()
    checkout_detail = str(resolved.baseline_root)
    execute_checks: list[PrerequisiteCheck] = [
        PrerequisiteCheck(
            label="Baseline checkout",
            ready=checkout_exists,
            detail=checkout_detail,
        )
    ]

    checkout_commit = _read_baseline_commit(resolved.baseline_root)
    execute_checks.append(
        PrerequisiteCheck(
            label="Baseline commit",
            ready=checkout_commit == manifest.baseline_commit,
            detail=checkout_commit or "not available",
        )
    )

    resolved_cmake = resolve_cmake_tool(repo_root)
    execute_checks.append(
        PrerequisiteCheck(
            label="Tool `cmake`",
            ready=resolved_cmake is not None,
            detail=(
                "not found on PATH or in build/local-tools/cmake-root"
                if resolved_cmake is None
                else resolved_cmake.detail
            ),
        )
    )
    execute_checks.extend(
        [
            _detect_tool("make"),
            _detect_tool("pkg-config"),
        ]
    )

    execute_checks.append(_detect_opencv_prerequisite(repo_root))
    execute_checks.append(_detect_eigen3_prerequisite(repo_root))
    execute_checks.append(_detect_boost_serialization_prerequisite(repo_root))
    execute_checks.append(_detect_pangolin_prerequisite(repo_root))

    vocabulary_archive = resolved.vocabulary.with_suffix(".txt.tar.gz")
    execute_checks.extend(
        [
            PrerequisiteCheck(
                label="Vocabulary archive",
                ready=vocabulary_archive.exists(),
                detail=str(vocabulary_archive),
            ),
            PrerequisiteCheck(
                label="Extracted vocabulary text",
                ready=resolved.vocabulary.exists(),
                detail=str(resolved.vocabulary),
            ),
            PrerequisiteCheck(
                label="Built monocular runner",
                ready=resolved.executable.exists(),
                detail=str(resolved.executable),
            ),
        ]
    )

    return MonocularBaselinePrerequisites(
        manifest_path=manifest_path,
        prepare_checks=prepare_checks,
        execute_checks=tuple(execute_checks),
    )


def render_monocular_baseline_prerequisite_report(
    prerequisites: MonocularBaselinePrerequisites,
) -> str:
    def render_check(check: PrerequisiteCheck) -> str:
        status = "ready" if check.ready else "missing"
        return f"- {check.label}: **{status}** (`{check.detail}`)"

    prepare_lines = "\n".join(
        render_check(check) for check in prerequisites.prepare_checks
    )
    execute_lines = "\n".join(
        render_check(check) for check in prerequisites.execute_checks
    )

    return f"""# Monocular baseline prerequisite check: {prerequisites.manifest_path.stem}

## Result

- Ready for `--prepare-only`: `{str(prerequisites.ready_for_prepare_only).lower()}`
- Ready for full execution: `{str(prerequisites.ready_for_execute).lower()}`

## Prepare-only prerequisites

{prepare_lines}

## Execution prerequisites

{execute_lines}
"""
