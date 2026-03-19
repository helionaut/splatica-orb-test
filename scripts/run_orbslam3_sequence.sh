#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

manifest=""
dry_run="false"
prepare_only="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest)
      manifest="$2"
      shift 2
      ;;
    --dry-run)
      dry_run="true"
      shift
      ;;
    --prepare-only)
      prepare_only="true"
      shift
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${manifest}" ]]; then
  printf 'Usage: %s --manifest <manifest.json> [--dry-run] [--prepare-only]\n' "${0##*/}" >&2
  exit 1
fi

if [[ "${dry_run}" == "true" && "${prepare_only}" == "true" ]]; then
  printf 'Use either --dry-run or --prepare-only, not both.\n' >&2
  exit 1
fi

if [[ "${dry_run}" == "true" ]]; then
  PYTHONPATH="${repo_root}/src" python3 "${repo_root}/scripts/run_smoke.py" --manifest "${manifest}"
  exit 0
fi

launch_mode="$(
  python3 - "${repo_root}" "${manifest}" <<'PY'
import json
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
manifest_text = sys.argv[2]
manifest_path = Path(manifest_text)
if not manifest_path.is_absolute():
    manifest_path = repo_root / manifest_path

raw = json.loads(manifest_path.read_text(encoding="utf-8"))
launch = raw.get("launch", {})
if isinstance(launch, dict):
    print(str(launch.get("mode", "")))
else:
    print("")
PY
)"

case "${launch_mode}" in
  calibration_config_smoke)
    if [[ "${prepare_only}" == "true" ]]; then
      printf 'The calibration config smoke mode does not support --prepare-only.\n' >&2
      exit 1
    fi

    PYTHONPATH="${repo_root}/src" python3 \
      "${repo_root}/scripts/run_calibration_config_smoke.py" \
      --manifest "${manifest}"
    ;;
  monocular_tum_vi|"")
    args=(
      "${repo_root}/scripts/run_monocular_baseline.py"
      --manifest "${manifest}"
    )

    if [[ "${prepare_only}" == "true" ]]; then
      args+=(--prepare-only)
    fi

    PYTHONPATH="${repo_root}/src" python3 "${args[@]}"
    ;;
  rgbd_tum)
    if [[ "${prepare_only}" == "true" ]]; then
      printf 'The RGB-D TUM mode does not support --prepare-only.\n' >&2
      exit 1
    fi

    PYTHONPATH="${repo_root}/src" python3 \
      "${repo_root}/scripts/run_rgbd_tum_baseline.py" \
      --manifest "${manifest}"
    ;;
  *)
    printf 'Unsupported launch.mode in manifest %s: %s\n' "${manifest}" "${launch_mode}" >&2
    exit 1
    ;;
esac
