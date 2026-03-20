#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

pangolin_repo_url="https://github.com/stevenlovegrove/Pangolin.git"
pangolin_tag="v0.8"
pangolin_commit="aff6883c83f3fd7e8268a9715e84266c42e2efe3"

packages_dir="${repo_root}/build/local-tools/pangolin-pkgs"
source_dir="${repo_root}/build/local-tools/pangolin-src"
build_dir="${repo_root}/build/local-tools/pangolin-build"
root_dir="${repo_root}/build/local-tools/pangolin-root"
sysroot_dir="${root_dir}/sysroot"
install_prefix="${root_dir}/usr/local"
manifest_path="${root_dir}/bootstrap-manifest.txt"
progress_artifact="${ORB_SLAM3_PROGRESS_ARTIFACT:-}"
progress_issue_id="${ORB_SLAM3_PROGRESS_ISSUE_ID:-}"
progress_heartbeat_seconds="${ORB_SLAM3_BOOTSTRAP_PROGRESS_HEARTBEAT_SECONDS:-60}"
progress_total=6
progress_heartbeat_pid=""
bootstrap_started=0
bootstrap_succeeded=0

local_cmake_bin="${repo_root}/build/local-tools/cmake-root/usr/bin/cmake"
local_cmake_lib="${repo_root}/build/local-tools/cmake-root/usr/lib/x86_64-linux-gnu"
local_eigen_prefix="${repo_root}/build/local-tools/eigen-root/usr"
local_eigen_config="${local_eigen_prefix}/share/eigen3/cmake/Eigen3Config.cmake"

cmake_bin=""
cmake_runtime_lib=""

seed_packages=(
  libglew-dev
  libglu1-mesa-dev
  libgl-dev
  libopengl-dev
  libglx-dev
  libx11-dev
  libegl-dev
)

for tool in apt dpkg-deb git make; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required bootstrap tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

if command -v cmake >/dev/null 2>&1; then
  cmake_bin="$(command -v cmake)"
elif [[ -x "${local_cmake_bin}" ]]; then
  cmake_bin="${local_cmake_bin}"
  cmake_runtime_lib="${local_cmake_lib}"
else
  "${script_dir}/bootstrap_local_cmake.sh"
  cmake_bin="${local_cmake_bin}"
  cmake_runtime_lib="${local_cmake_lib}"
fi

if [[ ! -f "${local_eigen_config}" ]] && ! pkg-config --exists eigen3 2>/dev/null; then
  "${script_dir}/bootstrap_local_eigen.sh"
fi

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

  python3 - "${repo_root}" "${progress_artifact}" "${progress_issue_id}" "${status}" "${current_step}" "${completed}" "${progress_total}" "${install_prefix}" "${manifest_path}" <<'PY'
import json
import sys
from pathlib import Path

