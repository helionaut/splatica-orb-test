PYTHON ?= python3
export PYTHONPATH := $(CURDIR)/src

.PHONY: help build smoke calibration-smoke fetch-tum-rgbd rgbd-sanity publish-rgbd-sanity bootstrap-local-cmake bootstrap-local-eigen bootstrap-local-opencv bootstrap-local-boost bootstrap-local-ffmpeg bootstrap-local-pangolin monocular-prereqs normalize-fixture test check verify-production clean

help:
	@printf '%s\n' \
		'make build               Generate the dry-run smoke plan under build/' \
		'make smoke               Produce dry-run smoke outputs for the placeholder sequence' \
		'make calibration-smoke   Generate and validate the shareable calibration settings bundles' \
		'make fetch-tum-rgbd      Download and extract the public TUM RGB-D fr1/xyz sanity dataset' \
		'make rgbd-sanity         Run the clean-room TUM RGB-D fr1/xyz upstream sanity lane' \
		'make publish-rgbd-sanity Promote the latest TUM RGB-D sanity artifacts into reports/published/' \
		'make bootstrap-local-cmake Bootstrap a repo-local cmake toolchain under build/' \
		'make bootstrap-local-eigen Bootstrap a repo-local Eigen3 prefix under build/' \
		'make bootstrap-local-opencv Bootstrap a repo-local OpenCV prefix under build/' \
		'make bootstrap-local-boost Bootstrap a repo-local Boost serialization prefix under build/' \
		'make bootstrap-local-ffmpeg Bootstrap a repo-local ffmpeg/ffprobe bundle under build/' \
		'make bootstrap-local-pangolin Bootstrap a repo-local Pangolin prefix plus GL/GLEW/X11 sysroot under build/' \
		'make monocular-prereqs   Check whether the lens-10 monocular baseline is ready to prepare/run' \
		'make normalize-fixture   Normalize the checked-in stereo+IMU fixture into build/' \
		'make test                Run the Python stdlib test suite' \
		'make check               Run tests, build, smoke, and normalization in one command' \
		'make verify-production   Verify a published artifact once HEL-45 exposes one'

build:
	@mkdir -p build
	@$(PYTHON) scripts/render_plan.py --manifest manifests/smoke-run.json --output build/smoke-plan.md
	@printf 'Wrote build/smoke-plan.md\n'

smoke:
	@./scripts/run_orbslam3_sequence.sh --manifest manifests/smoke-run.json --dry-run

calibration-smoke:
	@./scripts/run_orbslam3_sequence.sh --manifest manifests/insta360_x3_shareable_calibration_smoke.json

fetch-tum-rgbd:
	@./scripts/fetch_tum_rgbd_dataset.py --manifest manifests/tum_rgbd_fr1_xyz_sanity.json

rgbd-sanity:
	@./scripts/run_clean_room_rgbd_sanity.sh manifests/tum_rgbd_fr1_xyz_sanity.json

publish-rgbd-sanity:
	@PYTHONPATH="$(CURDIR)/src" python3 scripts/publish_rgbd_tum_sanity.py

bootstrap-local-cmake:
	@./scripts/bootstrap_local_cmake.sh

bootstrap-local-eigen:
	@./scripts/bootstrap_local_eigen.sh

bootstrap-local-opencv:
	@./scripts/bootstrap_local_opencv.sh

bootstrap-local-boost:
	@./scripts/bootstrap_local_boost.sh

bootstrap-local-ffmpeg:
	@./scripts/bootstrap_local_ffmpeg.sh

bootstrap-local-pangolin:
	@./scripts/bootstrap_local_pangolin.sh

monocular-prereqs:
	@PYTHONPATH="$(CURDIR)/src" python3 scripts/check_monocular_baseline_prereqs.py \
		--manifest manifests/insta360_x3_lens10_monocular_baseline.json \
		--report reports/out/insta360_x3_lens10_monocular_prereqs.md

normalize-fixture:
	@./scripts/prepare_stereo_imu_sequence.py --manifest manifests/stereo_imu_fixture_normalization.json

test:
	@$(PYTHON) -m unittest discover -s tests -t .

check: test build smoke calibration-smoke normalize-fixture

verify-production:
	@$(PYTHON) scripts/verify_production.py --artifact-url "$(ARTIFACT_URL)"

clean:
	@rm -rf build
