#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

checkout_dir="${1:-${repo_root}/third_party/orbslam3/upstream}"

for tool in cmake make; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required build tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

if [[ ! -x "${checkout_dir}/build.sh" ]]; then
  printf 'Missing upstream build.sh at %s. Run ./scripts/fetch_orbslam3_baseline.sh first.\n' "${checkout_dir}" >&2
  exit 1
fi

(
  cd "${checkout_dir}"
  ./build.sh
)

printf 'Built ORB-SLAM3 baseline in %s\n' "${checkout_dir}"
