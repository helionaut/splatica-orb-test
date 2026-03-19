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

rm -rf "${source_dir}" "${build_dir}" "${root_dir}"
mkdir -p "${packages_dir}" "${sysroot_dir}"

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

(
  cd "${packages_dir}"
  apt download "${packages[@]}"

  for deb_path in ./*.deb; do
    dpkg-deb -x "${deb_path}" "${sysroot_dir}"
  done
)

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

  "${cmake_bin}" --build "${build_dir}" --parallel 4
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

printf 'Bootstrapped local Pangolin prefix: %s\n' "${install_prefix}"
printf 'Pangolin CMake config: %s\n' \
  "${install_prefix}/lib/cmake/Pangolin/PangolinConfig.cmake"
printf 'Pangolin dependency sysroot: %s\n' "${sysroot_dir}/usr"
printf 'Bootstrap manifest: %s\n' "${manifest_path}"
