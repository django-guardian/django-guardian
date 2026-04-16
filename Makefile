.PHONY: help build pytest test test-all clean install dev-install lint format docs docs-serve check

help:
	@echo "Available commands:"
	@echo "  build        - Build the package"
	@echo "  pytest       - Run tests with pytest"
	@echo "  test         - Alias for pytest"
	@echo "  test-all     - Run the full tox matrix"
	@echo "  clean        - Clean build artifacts"
	@echo "  install      - Sync project dependencies"
	@echo "  dev-install  - Sync project with development dependencies"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Apply Ruff fixes and format code"
	@echo "  docs         - Build documentation"
	@echo "  docs-serve   - Serve documentation locally"
	@echo "  check        - Run lint, tests, and docs build"

# Build the package
build:
	uv build

# Run tests with pytest
pytest:
	uv run pytest --cov=guardian --cov-report=xml --cov-report=term

# Alias for pytest
test: pytest

# Run the full tox matrix
test-all:
	uv run tox run

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .tox/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Sync the default project environment
install:
	uv sync

# Sync the development environment
dev-install:
	uv sync --group dev

# Run linting checks
lint:
	uv run ruff check .
	uv run mypy ./guardian

# Apply auto-fixes and format code
format:
	uv run ruff check --fix .
	uv run ruff format .

# Build documentation
docs:
	uv run mkdocs build

# Serve documentation locally
docs-serve:
	uv run mkdocs serve

# Run the most common local checks
check:
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) docs
