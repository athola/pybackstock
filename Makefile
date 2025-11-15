.PHONY: help lint test typecheck format clean install

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make lint       - Run ruff linter with comprehensive checks"
	@echo "  make format     - Auto-format code with ruff"
	@echo "  make test       - Run pytest test suite"
	@echo "  make typecheck  - Run mypy and ty type checking"
	@echo "  make clean      - Remove cache files"
	@echo "  make all        - Run format, lint, typecheck, and test"

install:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest -v --cov=. --cov-report=term-missing --cov-report=html

typecheck:
	uv run mypy .
	uv run ty check . --ignore invalid-assignment --ignore invalid-return-type --ignore no-matching-overload --ignore invalid-argument-type --exclude migrations --exclude manage.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

all: format lint typecheck test
	@echo "All checks passed!"
