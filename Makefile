.PHONY: all test coverage lint format clean install dev help

# Default target
all: lint test

# Run all tests
test:
	@echo "Running tests..."
	uv run pytest

# Run tests with verbose output
test-verbose:
	@echo "Running tests with verbose output..."
	uv run pytest -v

# Run specific test file or pattern
test-filter:
	@echo "Running tests matching pattern $(PATTERN)..."
	uv run pytest -k "$(PATTERN)"

# Generate coverage report
coverage:
	@echo "Running tests with coverage..."
	uv run pytest --cov=obs_cli --cov-report=html --cov-report=term

# Open coverage report in browser
coverage-html: coverage
	@echo "Opening coverage report..."
	@open htmlcov/index.html || xdg-open htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html manually"

# Run linting
lint:
	@echo "Running linter..."
	uv run ruff check .

# Format code
format:
	@echo "Formatting code..."
	uv run ruff format .

# Check formatting without applying changes
format-check:
	@echo "Checking code formatting..."
	uv run ruff format --check .

# Clean up generated files
clean:
	@echo "Cleaning up..."
	rm -rf htmlcov .coverage .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv sync

# Install dev dependencies and pre-commit hooks
dev: install
	@echo "Setting up development environment..."
	uv sync --dev
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
	else \
		echo "pre-commit not found, skipping hook installation"; \
	fi

# Run the CLI
run:
	@echo "Running obs-cli..."
	uv run obs-dquery $(ARGS)

# Build the project
build:
	@echo "Building project..."
	uv build

# Help target
help:
	@echo "Available targets:"
	@echo "  make test          - Run all tests"
	@echo "  make test-verbose  - Run tests with verbose output"
	@echo "  make test-filter PATTERN=<pattern> - Run tests matching pattern"
	@echo "  make coverage      - Run tests with coverage report"
	@echo "  make coverage-html - Generate and open HTML coverage report"
	@echo "  make lint          - Run code linter"
	@echo "  make format        - Format code"
	@echo "  make format-check  - Check code formatting"
	@echo "  make clean         - Remove generated files"
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Set up development environment"
	@echo "  make run ARGS=<args> - Run the CLI with arguments"
	@echo "  make build         - Build the project"
	@echo "  make all           - Run lint and test (default)"