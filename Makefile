PYTHON ?= python3
export PYTHONPATH := $(CURDIR)/src

.PHONY: help build smoke test check verify-production clean

help:
	@printf '%s\n' \
		'make build               Generate the dry-run smoke plan under build/' \
		'make smoke               Produce dry-run smoke outputs for the placeholder sequence' \
		'make test                Run the Python stdlib test suite' \
		'make check               Run test, build, and smoke in one command' \
		'make verify-production   Verify a published artifact once HEL-45 exposes one'

build:
	@mkdir -p build
	@$(PYTHON) scripts/render_plan.py --manifest manifests/smoke-run.json --output build/smoke-plan.md
	@printf 'Wrote build/smoke-plan.md\n'

smoke:
	@./scripts/run_orbslam3_sequence.sh --manifest manifests/smoke-run.json --dry-run

test:
	@$(PYTHON) -m unittest discover -s tests -t .

check: test build smoke

verify-production:
	@$(PYTHON) scripts/verify_production.py --artifact-url "$(ARTIFACT_URL)"

clean:
	@rm -rf build
