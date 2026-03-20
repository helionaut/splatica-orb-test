#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

packages_dir="${repo_root}/build/local-tools/opencv-pkgs"
root_dir="${repo_root}/build/local-tools/opencv-root"
manifest_path="${root_dir}/bootstrap-manifest.txt"
progress_artifact="${ORB_SLAM3_PROGRESS_ARTIFACT:-}"
progress_issue_id="${ORB_SLAM3_PROGRESS_ISSUE_ID:-}"
progress_heartbeat_seconds="${ORB_SLAM3_BOOTSTRAP_PROGRESS_HEARTBEAT_SECONDS:-60}"
progress_total=4
progress_heartbeat_pid=""
bootstrap_started=0
bootstrap_succeeded=0
seed_packages=(
  libopencv-dev
  libopencv-calib3d-dev
  libopencv-contrib-dev
  libopencv-core-dev
  libopencv-dnn-dev
  libopencv-features2d-dev
  libopencv-flann-dev
  libopencv-highgui-dev
  libopencv-imgcodecs-dev
  libopencv-imgproc-dev
  libopencv-ml-dev
  libopencv-objdetect-dev
  libopencv-photo-dev
  libopencv-shape-dev
  libopencv-stitching-dev
  libopencv-superres-dev
  libopencv-video-dev
  libopencv-videoio-dev
  libopencv-videostab-dev
  libopencv-viz-dev
  libopencv-calib3d406t64
  libopencv-contrib406t64
  libopencv-core406t64
  libopencv-dnn406t64
  libopencv-features2d406t64
  libopencv-flann406t64
  libopencv-highgui406t64
  libopencv-imgcodecs406t64
  libopencv-imgproc406t64
  libopencv-ml406t64
  libopencv-objdetect406t64
  libopencv-photo406t64
  libopencv-shape406t64
  libopencv-stitching406t64
  libopencv-superres406t64
  libopencv-video406t64
  libopencv-videoio406t64
  libopencv-videostab406t64
  libopencv-viz406t64
  libtbb-dev
  zlib1g-dev
  libavcodec-dev
  libavformat-dev
  libdc1394-dev
  libgphoto2-dev
  libjpeg-turbo8-dev
  libopenexr-dev
  libpng-dev
  libraw1394-dev
  libswscale-dev
  libtiff-dev
  libgdcm-dev
)

for tool in apt apt-cache dpkg-deb; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required bootstrap tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

