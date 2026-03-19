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
append_march_native="${ORB_SLAM3_APPEND_MARCH_NATIVE:-OFF}"
build_parallelism="${ORB_SLAM3_BUILD_PARALLELISM:-1}"
build_experiment="${ORB_SLAM3_BUILD_EXPERIMENT:-orbslam3-${build_target}-portable-build}"
changed_variable="${ORB_SLAM3_BUILD_CHANGED_VARIABLE:-disable -march=native and capture build-attempt signature}"
hypothesis="${ORB_SLAM3_BUILD_HYPOTHESIS:-portable release flags plus explicit attempt metadata will either produce ${build_target}/libORB_SLAM3.so or surface a concrete compiler or linker blocker}"
success_criterion="${ORB_SLAM3_BUILD_SUCCESS_CRITERION:-${build_target} executable and libORB_SLAM3.so both exist after phase 7}"
allow_identical_retry="${ORB_SLAM3_ALLOW_IDENTICAL_RETRY:-0}"
build_attempt_dir="${repo_root}/.symphony/build-attempts"
build_attempt_latest="${build_attempt_dir}/orbslam3-build-latest.json"
build_attempt_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
build_attempt_current="${build_attempt_dir}/orbslam3-build-${build_attempt_stamp}.json"
build_log_latest="${build_attempt_dir}/orbslam3-build-latest.log"
build_log_current="${build_attempt_dir}/orbslam3-build-${build_attempt_stamp}.log"
dmesg_latest="${build_attempt_dir}/orbslam3-build-dmesg-latest.log"
dmesg_current="${build_attempt_dir}/orbslam3-build-dmesg-${build_attempt_stamp}.log"
build_started=0
build_succeeded=0
current_build_signature=""
build_executable_path=""
build_example_source_path=""
build_library_path=""
build_command_text=""
build_command_workdir=""
build_started_at=""
build_finished_at=""
build_pid=""
build_exit_code=""
build_exit_signal=""
oom_detected=0
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
release_flag_parts=("-std=gnu++14")

if [[ "${append_march_native}" == "ON" ]]; then
  release_flag_parts=("-march=native" "${release_flag_parts[@]}")
fi

release_flags="${release_flag_parts[*]}"

if [[ ! "${build_parallelism}" =~ ^[1-9][0-9]*$ ]]; then
  printf 'ORB_SLAM3_BUILD_PARALLELISM must be a positive integer, got: %s\n' "${build_parallelism}" >&2
  exit 1
fi

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

resolve_example_artifact_paths() {
  case "$1" in
    mono_inertial_* )
      printf '%s\n' "${checkout_dir}/Examples/Monocular-Inertial/${1}" "${checkout_dir}/Examples/Monocular-Inertial/${1}.cc"
      ;;
    mono_* )
      printf '%s\n' "${checkout_dir}/Examples/Monocular/${1}" "${checkout_dir}/Examples/Monocular/${1}.cc"
      ;;
    stereo_inertial_* )
      printf '%s\n' "${checkout_dir}/Examples/Stereo-Inertial/${1}" "${checkout_dir}/Examples/Stereo-Inertial/${1}.cc"
      ;;
    stereo_* )
      printf '%s\n' "${checkout_dir}/Examples/Stereo/${1}" "${checkout_dir}/Examples/Stereo/${1}.cc"
      ;;
    rgbd_* )
      printf '%s\n' "${checkout_dir}/Examples/RGB-D/${1}" "${checkout_dir}/Examples/RGB-D/${1}.cc"
      ;;
    * )
      printf 'Unsupported ORB-SLAM3 build target for artifact resolution: %s\n' "$1" >&2
      exit 1
      ;;
  esac
}

mapfile -t build_example_artifacts < <(resolve_example_artifact_paths "${build_target}")
build_executable_path="${build_example_artifacts[0]}"
build_example_source_path="${build_example_artifacts[1]}"
build_library_path="${checkout_dir}/lib/libORB_SLAM3.so"

capture_dmesg_snapshot() {
  local destination="$1"

  mkdir -p "$(dirname "${destination}")"
  if command -v dmesg >/dev/null 2>&1; then
    if ! dmesg -T >"${destination}" 2>&1; then
      printf 'Unable to read dmesg for build diagnostics.\n' >"${destination}"
    fi
  else
    printf 'dmesg is unavailable in this environment.\n' >"${destination}"
  fi
}

refresh_latest_diagnostics() {
  if [[ -f "${build_log_current}" ]]; then
    cp "${build_log_current}" "${build_log_latest}"
  fi
  if [[ -f "${dmesg_current}" ]]; then
    cp "${dmesg_current}" "${dmesg_latest}"
  fi
}

