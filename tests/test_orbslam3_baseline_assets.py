from __future__ import annotations

from pathlib import Path
import tarfile
import tempfile
import unittest

from splatica_orb_test.orbslam3_baseline_assets import (
    ensure_orbslam3_vocabulary_text,
    resolve_orbslam3_vocabulary_paths,
)


def write_archive(path: Path, *, filename: str = "ORBvoc.txt", text: str = "voc") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, mode="w:gz") as archive:
        temp_root = path.parent / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        source = temp_root / filename
        source.write_text(text, encoding="utf-8")
        archive.add(source, arcname=filename)


class Orbslam3BaselineAssetTests(unittest.TestCase):
    def test_extracts_vocabulary_text_from_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            checkout_dir = Path(tmpdir) / "upstream"
            archive_path, output_path = resolve_orbslam3_vocabulary_paths(checkout_dir)
            write_archive(archive_path, text="hello vocabulary")

            prepared_path = ensure_orbslam3_vocabulary_text(checkout_dir)
            extracted_text = output_path.read_text(encoding="utf-8")

            self.assertEqual(prepared_path, output_path)
            self.assertTrue(output_path.exists())
            self.assertEqual(extracted_text, "hello vocabulary")

    def test_is_idempotent_when_vocabulary_text_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            checkout_dir = Path(tmpdir) / "upstream"
            archive_path, output_path = resolve_orbslam3_vocabulary_paths(checkout_dir)
            write_archive(archive_path, text="archive text")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("existing text", encoding="utf-8")

            prepared_path = ensure_orbslam3_vocabulary_text(checkout_dir)
            extracted_text = output_path.read_text(encoding="utf-8")

            self.assertEqual(prepared_path, output_path)
            self.assertEqual(extracted_text, "existing text")

    def test_requires_orbvoc_member_in_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            checkout_dir = Path(tmpdir) / "upstream"
            archive_path, _output_path = resolve_orbslam3_vocabulary_paths(checkout_dir)
            write_archive(archive_path, filename="wrong-name.txt")

            with self.assertRaisesRegex(ValueError, "did not contain ORBvoc.txt"):
                ensure_orbslam3_vocabulary_text(checkout_dir)
