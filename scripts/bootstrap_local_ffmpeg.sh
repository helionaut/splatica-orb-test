#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

release_tag="autobuild-2026-03-18-13-43"
archive_name="ffmpeg-n8.0.1-76-gfa4ee7ab3c-linux64-gpl-8.0.tar.xz"
archive_sha256="7abcbe33923bd1ca6d4e708859745a7b7e97fc55eac04f0a757d6c7ca02ac56e"
archive_url="https://github.com/BtbN/FFmpeg-Builds/releases/download/${release_tag}/${archive_name}"

packages_dir="${repo_root}/build/local-tools/ffmpeg-pkgs"
root_dir="${repo_root}/build/local-tools/ffmpeg-root"
archive_path="${packages_dir}/${archive_name}"

for tool in python3 sha256sum tar; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required bootstrap tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

mkdir -p "${packages_dir}"

if [[ ! -f "${archive_path}" ]]; then
  python3 - "${archive_url}" "${archive_path}" <<'PY'
from __future__ import annotations

import sys
import urllib.request

url = sys.argv[1]
destination = sys.argv[2]

with urllib.request.urlopen(url) as response, open(destination, "wb") as handle:
    while True:
        chunk = response.read(1024 * 1024)
        if not chunk:
            break
        handle.write(chunk)
PY
fi

actual_sha256="$(sha256sum "${archive_path}" | awk '{print $1}')"
if [[ "${actual_sha256}" != "${archive_sha256}" ]]; then
  printf 'ffmpeg archive checksum mismatch: expected %s got %s\n' \
    "${archive_sha256}" "${actual_sha256}" >&2
  exit 1
fi

rm -rf "${root_dir}"
mkdir -p "${root_dir}"
tar -xf "${archive_path}" --strip-components=1 -C "${root_dir}"

printf 'Bootstrapped local ffmpeg: %s\n' "${root_dir}/bin/ffmpeg"
printf 'Bootstrapped local ffprobe: %s\n' "${root_dir}/bin/ffprobe"