repo_root_text, artifact_text, issue_id, status, current_step, completed_text, total_text, install_prefix_text, manifest_path_text = sys.argv[1:]

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
        "bootstrap": "pangolin",
        "install_prefix": rel(install_prefix_text),
    },
    "artifacts": [
        {
            "label": "pangolin_manifest",
            "path": rel(manifest_path_text),
        },
        {
            "label": "pangolin_cmake_config",
            "path": rel(f"{install_prefix_text}/lib/cmake/Pangolin/PangolinConfig.cmake"),
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
    write_progress_artifact "failed" "Pangolin bootstrap failed" 0
  fi
  exit "${exit_code}"
}

trap cleanup EXIT

rm -rf "${source_dir}" "${build_dir}" "${root_dir}"
mkdir -p "${packages_dir}" "${sysroot_dir}"
bootstrap_started=1
write_progress_artifact "in_progress" "Resolving Pangolin package closure" 0

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

write_progress_artifact "in_progress" "Downloading and extracting Pangolin dependency packages" 1
start_progress_heartbeat "in_progress" "Downloading and extracting Pangolin dependency packages" 1
(
  cd "${packages_dir}"
  apt download "${packages[@]}"

  for deb_path in ./*.deb; do
    dpkg-deb -x "${deb_path}" "${sysroot_dir}"
  done
)
stop_progress_heartbeat

write_progress_artifact "in_progress" "Cloning pinned Pangolin source" 2
git clone --depth 1 --branch "${pangolin_tag}" "${pangolin_repo_url}" "${source_dir}"

resolved_commit="$(git -C "${source_dir}" rev-parse HEAD)"
if [[ "${resolved_commit}" != "${pangolin_commit}" ]]; then
  printf 'Unexpected Pangolin commit for %s: got %s, expected %s\n' \
    "${pangolin_tag}" "${resolved_commit}" "${pangolin_commit}" >&2
  exit 1
fi

cmake_prefix_path="${sysroot_dir}/usr"
if [[ -f "${local_eigen_config}" ]]; then
  cmake_prefix_path="${local_eigen_prefix}:${cmake_prefix_path}"
fi

sysroot_lib="${sysroot_dir}/usr/lib/x86_64-linux-gnu"
sysroot_include="${sysroot_dir}/usr/include"
sysroot_pkgconfig="${sysroot_lib}/pkgconfig"
sysroot_share_pkgconfig="${sysroot_dir}/usr/share/pkgconfig"

write_progress_artifact "in_progress" "Configuring Pangolin build" 3
(
  export PATH="$(dirname "${cmake_bin}"):${PATH}"
  if [[ -n "${cmake_runtime_lib}" ]]; then
    export LD_LIBRARY_PATH="${cmake_runtime_lib}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  fi
  export LD_LIBRARY_PATH="${sysroot_lib}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  export CMAKE_PREFIX_PATH="${cmake_prefix_path}${CMAKE_PREFIX_PATH:+:${CMAKE_PREFIX_PATH}}"
  export CMAKE_INCLUDE_PATH="${sysroot_include}${CMAKE_INCLUDE_PATH:+:${CMAKE_INCLUDE_PATH}}"
  export CMAKE_LIBRARY_PATH="${sysroot_lib}${CMAKE_LIBRARY_PATH:+:${CMAKE_LIBRARY_PATH}}"
  export PKG_CONFIG_PATH="${sysroot_pkgconfig}:${sysroot_share_pkgconfig}${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
  export CPATH="${sysroot_include}${CPATH:+:${CPATH}}"
  export LIBRARY_PATH="${sysroot_lib}${LIBRARY_PATH:+:${LIBRARY_PATH}}"

  "${cmake_bin}" \
    -S "${source_dir}" \
    -B "${build_dir}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${install_prefix}" \
    -DCMAKE_CXX_FLAGS=-include\ cstdint \
    -DBUILD_TOOLS=OFF \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_TESTS=OFF \
    -DBUILD_PANGOLIN_FFMPEG=OFF \
    -DBUILD_PANGOLIN_LIBDC1394=OFF \
    -DBUILD_PANGOLIN_V4L=OFF \
    -DBUILD_PANGOLIN_REALSENSE=OFF \
    -DBUILD_PANGOLIN_REALSENSE2=OFF \
    -DBUILD_PANGOLIN_OPENNI=OFF \
    -DBUILD_PANGOLIN_OPENNI2=OFF \
    -DBUILD_PANGOLIN_LIBUVC=OFF \
    -DBUILD_PANGOLIN_DEPTHSENSE=OFF \
    -DBUILD_PANGOLIN_TELICAM=OFF \
    -DBUILD_PANGOLIN_PLEORA=OFF \
    -DBUILD_PANGOLIN_LIBPNG=OFF \
    -DBUILD_PANGOLIN_LIBJPEG=OFF \
    -DBUILD_PANGOLIN_LIBTIFF=OFF \
    -DBUILD_PANGOLIN_LIBOPENEXR=OFF \
    -DBUILD_PANGOLIN_LZ4=OFF \
    -DBUILD_PANGOLIN_ZSTD=OFF \
    -DBUILD_PANGOLIN_LIBRAW=OFF \
    -DBUILD_PANGOLIN_PYTHON=OFF

  write_progress_artifact "in_progress" "Building Pangolin libraries" 4
  start_progress_heartbeat "in_progress" "Building Pangolin libraries" 4
  "${cmake_bin}" --build "${build_dir}" --parallel 4
  stop_progress_heartbeat

  write_progress_artifact "in_progress" "Installing Pangolin prefix" 5
  "${cmake_bin}" --install "${build_dir}"
)

{
  printf 'Pangolin repo: %s\n' "${pangolin_repo_url}"
  printf 'Pangolin tag: %s\n' "${pangolin_tag}"
  printf 'Pangolin commit: %s\n' "${resolved_commit}"
  printf 'Install prefix: %s\n' "${install_prefix}"
  printf 'Dependency sysroot: %s\n' "${sysroot_dir}/usr"
  printf 'CMake binary: %s\n' "${cmake_bin}"
  printf 'Seed packages:\n'
  printf '  - %s\n' "${seed_packages[@]}"
  printf 'Resolved package closure:\n'
  printf '  - %s\n' "${packages[@]}"
} > "${manifest_path}"

bootstrap_succeeded=1
write_progress_artifact "completed" "Pangolin bootstrap completed" 6

printf 'Bootstrapped local Pangolin prefix: %s\n' "${install_prefix}"
printf 'Pangolin CMake config: %s\n' \
  "${install_prefix}/lib/cmake/Pangolin/PangolinConfig.cmake"
printf 'Pangolin dependency sysroot: %s\n' "${sysroot_dir}/usr"
printf 'Bootstrap manifest: %s\n' "${manifest_path}"
