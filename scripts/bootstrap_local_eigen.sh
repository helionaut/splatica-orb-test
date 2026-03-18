#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

packages_dir="${repo_root}/build/local-tools/eigen-pkgs"
root_dir="${repo_root}/build/local-tools/eigen-root"

for tool in apt dpkg-deb; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required bootstrap tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

mkdir -p "${packages_dir}" "${root_dir}"

(
  cd "${packages_dir}"
  apt download libeigen3-dev

  deb_path="$(ls -1t libeigen3-dev_*.deb 2>/dev/null | head -n1)"
  if [[ -z "${deb_path}" ]]; then
    printf 'Failed to download package: libeigen3-dev\n' >&2
    exit 1
  fi

  dpkg-deb -x "${deb_path}" "${root_dir}"
)

printf 'Bootstrapped local Eigen3 prefix: %s\n' "${root_dir}/usr"
printf 'Eigen3 CMake config: %s\n' "${root_dir}/usr/share/eigen3/cmake/Eigen3Config.cmake"
