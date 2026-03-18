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

args=(
  "${repo_root}/scripts/run_monocular_baseline.py"
  --manifest "${manifest}"
)

if [[ "${prepare_only}" == "true" ]]; then
  args+=(--prepare-only)
fi

PYTHONPATH="${repo_root}/src" python3 "${args[@]}"
