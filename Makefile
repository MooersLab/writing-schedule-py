# Makefile for the writing-schedule Python package.
# Run `make` or `make help` to list targets.

PYTHON ?= python3
PIP    := $(PYTHON) -m pip
PKG    := writing_schedule

# Overridable inputs for the demo target.
TABLE  ?= examples/projects-and-tasks.org
WEEK   ?= 2026-01-19
OUT    ?= out

# For the reference target: path to the elisp package and its fixture.
WS_EL    ?= writing-schedule.el
REF_WEEK ?= 2026-01-19
REF_TABLE ?= tests/fixtures/projects-and-tasks.org

.DEFAULT_GOAL := help

.PHONY: help install dev test coverage lint build check publish publish-test \
        demo reference clean distclean

help: ## List the available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	$(PIP) install .

dev: ## Install editable with the test extras
	$(PIP) install -e ".[test]"

test: ## Run the test suite
	$(PYTHON) -m pytest -q

coverage: ## Run the tests with a coverage report (needs pytest-cov)
	@$(PYTHON) -c "import pytest_cov" 2>/dev/null || $(PIP) install pytest-cov
	$(PYTHON) -m pytest --cov=$(PKG) --cov-report=term-missing

lint: ## Lint with ruff when it is installed
	@command -v ruff >/dev/null 2>&1 \
	  && ruff check $(PKG) tests \
	  || echo "ruff not installed; skipping (pip install ruff)"

build: ## Build the sdist and wheel into dist/
	@$(PYTHON) -c "import build" 2>/dev/null || $(PIP) install build
	$(PYTHON) -m build

check: build ## Validate the built distributions with twine
	@$(PYTHON) -c "import twine" 2>/dev/null || $(PIP) install twine
	$(PYTHON) -m twine check dist/*

publish-test: check ## Upload to TestPyPI
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish: check ## Upload to PyPI
	$(PYTHON) -m twine upload dist/*

demo: ## Generate the schedule, calendar, and sheets from $(TABLE) into $(OUT)/
	$(PYTHON) -m writing_schedule.cli generate $(TABLE) --week $(WEEK) --dir $(OUT)
	$(PYTHON) -m writing_schedule.cli sheets   $(TABLE) --week $(WEEK) --dir $(OUT) --format both
	@echo "Wrote outputs to $(OUT)/"

reference: ## Refresh the frozen elisp fixtures (needs emacs and WS_EL=path/to/writing-schedule.el)
	@command -v emacs >/dev/null 2>&1 || { echo "emacs not found"; exit 1; }
	@test -f "$(WS_EL)" || { echo "set WS_EL to writing-schedule.el (WS_EL=$(WS_EL) not found)"; exit 1; }
	@tmp=$$(mktemp -d); \
	 dir=$$(cd "$$(dirname "$(WS_EL)")" && pwd); \
	 printf '(add-to-list (quote load-path) "%s")\n(require (quote writing-schedule))\n(setq writing-schedule-directory "%s")\n(setq writing-schedule-sheets-directory "%s")\n(writing-schedule-batch-generate "%s" "%s" "%s")\n(writing-schedule-batch-timeblock-sheets "%s" "%s" nil "%s" "org")\n' \
	   "$$dir" "$$tmp" "$$tmp" "$(abspath $(REF_TABLE))" "$(REF_WEEK)" "$$tmp" "$(abspath $(REF_TABLE))" "$(REF_WEEK)" "$$tmp" > $$tmp/driver.el; \
	 emacs --batch -Q -l $$tmp/driver.el; \
	 cp $$tmp/writing-$(REF_WEEK).org       tests/fixtures/expected/writing-$(REF_WEEK).org; \
	 cp $$tmp/writing-$(REF_WEEK).ics       tests/fixtures/expected/writing-$(REF_WEEK).ics; \
	 cp $$tmp/sheets-week-$(REF_WEEK).org   tests/fixtures/expected/sheets-week-$(REF_WEEK).org; \
	 rm -rf $$tmp; \
	 echo "Refreshed tests/fixtures/expected/ from the elisp reference"

clean: ## Remove caches, build artifacts, and demo output
	rm -rf build dist *.egg-info $(OUT)
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete

distclean: clean ## Alias for clean
	@true
