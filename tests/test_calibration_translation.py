from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from splatica_orb_test.calibration_translation import (
    load_calibration_config_smoke_manifest,
    load_shareable_rig_calibration,
    render_shareable_monocular_settings_yaml,
    run_calibration_config_smoke,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class ShareableRigCalibrationTests(unittest.TestCase):
    def test_loads_checked_in_shareable_bundle(self) -> None:
        calibration = load_shareable_rig_calibration(
            REPO_ROOT / "configs/calibration/insta360_x3_shareable_rig.json"
        )

        self.assertEqual(calibration.source_camera_model.lower(), "kannalabrandt4")
        self.assertEqual(calibration.image_width, 2880)
        self.assertEqual(calibration.image_height, 2880)
        self.assertEqual(sorted(calibration.cameras.keys()), ["00", "10"])
        self.assertEqual(calibration.reference_camera, "10")

    def test_renders_monocular_yaml_from_kannala_brandt4_source(self) -> None:
        calibration = load_shareable_rig_calibration(
            REPO_ROOT / "configs/calibration/insta360_x3_shareable_rig.json"
        )

        settings = render_shareable_monocular_settings_yaml(
            calibration,
            color_order="RGB",
            fps=30,
            lens_id="10",
            source_label="configs/calibration/insta360_x3_shareable_rig.json",
        )

        self.assertIn('Camera.type: "KannalaBrandt8"', settings)
        self.assertIn("Camera.width: 2880", settings)
        self.assertIn("Camera.height: 2880", settings)
        self.assertIn("Camera.fps: 30.0", settings)
        self.assertIn("Camera1.fx: 781.598232980262", settings)
        self.assertIn("Camera1.k4: -0.002161607489", settings)
        self.assertIn("Smoke/profile override Camera.RGB: 1 (RGB)", settings)

    def test_requires_explicit_monocular_overrides_instead_of_guessing(self) -> None:
        calibration = load_shareable_rig_calibration(
            REPO_ROOT / "configs/calibration/insta360_x3_shareable_rig.json"
        )

        with self.assertRaisesRegex(
            ValueError, "Missing required monocular overrides"
        ):
            render_shareable_monocular_settings_yaml(
                calibration,
                color_order="RGB",
                fps=None,
                lens_id="10",
            )


class CalibrationConfigSmokeManifestTests(unittest.TestCase):
    def test_loads_checked_in_calibration_smoke_manifest(self) -> None:
        manifest = load_calibration_config_smoke_manifest(
            REPO_ROOT / "manifests/insta360_x3_shareable_calibration_smoke.json"
        )

        self.assertEqual(
            manifest.calibration_path,
            "configs/calibration/insta360_x3_shareable_rig.json",
        )
        self.assertEqual(manifest.launch_mode, "calibration_config_smoke")
        self.assertEqual(len(manifest.profiles), 2)


class CalibrationConfigSmokeRunnerTests(unittest.TestCase):
    def test_generates_settings_and_reports_without_external_dependencies(self) -> None:
        manifest = load_calibration_config_smoke_manifest(
            REPO_ROOT / "manifests/insta360_x3_shareable_calibration_smoke.json"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)

            calibration_dir = tmp_root / "configs" / "calibration"
            calibration_dir.mkdir(parents=True)
            calibration_source = (
                REPO_ROOT / "configs/calibration/insta360_x3_shareable_rig.json"
            )
            calibration_target = calibration_dir / calibration_source.name
            calibration_target.write_text(
                calibration_source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            run = run_calibration_config_smoke(tmp_root, manifest)

            self.assertEqual(len(run.outputs), 2)
            self.assertTrue(
                (tmp_root / "configs/orbslam3/insta360_x3_lens10_monocular.yaml").exists()
            )
            self.assertTrue(
                (tmp_root / "configs/orbslam3/insta360_x3_lens00_monocular.yaml").exists()
            )
            self.assertTrue((tmp_root / "logs/out/insta360_x3_shareable_calibration_smoke.log").exists())
            self.assertTrue((tmp_root / "reports/out/insta360_x3_shareable_calibration_smoke.md").exists())
            self.assertIn("Missing camera_to_imu", "\n".join(run.blockers))

