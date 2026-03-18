PYTHON ?= python3
export PYTHONPATH := $(CURDIR)/src

.PHONY: help build smoke calibration-smoke normalize-fixture test check verify-production clean

help:
	@printf '%s\n' \
		'make build               Generate the dry-run smoke plan under build/' \
		'make smoke               Produce dry-run smoke outputs for the placeholder sequence' \
		'make calibration-smoke   Generate and validate the shareable calibration settings bundles' \
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

normalize-fixture:
	@./scripts/prepare_stereo_imu_sequence.py --manifest manifests/stereo_imu_fixture_normalization.json

test:
	@$(PYTHON) -m unittest discover -s tests -t .

check: test build smoke calibration-smoke normalize-fixture

verify-production:
	@$(PYTHON) scripts/verify_production.py --artifact-url "$(ARTIFACT_URL)"

clean:
	@rm -rf build
