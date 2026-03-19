#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

checkout_dir="${1:-${repo_root}/third_party/orbslam3/upstream}"
local_cmake_bin="${repo_root}/build/local-tools/cmake-root/usr/bin/cmake"
local_cmake_lib="${repo_root}/build/local-tools/cmake-root/usr/lib/x86_64-linux-gnu"
local_eigen_prefix="${repo_root}/build/local-tools/eigen-root/usr"
local_opencv_prefix="${repo_root}/build/local-tools/opencv-root/usr"
local_opencv_cmake="${local_opencv_prefix}/lib/x86_64-linux-gnu/cmake/opencv4/OpenCVConfig.cmake"
local_opencv_pkgconfig="${local_opencv_prefix}/lib/x86_64-linux-gnu/pkgconfig/opencv4.pc"
local_opencv_lib="${local_opencv_prefix}/lib/x86_64-linux-gnu"
local_boost_prefix="${repo_root}/build/local-tools/boost-root/usr"
local_boost_header="${local_boost_prefix}/include/boost/serialization/serialization.hpp"
local_boost_lib="${local_boost_prefix}/lib/x86_64-linux-gnu"
local_pangolin_prefix="${repo_root}/build/local-tools/pangolin-root/usr/local"
local_pangolin_cmake="${local_pangolin_prefix}/lib/cmake/Pangolin/PangolinConfig.cmake"
local_pangolin_pkgconfig="${local_pangolin_prefix}/lib/pkgconfig/pangolin.pc"
local_pangolin_lib="${local_pangolin_prefix}/lib"
local_pangolin_sysroot_prefix="${repo_root}/build/local-tools/pangolin-root/sysroot/usr"
local_pangolin_sysroot_lib="${local_pangolin_sysroot_prefix}/lib/x86_64-linux-gnu"
local_pangolin_sysroot_include="${local_pangolin_sysroot_prefix}/include"
local_pangolin_sysroot_pkgconfig="${local_pangolin_sysroot_lib}/pkgconfig"
local_pangolin_sysroot_share_pkgconfig="${local_pangolin_sysroot_prefix}/share/pkgconfig"
cmake_bin=""
build_target="${ORB_SLAM3_BUILD_TARGET:-mono_tum_vi}"
local_opencv_link_dirs=(
  "${local_opencv_prefix}/lib"
  "${local_opencv_lib}"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/atlas"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/blas"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/lapack"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/blis-openmp"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/blis-pthread"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/blis-serial"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/openblas-openmp"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/openblas-pthread"
  "${local_opencv_prefix}/lib/x86_64-linux-gnu/openblas-serial"
)
linker_search_dirs=()

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

if [[ ! -f "${checkout_dir}/CMakeLists.txt" ]]; then
  printf 'Missing ORB-SLAM3 checkout at %s. Run ./scripts/fetch_orbslam3_baseline.sh first.\n' "${checkout_dir}" >&2
  exit 1
fi

run_component_build() {
  local label="$1"
  local source_dir="$2"
  local build_dir="$3"
  shift 3

  printf 'Configuring and building %s ...\n' "${label}"
  mkdir -p "${build_dir}"
  (
    cd "${build_dir}"
    "${cmake_bin}" "${source_dir}" -DCMAKE_BUILD_TYPE=Release "$@"
    make -j
  )
}

prepend_path_var() {
  local name="$1"
  local value="$2"

  if [[ ! -d "${value}" ]]; then
    return 0
  fi

  local current_value="${!name-}"
  if [[ -n "${current_value}" ]]; then
    printf -v "${name}" '%s:%s' "${value}" "${current_value}"
  else
    printf -v "${name}" '%s' "${value}"
  fi
  export "${name}"
}

append_linker_search_dir() {
  local dir="$1"

  if [[ ! -d "${dir}" ]]; then
    return 0
  fi

  linker_search_dirs+=("${dir}")
  prepend_path_var LD_LIBRARY_PATH "${dir}"
  prepend_path_var LIBRARY_PATH "${dir}"
  prepend_path_var CMAKE_LIBRARY_PATH "${dir}"
}

