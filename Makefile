.PHONY: test lint format check build

test:
	python -m pytest

lint:
	ruff check src tests

format:
	ruff check --fix src tests
	ruff format src tests

check:
	ruff check src tests
	ruff format --check src tests
	python -m pytest

build:
	python -m build