if [[ -n "${progress_artifact}" && "${progress_artifact}" != /* ]]; then
  progress_artifact="${repo_root}/${progress_artifact}"
fi

if [[ ! "${progress_heartbeat_seconds}" =~ ^[1-9][0-9]*$ ]]; then
  printf 'ORB_SLAM3_BOOTSTRAP_PROGRESS_HEARTBEAT_SECONDS must be a positive integer, got: %s\n' \
    "${progress_heartbeat_seconds}" >&2
  exit 1
fi

write_progress_artifact() {
  local status="$1"
  local current_step="$2"
  local completed="$3"

  if [[ -z "${progress_artifact}" ]]; then
    return 0
  fi

  python3 - "${repo_root}" "${progress_artifact}" "${progress_issue_id}" "${status}" "${current_step}" "${completed}" "${progress_total}" "${root_dir}" "${manifest_path}" <<'PY'
import json
import sys
from pathlib import Path

repo_root_text, artifact_text, issue_id, status, current_step, completed_text, total_text, root_dir_text, manifest_path_text = sys.argv[1:]

repo_root = Path(repo_root_text)
artifact_path = Path(artifact_text)
completed = int(completed_text)
total = int(total_text)
progress_percent = round((max(0, min(completed, total)) / total) * 100) if total else 100

def rel(path_text: str) -> str:
    path = Path(path_text)
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except Exception:
        return str(path)

payload = {
    "issue": issue_id,
    "status": status,
    "current_step": current_step,
    "completed": completed,
    "total": total,
    "unit": "phases",
    "progress_percent": progress_percent,
    "eta_seconds": None,
    "metrics": {
        "bootstrap": "opencv",
        "install_prefix": rel(f"{root_dir_text}/usr"),
    },
    "artifacts": [
        {
            "label": "opencv_manifest",
            "path": rel(manifest_path_text),
        },
        {
            "label": "opencv_cmake_config",
            "path": rel(f"{root_dir_text}/usr/lib/x86_64-linux-gnu/cmake/opencv4/OpenCVConfig.cmake"),
        },
        {
            "label": "opencv_pkgconfig",
            "path": rel(f"{root_dir_text}/usr/lib/x86_64-linux-gnu/pkgconfig/opencv4.pc"),
        },
    ],
}
artifact_path.parent.mkdir(parents=True, exist_ok=True)
artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

start_progress_heartbeat() {
  local status="$1"
  local current_step="$2"
  local completed="$3"

  stop_progress_heartbeat
  if [[ -z "${progress_artifact}" ]]; then
    return 0
  fi

  (
    while true; do
      sleep "${progress_heartbeat_seconds}"
      write_progress_artifact "${status}" "${current_step}" "${completed}"
    done
  ) &
  progress_heartbeat_pid=$!
}

stop_progress_heartbeat() {
  if [[ -n "${progress_heartbeat_pid}" ]]; then
    kill "${progress_heartbeat_pid}" >/dev/null 2>&1 || true
    wait "${progress_heartbeat_pid}" >/dev/null 2>&1 || true
    progress_heartbeat_pid=""
  fi
}

cleanup() {
  local exit_code=$?

  stop_progress_heartbeat
  if [[ "${bootstrap_started}" == "1" && "${bootstrap_succeeded}" != "1" ]]; then
    write_progress_artifact "failed" "OpenCV bootstrap failed" 0
  fi
  exit "${exit_code}"
}

trap cleanup EXIT

mkdir -p "${packages_dir}"
rm -rf "${root_dir}"
mkdir -p "${root_dir}"
bootstrap_started=1
write_progress_artifact "in_progress" "Resolving OpenCV package closure" 0

mapfile -t packages < <(
  {
    printf '%s\n' "${seed_packages[@]}"
    apt-cache depends \
      --recurse \
      --no-recommends \
      --no-suggests \
      --no-conflicts \
      --no-breaks \
      --no-replaces \
      --no-enhances \
      "${seed_packages[@]}" 2>/dev/null \
      | awk '
          /^[A-Za-z0-9][^ ]*$/ { print $1; next }
          /^  Depends: / || /^\|Depends: / {
            dep=$2
            if (dep !~ /^</) print dep
          }
        '
  } | sort -u
)

write_progress_artifact "in_progress" "Downloading and extracting OpenCV dependency packages" 1
start_progress_heartbeat "in_progress" "Downloading and extracting OpenCV dependency packages" 1
(
  cd "${packages_dir}"
  apt download "${packages[@]}"

  for deb_path in ./*.deb; do
    dpkg-deb -x "${deb_path}" "${root_dir}"
  done
)
stop_progress_heartbeat

write_progress_artifact "in_progress" "Writing OpenCV bootstrap manifest" 2
{
  printf 'Seed packages:\n'
  printf '  - %s\n' "${seed_packages[@]}"
  printf 'Resolved package closure:\n'
  printf '  - %s\n' "${packages[@]}"
} > "${manifest_path}"

bootstrap_succeeded=1
write_progress_artifact "completed" "OpenCV bootstrap completed" 4

printf 'Bootstrapped local OpenCV prefix: %s\n' "${root_dir}/usr"
printf 'OpenCV CMake config: %s\n' \
  "${root_dir}/usr/lib/x86_64-linux-gnu/cmake/opencv4/OpenCVConfig.cmake"
printf 'OpenCV pkg-config metadata: %s\n' \
  "${root_dir}/usr/lib/x86_64-linux-gnu/pkgconfig/opencv4.pc"
printf 'Bootstrap manifest: %s\n' "${manifest_path}"
