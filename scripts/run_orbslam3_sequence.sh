#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

manifest=""
dry_run="false"

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
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${manifest}" ]]; then
  printf 'Usage: %s --manifest manifests/smoke-run.json --dry-run\n' "${0##*/}" >&2
  exit 1
fi

if [[ "${dry_run}" != "true" ]]; then
  printf 'Real ORB-SLAM3 execution is not wired yet. Use --dry-run until a baseline commit and dataset are pinned.\n' >&2
  exit 1
fi

PYTHONPATH="${repo_root}/src" python3 "${repo_root}/scripts/run_smoke.py" --manifest "${manifest}"
