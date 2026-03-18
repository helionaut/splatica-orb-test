#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

target_dir="${1:-${repo_root}/third_party/orbslam3/upstream}"
remote_url="https://github.com/UZ-SLAMLab/ORB_SLAM3.git"
commit_sha="4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4"

if [[ -e "${target_dir}" && ! -d "${target_dir}/.git" ]]; then
  printf 'Target exists but is not a git checkout: %s\n' "${target_dir}" >&2
  exit 1
fi

if [[ -d "${target_dir}/.git" ]]; then
  git -C "${target_dir}" fetch --tags origin
else
  git clone "${remote_url}" "${target_dir}"
fi

git -C "${target_dir}" checkout --detach "${commit_sha}"
printf 'Checked out ORB-SLAM3 %s at %s\n' "${commit_sha}" "${target_dir}"
