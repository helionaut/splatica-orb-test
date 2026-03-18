from __future__ import annotations

from pathlib import Path
import unittest

from splatica_orb_test.monocular_baseline import (
    ORB_SLAM3_UPSTREAM_MASTER,
    ORB_SLAM3_V1_0_RELEASE,
    load_monocular_baseline_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
LENS10_CALIBRATION_PATH = (
    "datasets/user/insta360_x3_one_lens_baseline/lenses/10/monocular_calibration.json"
)
LENS10_FRAME_INDEX_PATH = (
    "datasets/user/insta360_x3_one_lens_baseline/lenses/10/frame_index.csv"
)


class CandidateEvaluationManifestTests(unittest.TestCase):
    def test_candidate_manifests_pin_expected_sources(self) -> None:
        manifests = {
            "selected": load_monocular_baseline_manifest(
                REPO_ROOT / "manifests/insta360_x3_lens10_monocular_baseline.json"
            ),
            "upstream_v1_0_release": load_monocular_baseline_manifest(
                REPO_ROOT
                / "manifests/insta360_x3_lens10_upstream_v1_0_release_evaluation.json"
            ),
            "openmavis_master": load_monocular_baseline_manifest(
                REPO_ROOT
                / "manifests/insta360_x3_lens10_openmavis_master_evaluation.json"
            ),
        }

        self.assertEqual(
            manifests["selected"].repo_url, "https://github.com/UZ-SLAMLab/ORB_SLAM3"
        )
        self.assertEqual(
            manifests["selected"].baseline_commit, ORB_SLAM3_UPSTREAM_MASTER
        )
        self.assertEqual(
            manifests["upstream_v1_0_release"].baseline_commit, ORB_SLAM3_V1_0_RELEASE
        )
        self.assertEqual(
            manifests["openmavis_master"].repo_url,
            "https://github.com/MAVIS-SLAM/OpenMAVIS",
        )
        self.assertEqual(
            manifests["openmavis_master"].baseline_commit,
            "b13b1c20e84efa4bb63564e26308541af70d03f2",
        )

    def test_candidate_manifests_use_identical_private_inputs(self) -> None:
        manifests = [
            load_monocular_baseline_manifest(
                REPO_ROOT / "manifests/insta360_x3_lens10_monocular_baseline.json"
            ),
            load_monocular_baseline_manifest(
                REPO_ROOT
                / "manifests/insta360_x3_lens10_upstream_v1_0_release_evaluation.json"
            ),
            load_monocular_baseline_manifest(
                REPO_ROOT
                / "manifests/insta360_x3_lens10_openmavis_master_evaluation.json"
            ),
        ]

        self.assertEqual(
            {manifest.calibration_path for manifest in manifests},
            {LENS10_CALIBRATION_PATH},
        )
        self.assertEqual(
            {manifest.frame_index_path for manifest in manifests},
            {LENS10_FRAME_INDEX_PATH},
        )
        self.assertEqual(
            {manifest.executable_path for manifest in manifests},
            {"Examples/Monocular/mono_tum_vi"},
        )
        self.assertEqual(
            len({manifest.log_path for manifest in manifests}),
            len(manifests),
        )
        self.assertEqual(
            len({manifest.report_path for manifest in manifests}),
            len(manifests),
        )
