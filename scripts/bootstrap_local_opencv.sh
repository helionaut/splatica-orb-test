#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

packages_dir="${repo_root}/build/local-tools/opencv-pkgs"
root_dir="${repo_root}/build/local-tools/opencv-root"
packages=(
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

for tool in apt dpkg-deb; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required bootstrap tool: %s\n' "${tool}" >&2
    exit 1
  fi
done

mkdir -p "${packages_dir}"
rm -rf "${root_dir}"
mkdir -p "${root_dir}"

(
  cd "${packages_dir}"
  apt download "${packages[@]}"

  for deb_path in ./*.deb; do
    dpkg-deb -x "${deb_path}" "${root_dir}"
  done
)

printf 'Bootstrapped local OpenCV prefix: %s\n' "${root_dir}/usr"
printf 'OpenCV CMake config: %s\n' \
  "${root_dir}/usr/lib/x86_64-linux-gnu/cmake/opencv4/OpenCVConfig.cmake"
printf 'OpenCV pkg-config metadata: %s\n' \
  "${root_dir}/usr/lib/x86_64-linux-gnu/pkgconfig/opencv4.pc"
