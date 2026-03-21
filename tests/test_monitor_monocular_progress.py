from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts/monitor_monocular_progress.py"


spec = importlib.util.spec_from_file_location(
    "monitor_monocular_progress",
    MODULE_PATH,
)
assert spec is not None and spec.loader is not None
monitor_monocular_progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor_monocular_progress)


class MonitorMonocularProgressTests(unittest.TestCase):
    def test_write_progress_outputs_updates_jsonl_and_primary_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "HEL-72.jsonl"
            primary_artifact_path = Path(tmpdir) / "HEL-72.json"
            payload = {
                "status": "in_progress",
                "completed": 2005,
                "total": 2821,
                "unit": "frames",
            }

            monitor_monocular_progress.write_progress_outputs(
                artifact_path,
                payload,
                primary_artifact_path=primary_artifact_path,
            )

            jsonl_lines = artifact_path.read_text(encoding="utf-8").splitlines()
            primary_payload = json.loads(
                primary_artifact_path.read_text(encoding="utf-8")
            )

        self.assertEqual(len(jsonl_lines), 1)
        self.assertEqual(json.loads(jsonl_lines[0])["completed"], 2005)
        self.assertEqual(primary_payload["completed"], 2005)
