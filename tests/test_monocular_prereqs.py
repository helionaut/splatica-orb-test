from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from splatica_orb_test.monocular_prereqs import (
    inspect_monocular_baseline_prerequisites,
    render_monocular_baseline_prerequisite_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "manifests/insta360_x3_lens10_monocular_baseline.json"
BASELINE_COMMIT = "4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4"
LENS10_ROOT = Path("datasets/user/insta360_x3_one_lens_baseline/lenses/10")


def write_file(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class MonocularPrerequisiteTests(unittest.TestCase):
    def test_reports_missing_inputs_and_native_packages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            write_file(
                repo_root / "manifests/insta360_x3_lens10_monocular_baseline.json",
                MANIFEST_PATH.read_text(encoding="utf-8"),
            )

            with mock.patch(
                "splatica_orb_test.monocular_prereqs.shutil.which",
                side_effect=lambda name: {
                    "make": "/usr/bin/make",
                    "pkg-config": "/usr/bin/pkg-config",
                }.get(name),
            ), mock.patch(
                "splatica_orb_test.monocular_prereqs.subprocess.run",
                return_value=mock.Mock(returncode=1, stdout="", stderr=""),
            ):
                prerequisites = inspect_monocular_baseline_prerequisites(
                    repo_root,
                    repo_root / "manifests/insta360_x3_lens10_monocular_baseline.json",
                )

        self.assertFalse(prerequisites.ready_for_prepare_only)
        self.assertFalse(prerequisites.ready_for_execute)
        self.assertEqual(prerequisites.prepare_checks[0].label, "Calibration JSON")
        self.assertFalse(prerequisites.prepare_checks[0].ready)
        self.assertEqual(prerequisites.execute_checks[0].label, "Baseline checkout")
        self.assertFalse(prerequisites.execute_checks[0].ready)
        self.assertIn("missing", render_monocular_baseline_prerequisite_report(prerequisites))

    def test_reports_execution_ready_when_all_assets_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            manifest_path = (
                repo_root / "manifests/insta360_x3_lens10_monocular_baseline.json"
            )
            write_file(manifest_path, MANIFEST_PATH.read_text(encoding="utf-8"))

            calibration_path = repo_root / LENS10_ROOT / "monocular_calibration.json"
            frame_index_path = repo_root / LENS10_ROOT / "frame_index.csv"
            write_file(calibration_path, json.dumps({"camera": {}}))
            write_file(frame_index_path, "timestamp_ns,source_path\n")
            write_file(repo_root / "third_party/orbslam3/upstream/.git", "gitdir")
            write_file(
                repo_root / "third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt.tar.gz",
                "archive",
            )
            write_file(repo_root / "third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt", "text")
            executable = (
                repo_root
                / "third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi"
            )
            write_file(executable, "binary")
            executable.chmod(0o755)

            def fake_run(cmd: list[str], **_kwargs: object) -> mock.Mock:
                if cmd[:4] == [
                    "git",
                    "-C",
                    str(repo_root / "third_party/orbslam3/upstream"),
                    "rev-parse",
                ]:
                    return mock.Mock(returncode=0, stdout=f"{BASELINE_COMMIT}\n", stderr="")
                if cmd[:2] == ["pkg-config", "--modversion"]:
                    package = cmd[2]
                    versions = {
                        "opencv4": "4.6.0\n",
                        "eigen3": "3.4.0\n",
                        "pangolin": "0.8\n",
                    }
                    if package in versions:
                        return mock.Mock(returncode=0, stdout=versions[package], stderr="")
                    return mock.Mock(returncode=1, stdout="", stderr="")
                raise AssertionError(f"Unexpected command: {cmd}")

            with mock.patch(
                "splatica_orb_test.monocular_prereqs.shutil.which",
                side_effect=lambda name: {
                    "cmake": "/tmp/cmake",
                    "make": "/usr/bin/make",
                    "pkg-config": "/usr/bin/pkg-config",
                }.get(name),
            ), mock.patch(
                "splatica_orb_test.monocular_prereqs.subprocess.run",
                side_effect=fake_run,
            ):
                prerequisites = inspect_monocular_baseline_prerequisites(
                    repo_root,
                    manifest_path,
                )

        self.assertTrue(prerequisites.ready_for_prepare_only)
        self.assertTrue(prerequisites.ready_for_execute)
        self.assertIn(
            "Ready for full execution: `true`",
            render_monocular_baseline_prerequisite_report(prerequisites),
        )

    def test_reports_archive_when_vocabulary_has_not_been_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            manifest_path = (
                repo_root / "manifests/insta360_x3_lens10_monocular_baseline.json"
            )
            write_file(manifest_path, MANIFEST_PATH.read_text(encoding="utf-8"))

            write_file(
                repo_root / LENS10_ROOT / "monocular_calibration.json",
                "{}",
            )
            write_file(
                repo_root / LENS10_ROOT / "frame_index.csv",
                "timestamp_ns,source_path\n",
            )
            write_file(repo_root / "third_party/orbslam3/upstream/.git", "gitdir")
            write_file(
                repo_root / "third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt.tar.gz",
                "archive",
            )

            def fake_run(cmd: list[str], **_kwargs: object) -> mock.Mock:
                if cmd[:2] == ["pkg-config", "--modversion"]:
                    return mock.Mock(returncode=0, stdout="1.0\n", stderr="")
                if cmd[:4] == [
                    "git",
                    "-C",
                    str(repo_root / "third_party/orbslam3/upstream"),
                    "rev-parse",
                ]:
                    return mock.Mock(returncode=0, stdout=f"{BASELINE_COMMIT}\n", stderr="")
                raise AssertionError(f"Unexpected command: {cmd}")

            with mock.patch(
                "splatica_orb_test.monocular_prereqs.shutil.which",
                side_effect=lambda _name: "/usr/bin/fake",
            ), mock.patch(
                "splatica_orb_test.monocular_prereqs.subprocess.run",
                side_effect=fake_run,
            ):
                prerequisites = inspect_monocular_baseline_prerequisites(
                    repo_root,
                    manifest_path,
                )

        self.assertFalse(prerequisites.ready_for_execute)
        report = render_monocular_baseline_prerequisite_report(prerequisites)
        self.assertIn("Vocabulary archive: **ready**", report)
        self.assertIn("Extracted vocabulary text: **missing**", report)

    def test_reports_repo_local_eigen_bootstrap_as_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            manifest_path = (
                repo_root / "manifests/insta360_x3_lens10_monocular_baseline.json"
            )
            write_file(manifest_path, MANIFEST_PATH.read_text(encoding="utf-8"))

            write_file(
                repo_root / LENS10_ROOT / "monocular_calibration.json",
                "{}",
            )
            write_file(
                repo_root / LENS10_ROOT / "frame_index.csv",
                "timestamp_ns,source_path\n",
            )
            write_file(repo_root / "third_party/orbslam3/upstream/.git", "gitdir")
            write_file(
                repo_root / "third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt.tar.gz",
                "archive",
            )
            write_file(repo_root / "third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt", "text")
            write_file(
                repo_root
                / "build/local-tools/eigen-root/usr/share/eigen3/cmake/Eigen3Config.cmake",
                "config",
            )
            executable = (
                repo_root
                / "third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi"
            )
            write_file(executable, "binary")
            executable.chmod(0o755)

            def fake_run(cmd: list[str], **_kwargs: object) -> mock.Mock:
                if cmd[:4] == [
                    "git",
                    "-C",
                    str(repo_root / "third_party/orbslam3/upstream"),
                    "rev-parse",
                ]:
                    return mock.Mock(returncode=0, stdout=f"{BASELINE_COMMIT}\n", stderr="")
                if cmd[:2] == ["pkg-config", "--modversion"]:
                    package = cmd[2]
                    versions = {
                        "opencv4": "4.6.0\n",
                        "pangolin": "0.8\n",
                    }
                    if package in versions:
                        return mock.Mock(returncode=0, stdout=versions[package], stderr="")
                    return mock.Mock(returncode=1, stdout="", stderr="")
                raise AssertionError(f"Unexpected command: {cmd}")

            with mock.patch(
                "splatica_orb_test.monocular_prereqs.shutil.which",
                side_effect=lambda name: {
                    "cmake": "/tmp/cmake",
                    "make": "/usr/bin/make",
                    "pkg-config": "/usr/bin/pkg-config",
                }.get(name),
            ), mock.patch(
                "splatica_orb_test.monocular_prereqs.subprocess.run",
                side_effect=fake_run,
            ):
                prerequisites = inspect_monocular_baseline_prerequisites(
                    repo_root,
                    manifest_path,
                )

        report = render_monocular_baseline_prerequisite_report(prerequisites)
        self.assertTrue(prerequisites.ready_for_execute)
        self.assertIn("Eigen3 development package: **ready**", report)
        self.assertIn("repo-local bootstrap", report)
