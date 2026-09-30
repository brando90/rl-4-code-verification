# TLDR: Shortcuts for installing, testing and fetching the pinned external repositories.
.PHONY: install test external

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

external:
	bash scripts/setup_external.sh
