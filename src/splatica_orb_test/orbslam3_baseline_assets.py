from __future__ import annotations

from pathlib import Path
import tarfile


def resolve_orbslam3_vocabulary_paths(checkout_dir: Path) -> tuple[Path, Path]:
    vocabulary_dir = checkout_dir / "Vocabulary"
    return (
        vocabulary_dir / "ORBvoc.txt.tar.gz",
        vocabulary_dir / "ORBvoc.txt",
    )


def ensure_orbslam3_vocabulary_text(checkout_dir: Path) -> Path:
    archive_path, output_path = resolve_orbslam3_vocabulary_paths(checkout_dir)
    if output_path.exists():
        return output_path

    if not archive_path.exists():
        raise FileNotFoundError(f"Missing ORB-SLAM3 vocabulary archive: {archive_path}")

    with tarfile.open(archive_path, mode="r:gz") as archive:
        member = next(
            (
                candidate
                for candidate in archive.getmembers()
                if candidate.isfile() and Path(candidate.name).name == "ORBvoc.txt"
            ),
            None,
        )
        if member is None:
            raise ValueError(
                f"ORB-SLAM3 vocabulary archive did not contain ORBvoc.txt: {archive_path}"
            )

        extracted = archive.extractfile(member)
        if extracted is None:
            raise ValueError(f"Failed to read ORBvoc.txt from archive: {archive_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(extracted.read())

    return output_path
