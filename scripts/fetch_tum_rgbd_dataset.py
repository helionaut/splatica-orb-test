#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import tarfile
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from splatica_orb_test.rgbd_tum_baseline import (  # noqa: E402
    load_rgbd_tum_baseline_manifest,
    resolve_rgbd_tum_baseline_paths,
)


CHUNK_SIZE = 1024 * 1024


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    resolved_destination = destination.resolve()
    for member in archive.getmembers():
        member_path = (destination / member.name).resolve()
        if not is_within(member_path, resolved_destination):
            raise ValueError(
                f"Archive member escaped extraction root: {member.name}"
            )
    archive.extractall(destination)


def dataset_is_ready(dataset_root: Path) -> bool:
    return (
        (dataset_root / "rgb").is_dir()
        and (dataset_root / "depth").is_dir()
        and (dataset_root / "groundtruth.txt").is_file()
    )


def download_archive(url: str, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = archive_path.with_suffix(f"{archive_path.suffix}.partial")
    if partial_path.exists():
        partial_path.unlink()

    with urlopen(url) as response, partial_path.open("wb") as handle:
        total_text = response.headers.get("Content-Length")
        total_bytes = int(total_text) if total_text else 0
        downloaded = 0
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            handle.write(chunk)
            downloaded += len(chunk)
            if total_bytes:
                percent = downloaded * 100.0 / total_bytes
                print(
                    f"Downloaded {downloaded}/{total_bytes} bytes ({percent:.1f}%)",
                    flush=True,
                )
            else:
                print(f"Downloaded {downloaded} bytes", flush=True)

    partial_path.replace(archive_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest = load_rgbd_tum_baseline_manifest(resolve_repo_path(args.manifest))
    resolved = resolve_rgbd_tum_baseline_paths(REPO_ROOT, manifest)

    if dataset_is_ready(resolved.dataset_root):
        print(f"Dataset already prepared: {resolved.dataset_root}")
        return 0

    if not resolved.archive.exists():
        print(f"Downloading {manifest.archive_url} -> {resolved.archive}")
        download_archive(manifest.archive_url, resolved.archive)
    else:
        print(f"Using existing archive: {resolved.archive}")

    staging_root = (
        resolved.dataset_root.parent / f".{resolved.dataset_root.name}.extracting"
    )
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(resolved.archive, mode="r:gz") as archive:
            print(f"Extracting {resolved.archive} -> {staging_root}")
            safe_extract(archive, staging_root)

        extracted_root = staging_root / manifest.dataset_name
        if not extracted_root.exists():
            raise FileNotFoundError(
                f"Expected extracted dataset root at {extracted_root}"
            )

        if resolved.dataset_root.exists():
            shutil.rmtree(resolved.dataset_root)
        extracted_root.replace(resolved.dataset_root)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    if not dataset_is_ready(resolved.dataset_root):
        raise SystemExit(
            f"Dataset extraction was incomplete at {resolved.dataset_root}"
        )

    print(f"Prepared dataset: {resolved.dataset_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
