from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from splatica_orb_test.local_tooling import (
    resolve_boost_prefix,
    resolve_cmake_tool,
    resolve_eigen3_prefix,
    resolve_ffmpeg_tool,
    resolve_ffprobe_tool,
    resolve_opencv_prefix,
    resolve_pangolin_prefix,
    resolve_repo_local_boost_paths,
    resolve_repo_local_cmake_paths,
    resolve_repo_local_eigen3_paths,
    resolve_repo_local_ffmpeg_paths,
    resolve_repo_local_opencv_paths,
    resolve_repo_local_pangolin_paths,
)


class LocalToolingTests(unittest.TestCase):
    def test_prefers_path_cmake_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            with mock.patch(
                "splatica_orb_test.local_tooling.shutil.which",
                return_value="/usr/bin/cmake",
            ):
                resolved = resolve_cmake_tool(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.path, Path("/usr/bin/cmake"))
        self.assertFalse(resolved.uses_repo_local_runtime)

    def test_uses_repo_local_cmake_when_path_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            local_bin, local_lib = resolve_repo_local_cmake_paths(repo_root)
            local_bin.parent.mkdir(parents=True, exist_ok=True)
            local_bin.write_text("binary", encoding="utf-8")
            local_bin.chmod(0o755)
            local_lib.mkdir(parents=True, exist_ok=True)

            with mock.patch(
                "splatica_orb_test.local_tooling.shutil.which",
                return_value=None,
            ):
                resolved = resolve_cmake_tool(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.path, local_bin)
        self.assertTrue(resolved.uses_repo_local_runtime)
        self.assertEqual(resolved.runtime_library_path, local_lib)

    def test_returns_none_when_no_cmake_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            with mock.patch(
                "splatica_orb_test.local_tooling.shutil.which",
                return_value=None,
            ):
                resolved = resolve_cmake_tool(repo_root)

        self.assertIsNone(resolved)

    def test_prefers_path_ffmpeg_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            with mock.patch(
                "splatica_orb_test.local_tooling.shutil.which",
                side_effect=lambda name: {
                    "ffmpeg": "/usr/bin/ffmpeg",
                }.get(name),
            ):
                resolved = resolve_ffmpeg_tool(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.path, Path("/usr/bin/ffmpeg"))
        self.assertFalse(resolved.uses_repo_local_runtime)

    def test_uses_repo_local_ffmpeg_when_path_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            local_ffmpeg, _local_ffprobe = resolve_repo_local_ffmpeg_paths(repo_root)
            local_ffmpeg.parent.mkdir(parents=True, exist_ok=True)
            local_ffmpeg.write_text("binary", encoding="utf-8")
            local_ffmpeg.chmod(0o755)

            with mock.patch(
                "splatica_orb_test.local_tooling.shutil.which",
                return_value=None,
            ):
                resolved = resolve_ffmpeg_tool(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.path, local_ffmpeg)
        self.assertFalse(resolved.uses_repo_local_runtime)
        self.assertIn("repo-local bootstrap", resolved.detail)

    def test_prefers_path_ffprobe_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            with mock.patch(
                "splatica_orb_test.local_tooling.shutil.which",
                side_effect=lambda name: {
                    "ffprobe": "/usr/bin/ffprobe",
                }.get(name),
            ):
                resolved = resolve_ffprobe_tool(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.path, Path("/usr/bin/ffprobe"))
        self.assertFalse(resolved.uses_repo_local_runtime)

    def test_uses_repo_local_ffprobe_when_path_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _local_ffmpeg, local_ffprobe = resolve_repo_local_ffmpeg_paths(repo_root)
            local_ffprobe.parent.mkdir(parents=True, exist_ok=True)
            local_ffprobe.write_text("binary", encoding="utf-8")
            local_ffprobe.chmod(0o755)

            with mock.patch(
                "splatica_orb_test.local_tooling.shutil.which",
                return_value=None,
            ):
                resolved = resolve_ffprobe_tool(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.path, local_ffprobe)
        self.assertFalse(resolved.uses_repo_local_runtime)
        self.assertIn("repo-local bootstrap", resolved.detail)

    def test_returns_none_when_no_ffmpeg_or_ffprobe_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            with mock.patch(
                "splatica_orb_test.local_tooling.shutil.which",
                return_value=None,
            ):
                resolved_ffmpeg = resolve_ffmpeg_tool(repo_root)
                resolved_ffprobe = resolve_ffprobe_tool(repo_root)

        self.assertIsNone(resolved_ffmpeg)
        self.assertIsNone(resolved_ffprobe)

    def test_detects_repo_local_eigen_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_path, pkgconfig_path = resolve_repo_local_eigen3_paths(repo_root)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("config", encoding="utf-8")
            pkgconfig_path.parent.mkdir(parents=True, exist_ok=True)
            pkgconfig_path.write_text("pc", encoding="utf-8")

            resolved = resolve_eigen3_prefix(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.prefix, repo_root / "build/local-tools/eigen-root/usr")

    def test_returns_none_when_repo_local_eigen_prefix_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            resolved = resolve_eigen3_prefix(repo_root)

        self.assertIsNone(resolved)

    def test_detects_repo_local_opencv_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_path, pkgconfig_path, _library_path = resolve_repo_local_opencv_paths(
                repo_root
            )
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("config", encoding="utf-8")
            pkgconfig_path.parent.mkdir(parents=True, exist_ok=True)
            pkgconfig_path.write_text("pc", encoding="utf-8")

            resolved = resolve_opencv_prefix(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.prefix, repo_root / "build/local-tools/opencv-root/usr")

    def test_returns_none_when_repo_local_opencv_prefix_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            resolved = resolve_opencv_prefix(repo_root)

        self.assertIsNone(resolved)

    def test_detects_repo_local_boost_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            header_path, library_path = resolve_repo_local_boost_paths(repo_root)
            header_path.parent.mkdir(parents=True, exist_ok=True)
            header_path.write_text("header", encoding="utf-8")
            library_path.mkdir(parents=True, exist_ok=True)
            (library_path / "libboost_serialization.so").write_text(
                "library",
                encoding="utf-8",
            )

            resolved = resolve_boost_prefix(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.prefix, repo_root / "build/local-tools/boost-root/usr")

    def test_returns_none_when_repo_local_boost_prefix_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            resolved = resolve_boost_prefix(repo_root)

        self.assertIsNone(resolved)

    def test_detects_repo_local_pangolin_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_path, pkgconfig_path = resolve_repo_local_pangolin_paths(repo_root)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("config", encoding="utf-8")
            pkgconfig_path.parent.mkdir(parents=True, exist_ok=True)
            pkgconfig_path.write_text("pc", encoding="utf-8")

            resolved = resolve_pangolin_prefix(repo_root)

        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(
            resolved.prefix,
            repo_root / "build/local-tools/pangolin-root/usr/local",
        )

    def test_returns_none_when_repo_local_pangolin_prefix_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            resolved = resolve_pangolin_prefix(repo_root)

        self.assertIsNone(resolved)
