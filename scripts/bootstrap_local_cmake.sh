#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

packages_dir="${repo_root}/build/local-tools/cmake-pkgs"
root_dir="${repo_root}/build/local-tools/cmake-root"
packages=(
  cmake
  cmake-data
  libarchive13t64
  librhash0
  libuv1t64
  libjsoncpp25
)

for tool in apt dpkg-deb; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required bootstrap tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

mkdir -p "${packages_dir}" "${root_dir}"

(
  cd "${packages_dir}"
  apt download "${packages[@]}"

  for package in "${packages[@]}"; do
    deb_path="$(ls -1t "${package}"_*.deb 2>/dev/null | head -n1)"
    if [[ -z "${deb_path}" ]]; then
      printf 'Failed to download package: %s\n' "${package}" >&2
      exit 1
    fi

    dpkg-deb -x "${deb_path}" "${root_dir}"
  done
)

printf 'Bootstrapped local cmake: %s\n' "${root_dir}/usr/bin/cmake"
printf 'Local cmake runtime libs: %s\n' "${root_dir}/usr/lib/x86_64-linux-gnu"
