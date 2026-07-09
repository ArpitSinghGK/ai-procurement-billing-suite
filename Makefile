.PHONY: install dev test lint run diagram

install:
	python3 -m pip install -e .

dev:
	python3 -m pip install -e ".[dev]"

test:
	python3 -m pytest -q

lint:
	python3 -m ruff check src tests

run:
	python3 -m uvicorn procurement_suite.api.app:app --reload

# Regenerate the animated architecture diagram from the spec.
diagram:
	python3 scripts/generate_arch_diagram.py assets/architecture.json --outdir assets
