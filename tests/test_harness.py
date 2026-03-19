from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.harness import (
    PRODUCTION_VERIFICATION_COMMAND,
    REPOSITORY_LAYOUT,
    TEST_FIRST_EXPECTATION,
    build_smoke_command,
    load_smoke_manifest,
    render_build_plan,
    validate_layout,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class LoadSmokeManifestTests(unittest.TestCase):
    def test_loads_the_checked_in_manifest(self) -> None:
        manifest = load_smoke_manifest(REPO_ROOT / "manifests/smoke-run.json")

        self.assertEqual(manifest.sequence_name, "fixture-dry-run")
        self.assertEqual(
            manifest.settings_path, "configs/orbslam3/smoke-placeholder.yaml"
        )

    def test_requires_top_level_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text(json.dumps({"baseline": {}}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Missing manifest section"):
                load_smoke_manifest(manifest_path)


class HarnessContractTests(unittest.TestCase):
    def test_repository_layout_is_present(self) -> None:
        self.assertEqual(validate_layout(REPO_ROOT), [])

    def test_rendered_plan_calls_out_commands_and_testing_policy(self) -> None:
        manifest = load_smoke_manifest(REPO_ROOT / "manifests/smoke-run.json")
        plan = render_build_plan(manifest)

        self.assertIn("make build", plan)
        self.assertIn("make smoke", plan)
        self.assertIn(PRODUCTION_VERIFICATION_COMMAND, plan)
        self.assertIn(TEST_FIRST_EXPECTATION, plan)

    def test_smoke_command_uses_the_canonical_launcher(self) -> None:
        self.assertEqual(
            build_smoke_command("manifests/smoke-run.json"),
            "./scripts/run_orbslam3_sequence.sh --manifest manifests/smoke-run.json --dry-run",
        )

    def test_layout_declares_expected_work_areas(self) -> None:
        self.assertEqual(
            [area.path for area in REPOSITORY_LAYOUT],
            [
                "configs/calibration",
                "configs/orbslam3",
                "datasets/fixtures",
                "datasets/public",
                "datasets/user",
                "logs/out",
                "reports/out",
                "scripts",
                "tests",
                "third_party/orbslam3",
            ],
        )
