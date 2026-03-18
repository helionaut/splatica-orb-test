#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

packages_dir="${repo_root}/build/local-tools/boost-pkgs"
root_dir="${repo_root}/build/local-tools/boost-root"
packages=(
  libboost-dev
  libboost1.83-dev
  libboost-serialization-dev
  libboost-serialization1.83-dev
  libboost-serialization1.83.0
)

for tool in apt dpkg-deb; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required bootstrap tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

mkdir -p "${packages_dir}"
rm -rf "${root_dir}"
mkdir -p "${root_dir}"

(
  cd "${packages_dir}"
  apt download "${packages[@]}"

  for deb_path in ./*.deb; do
    dpkg-deb -x "${deb_path}" "${root_dir}"
  done
)

printf 'Bootstrapped local Boost prefix: %s\n' "${root_dir}/usr"
printf 'Boost serialization header: %s\n' \
  "${root_dir}/usr/include/boost/serialization/serialization.hpp"
printf 'Boost serialization library: %s\n' \
  "${root_dir}/usr/lib/x86_64-linux-gnu/libboost_serialization.so"
