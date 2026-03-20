#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

manifest="${1:-manifests/tum_vi_room1_512_16_cam0_sanity.json}"

PYTHONPATH="${repo_root}/src" python3 \
  "${repo_root}/scripts/run_clean_room_public_tum_vi_sanity.py" \
  --manifest "${manifest}"