write_build_attempt_metadata() {
  local status="$1"
  local failure_reason="${2:-}"

  refresh_latest_diagnostics

  python3 - "${repo_root}" "${checkout_dir}" "${build_attempt_current}" "${build_attempt_latest}" "${build_target}" "${append_march_native}" "${build_parallelism}" "${release_flags}" "${build_experiment}" "${changed_variable}" "${hypothesis}" "${success_criterion}" "${status}" "${failure_reason}" "${build_executable_path}" "${build_example_source_path}" "${build_library_path}" "${allow_identical_retry}" "${current_build_signature}" "${build_log_current}" "${dmesg_current}" "${build_command_text}" "${build_command_workdir}" "${build_started_at}" "${build_finished_at}" "${build_pid}" "${build_exit_code}" "${build_exit_signal}" "${oom_detected}" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

(
    repo_root_text,
    checkout_dir_text,
    current_path_text,
    latest_path_text,
    build_target,
    append_march_native,
    build_parallelism,
    release_flags,
    build_experiment,
    changed_variable,
    hypothesis,
    success_criterion,
    status,
    failure_reason,
    executable_path_text,
    example_source_path_text,
    library_path_text,
    allow_identical_retry,
    current_build_signature,
    build_log_path_text,
    dmesg_path_text,
    build_command_text,
    build_command_workdir,
    build_started_at,
    build_finished_at,
    build_pid,
    build_exit_code,
    build_exit_signal,
    oom_detected,
) = sys.argv[1:]

repo_root = Path(repo_root_text)
checkout_dir = Path(checkout_dir_text)
current_path = Path(current_path_text)
latest_path = Path(latest_path_text)
executable_path = Path(executable_path_text)
example_source_path = Path(example_source_path_text)
library_path = Path(library_path_text)
build_log_path = Path(build_log_path_text)
dmesg_path = Path(dmesg_path_text)
current_path.parent.mkdir(parents=True, exist_ok=True)

def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git_head(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None

def relative_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)

def tail_lines(path: Path, limit: int = 40) -> list[str]:
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except Exception:
        return []

def optional_int(text: str) -> int | None:
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None

payload = {
    "kind": "orbslam3-build-attempt",
    "build_target": build_target,
    "checkout_head": git_head(checkout_dir),
    "append_march_native": append_march_native == "ON",
    "build_parallelism": int(build_parallelism),
    "release_flags": release_flags,
    "experiment": build_experiment,
    "changed_variable": changed_variable,
    "hypothesis": hypothesis,
    "success_criterion": success_criterion,
    "allow_identical_retry": allow_identical_retry == "1",
    "signature": current_build_signature,
    "status": status,
    "failure_reason": failure_reason,
    "patch_targets": {
        "CMakeLists.txt": sha256(checkout_dir / "CMakeLists.txt"),
        "src/System.cc": sha256(checkout_dir / "src/System.cc"),
        "example_entrypoint": sha256(example_source_path),
    },
    "artifacts": {
        "executable": str(executable_path.relative_to(repo_root)),
        "example_source": str(example_source_path.relative_to(repo_root)),
        "library": str(library_path.relative_to(repo_root)),
    },
    "artifact_exists": {
        "executable": executable_path.exists(),
        "example_source": example_source_path.exists(),
        "library": library_path.exists(),
    },
    "diagnostics": {
        "build_command": build_command_text or None,
        "build_working_directory": build_command_workdir or None,
        "build_started_at": build_started_at or None,
        "build_finished_at": build_finished_at or None,
        "build_pid": optional_int(build_pid),
        "build_exit_code": optional_int(build_exit_code),
        "build_exit_signal": optional_int(build_exit_signal),
        "build_log": relative_text(build_log_path),
        "kernel_dmesg": relative_text(dmesg_path),
        "oom_detected": oom_detected == "1",
        "last_build_log_lines": tail_lines(build_log_path),
        "last_dmesg_lines": tail_lines(dmesg_path),
    },
}

text = json.dumps(payload, indent=2) + "\n"
current_path.write_text(text, encoding="utf-8")
latest_path.write_text(text, encoding="utf-8")
PY
}

compute_build_signature() {
  python3 - "${checkout_dir}" "${build_target}" "${append_march_native}" "${release_flags}" "${build_experiment}" "${changed_variable}" "${hypothesis}" "${success_criterion}" "${build_example_source_path}" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

(
    checkout_dir_text,
    build_target,
    append_march_native,
    release_flags,
    build_experiment,
    changed_variable,
    hypothesis,
    success_criterion,
    example_source_path_text,
) = sys.argv[1:]

checkout_dir = Path(checkout_dir_text)
example_source_path = Path(example_source_path_text)

def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git_head(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None

signature_payload = {
    "build_target": build_target,
    "checkout_head": git_head(checkout_dir),
    "append_march_native": append_march_native == "ON",
    "release_flags": release_flags,
    "experiment": build_experiment,
    "changed_variable": changed_variable,
    "hypothesis": hypothesis,
    "success_criterion": success_criterion,
    "patch_targets": {
        "CMakeLists.txt": sha256(checkout_dir / "CMakeLists.txt"),
        "src/System.cc": sha256(checkout_dir / "src/System.cc"),
        "example_entrypoint": sha256(example_source_path),
    },
}
print(hashlib.sha256(json.dumps(signature_payload, sort_keys=True).encode("utf-8")).hexdigest())
PY
}

reject_identical_retry_if_needed() {
  if [[ ! -f "${build_attempt_latest}" ]]; then
    return 0
  fi

  previous_signature="$(python3 - "${build_attempt_latest}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("")
else:
    print(data.get("signature", ""))
PY
)"

  if [[ -n "${previous_signature}" && "${previous_signature}" == "${current_build_signature}" && "${allow_identical_retry}" != "1" ]]; then
    printf 'Identical retry rejected for target %s.\n' "${build_target}" >&2
    printf 'Declare a changed variable, hypothesis, or explicit override before rebuilding with the same inputs.\n' >&2
    write_build_attempt_metadata "rejected" "identical retry rejected"
    exit 2
  fi
}

