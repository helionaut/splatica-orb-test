from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.monocular_runtime_progress import (
    build_monocular_progress_payload,
    summarize_monocular_runtime_log,
    write_progress_snapshot,
)


class MonocularRuntimeProgressTests(unittest.TestCase):
    def test_summarize_log_tracks_latest_frames_and_shutdown(self) -> None:
        summary = summarize_monocular_runtime_log(
            [
                "HEL-68 diagnostic: frame 0 TrackMonocular start timestamp=1.0",
                "HEL-68 diagnostic: frame 0 TrackMonocular completed",
                "HEL-68 diagnostic: frame 1 TrackMonocular start timestamp=2.0",
                "HEL-68 diagnostic: frame 1 TrackMonocular completed",
                "HEL-63 diagnostic: entering SLAM shutdown",
                "HEL-63 diagnostic: SLAM shutdown completed",
            ],
            total_frames=20,
        )

        self.assertEqual(summary.completed_frames, 2)
        self.assertEqual(summary.latest_started_frame, 1)
        self.assertEqual(summary.latest_completed_frame, 1)
        self.assertEqual(summary.current_step, "SLAM shutdown completed")
        self.assertTrue(summary.shutdown_started)
        self.assertTrue(summary.shutdown_completed)

    def test_build_payload_uses_frame_progress(self) -> None:
        summary = summarize_monocular_runtime_log(
            [
                "HEL-68 diagnostic: frame 33 TrackMonocular start timestamp=10.0",
                "HEL-68 diagnostic: frame 33 TrackMonocular completed",
            ],
            total_frames=100,
        )

        payload = build_monocular_progress_payload(
            issue="HEL-72",
            status="in_progress",
            summary=summary,
            artifacts={"log_path": "logs/out/example.log"},
            metrics={"latest_completed_frame": 33},
            experiment={"changed_variable": "enable ASan"},
        )

        self.assertEqual(payload["progress_percent"], 34)
        self.assertEqual(payload["completed"], 34)
        self.assertEqual(payload["unit"], "frames")
        self.assertEqual(payload["experiment"]["changed_variable"], "enable ASan")

    def test_write_progress_snapshot_appends_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact = Path(tmpdir) / "HEL-72.jsonl"
            write_progress_snapshot(artifact, {"status": "in_progress", "completed": 1})
            write_progress_snapshot(artifact, {"status": "in_progress", "completed": 2})

            lines = artifact.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[-1])["completed"], 2)
