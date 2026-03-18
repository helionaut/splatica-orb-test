from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from splatica_orb_test.local_tooling import (
    resolve_cmake_tool,
    resolve_repo_local_cmake_paths,
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