finalize_build_attempt() {
  local exit_code="$1"
  local status="failed"
  local failure_reason="build script exited before producing expected outputs"

  if [[ "${build_started}" -eq 0 ]]; then
    return
  fi

  if [[ "${exit_code}" -eq 0 && "${build_succeeded}" -eq 1 ]]; then
    status="completed"
    failure_reason=""
  elif [[ "${exit_code}" -ne 0 ]]; then
    failure_reason="build command failed with exit code ${exit_code}"
  elif [[ ! -x "${build_executable_path}" ]]; then
    failure_reason="expected executable missing after build"
  elif [[ ! -f "${build_library_path}" ]]; then
    failure_reason="expected libORB_SLAM3.so missing after build"
  fi

  if [[ -z "${build_finished_at}" ]]; then
    build_finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  fi

  if [[ "${oom_detected}" -eq 1 ]]; then
    if [[ -n "${failure_reason}" ]]; then
      failure_reason="${failure_reason}; kernel reported OOM kill during build"
    else
      failure_reason="kernel reported OOM kill during build"
    fi
  fi

  write_build_attempt_metadata "${status}" "${failure_reason}"
}

trap 'finalize_build_attempt "$?"' EXIT

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

{
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

  mkdir -p "${build_attempt_dir}"
  current_build_signature="$(compute_build_signature)"
  reject_identical_retry_if_needed
  build_started=1
  write_build_attempt_metadata "started" ""

  printf 'Configuring ORB_SLAM3 ...\n'
  mkdir -p "${checkout_dir}/build"
  (
    cd "${checkout_dir}/build"
    cmake_args=(
      "${checkout_dir}"
      -DCMAKE_BUILD_TYPE=Release
      "-DCMAKE_CXX_FLAGS_RELEASE=${release_flags}"
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
    mkdir -p "${build_attempt_dir}"
    : >"${build_log_current}"
    build_command_workdir="$(pwd)"
    build_started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    build_command=(
      "${cmake_bin}"
      --build
      .
      --parallel
      "${build_parallelism}"
      --verbose
      --target
      "${build_target}"
    )
    printf -v build_command_text '%q ' "${build_command[@]}"
    build_command_text="${build_command_text% }"
    printf 'Build command: %s\n' "${build_command_text}" | tee -a "${build_log_current}"
    printf 'Build working directory: %s\n' "${build_command_workdir}" | tee -a "${build_log_current}"
    printf 'Build started at: %s\n' "${build_started_at}" | tee -a "${build_log_current}"
    set +e
    "${build_command[@]}" > >(tee -a "${build_log_current}") 2>&1 &
    build_pid="$!"
    wait "${build_pid}"
    build_exit_code="$?"
    set -e
    build_finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if (( build_exit_code > 128 )); then
      build_exit_signal="$((build_exit_code - 128))"
    fi
    capture_dmesg_snapshot "${dmesg_current}"
    if grep -Eq "oom-kill|Out of memory: Killed process" "${dmesg_current}"; then
      oom_detected=1
    fi
    printf 'Build finished at: %s\n' "${build_finished_at}" | tee -a "${build_log_current}"
    printf 'Build PID: %s\n' "${build_pid}" | tee -a "${build_log_current}"
    printf 'Build exit code: %s\n' "${build_exit_code}" | tee -a "${build_log_current}"
    if [[ -n "${build_exit_signal}" ]]; then
      printf 'Build exit signal: %s\n' "${build_exit_signal}" | tee -a "${build_log_current}"
    fi
    if [[ "${oom_detected}" -eq 1 ]]; then
      printf 'Kernel OOM evidence detected in %s\n' "${dmesg_current}" | tee -a "${build_log_current}"
    fi
    if [[ "${build_exit_code}" -ne 0 ]]; then
      exit "${build_exit_code}"
    fi
  )

  if [[ ! -x "${build_executable_path}" ]]; then
    printf 'Expected executable missing after build: %s\n' "${build_executable_path}" >&2
    exit 1
  fi

  if [[ ! -f "${build_library_path}" ]]; then
    printf 'Expected shared library missing after build: %s\n' "${build_library_path}" >&2
    exit 1
  fi

  build_succeeded=1
}

printf 'Built ORB-SLAM3 baseline in %s\n' "${checkout_dir}"
