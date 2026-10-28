PYTHON = python3
VENV = .venv
BIN = $(VENV)/bin
CONFIG = config.txt

.PHONY: install run debug clean lint lint-strict build

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install flake8 mypy build

run:
	$(PYTHON) a_maze_ing.py $(CONFIG)

debug:
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .mypy_cache build dist *.egg-info

lint:
	$(BIN)/flake8 .
	$(BIN)/mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(BIN)/flake8 .
	$(BIN)/mypy . --strict

build:
	$(BIN)/python -m build --wheel --outdir .
