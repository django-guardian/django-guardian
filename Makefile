.PHONY: help build pytest test clean install dev-install lint format docs

help:
	@echo "Available commands:"
	@echo "  build        - Build the package"
	@echo "  pytest       - Run tests with pytest"
	@echo "  test         - Alias for pytest"
	@echo "  clean        - Clean build artifacts"
	@echo "  install      - Install the package"
	@echo "  dev-install  - Install package in development mode with dev dependencies"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code"
	@echo "  docs         - Build documentation"

# Build the package
build:
	uv build

# Run tests with pytest
pytest:
	pytest --cov=guardian --cov-report=xml --cov-report=term

# Alias for pytest
test: pytest

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Install the package
install:
	uv pip install .

# Install in development mode with dev dependencies
dev-install:
	uv pip install -e . --group dev

# Run linting checks
lint:
	ruff check .
	mypy ./guardian

# Format code
format:
	ruff format .

# Build documentation
docs:
	mkdocs build