(
  if [[ "${cmake_bin}" == "${local_cmake_bin}" ]]; then
    export PATH="$(dirname "${local_cmake_bin}"):${PATH}"
    export LD_LIBRARY_PATH="${local_cmake_lib}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  fi
  if [[ -d "${local_eigen_prefix}/share/eigen3/cmake" ]]; then
    export CMAKE_PREFIX_PATH="${local_eigen_prefix}${CMAKE_PREFIX_PATH:+:${CMAKE_PREFIX_PATH}}"
    export PKG_CONFIG_PATH="${local_eigen_prefix}/share/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
  fi
  if [[ -f "${local_opencv_cmake}" || -f "${local_opencv_pkgconfig}" ]]; then
    export CMAKE_PREFIX_PATH="${local_opencv_prefix}${CMAKE_PREFIX_PATH:+:${CMAKE_PREFIX_PATH}}"
    export PKG_CONFIG_PATH="${local_opencv_prefix}/lib/x86_64-linux-gnu/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
    for link_dir in "${local_opencv_link_dirs[@]}"; do
      append_linker_search_dir "${link_dir}"
    done
  fi
  if [[ -f "${local_boost_header}" ]] && compgen -G "${local_boost_lib}/libboost_serialization.so*" >/dev/null; then
    export CMAKE_PREFIX_PATH="${local_boost_prefix}${CMAKE_PREFIX_PATH:+:${CMAKE_PREFIX_PATH}}"
    export CPATH="${local_boost_prefix}/include${CPATH:+:${CPATH}}"
    append_linker_search_dir "${local_boost_lib}"
  fi
  if [[ -f "${local_pangolin_cmake}" || -f "${local_pangolin_pkgconfig}" ]]; then
    export CMAKE_PREFIX_PATH="${local_pangolin_prefix}${CMAKE_PREFIX_PATH:+:${CMAKE_PREFIX_PATH}}"
    export PKG_CONFIG_PATH="${local_pangolin_prefix}/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
    append_linker_search_dir "${local_pangolin_lib}"
  fi
  if [[ -d "${local_pangolin_sysroot_lib}" ]]; then
    export CMAKE_PREFIX_PATH="${local_pangolin_sysroot_prefix}${CMAKE_PREFIX_PATH:+:${CMAKE_PREFIX_PATH}}"
    export CMAKE_INCLUDE_PATH="${local_pangolin_sysroot_include}${CMAKE_INCLUDE_PATH:+:${CMAKE_INCLUDE_PATH}}"
    export PKG_CONFIG_PATH="${local_pangolin_sysroot_pkgconfig}:${local_pangolin_sysroot_share_pkgconfig}${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
    export CPATH="${local_pangolin_sysroot_include}${CPATH:+:${CPATH}}"
    append_linker_search_dir "${local_pangolin_sysroot_lib}"
  fi

  run_component_build \
    "Thirdparty/DBoW2" \
    "${checkout_dir}/Thirdparty/DBoW2" \
    "${checkout_dir}/Thirdparty/DBoW2/build"
  run_component_build \
    "Thirdparty/g2o" \
    "${checkout_dir}/Thirdparty/g2o" \
    "${checkout_dir}/Thirdparty/g2o/build"
  run_component_build \
    "Thirdparty/Sophus" \
    "${checkout_dir}/Thirdparty/Sophus" \
    "${checkout_dir}/Thirdparty/Sophus/build" \
    -DBUILD_TESTS=OFF \
    -DBUILD_EXAMPLES=OFF

  printf 'Uncompress vocabulary ...\n'
  (
    cd "${checkout_dir}/Vocabulary"
    tar -xf ORBvoc.txt.tar.gz
  )

  python3 "${repo_root}/scripts/patch_orbslam3_baseline.py" \
    --checkout-dir "${checkout_dir}"

  printf 'Configuring ORB_SLAM3 ...\n'
  mkdir -p "${checkout_dir}/build"
  (
    cd "${checkout_dir}/build"
    cmake_args=(
      "${checkout_dir}"
      -DCMAKE_BUILD_TYPE=Release
      -DCMAKE_CXX_FLAGS_RELEASE=-march=native\ -std=gnu++14
    )
    if ((${#linker_search_dirs[@]})); then
      linker_flag_text=""
      for link_dir in "${linker_search_dirs[@]}"; do
        linker_flag_text+=" -Wl,-rpath-link,${link_dir}"
      done
      linker_flag_text="${linker_flag_text# }"
      cmake_args+=(
        "-DCMAKE_EXE_LINKER_FLAGS=${linker_flag_text}"
        "-DCMAKE_SHARED_LINKER_FLAGS=${linker_flag_text}"
      )
    fi
    # Pangolin v0.8 installs sigslot headers that require C++14 aliases.
    "${cmake_bin}" "${cmake_args[@]}"
    printf 'Building ORB_SLAM3 target %s ...\n' "${build_target}"
    "${cmake_bin}" --build . --parallel 4 --target "${build_target}"
  )
)

printf 'Built ORB-SLAM3 baseline in %s\n' "${checkout_dir}"
