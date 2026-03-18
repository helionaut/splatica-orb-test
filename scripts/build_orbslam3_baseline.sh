#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

checkout_dir="${1:-${repo_root}/third_party/orbslam3/upstream}"
local_cmake_bin="${repo_root}/build/local-tools/cmake-root/usr/bin/cmake"
local_cmake_lib="${repo_root}/build/local-tools/cmake-root/usr/lib/x86_64-linux-gnu"
cmake_bin=""

for tool in make; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required build tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

if command -v cmake >/dev/null 2>&1; then
  cmake_bin="$(command -v cmake)"
elif [[ -x "${local_cmake_bin}" ]]; then
  cmake_bin="${local_cmake_bin}"
else
  printf 'Missing required build tool: cmake\n' >&2
  printf 'Install cmake on PATH or run ./scripts/bootstrap_local_cmake.sh first.\n' >&2
  exit 1
fi

if [[ ! -x "${checkout_dir}/build.sh" ]]; then
  printf 'Missing upstream build.sh at %s. Run ./scripts/fetch_orbslam3_baseline.sh first.\n' "${checkout_dir}" >&2
  exit 1
fi

(
  cd "${checkout_dir}"
  if [[ "${cmake_bin}" == "${local_cmake_bin}" ]]; then
    export PATH="$(dirname "${local_cmake_bin}"):${PATH}"
    export LD_LIBRARY_PATH="${local_cmake_lib}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  fi
  ./build.sh
)

printf 'Built ORB-SLAM3 baseline in %s\n' "${checkout_dir}"
