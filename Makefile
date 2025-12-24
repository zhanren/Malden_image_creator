.PHONY: help test test-verbose test-cov test-fast lint lint-fix format clean install dev-install test-all pre-commit git-status git-diff git-commit git-push git-pull

# Default target
help:
	@echo "Available commands:"
	@echo "  make test          - Run all tests"
	@echo "  make test-verbose  - Run tests with verbose output"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make lint          - Run linter (ruff)"
	@echo "  make lint-fix      - Run linter with auto-fix"
	@echo "  make format        - Format code (ruff)"
	@echo "  make clean         - Clean build artifacts and cache"
	@echo "  make install       - Install package in development mode"
	@echo "  make dev-install   - Install with dev dependencies"
	@echo ""
	@echo "Combined workflows:"
	@echo "  make test-all      - Run lint + tests"
	@echo "  make pre-commit    - Format + lint-fix + test (pre-commit checks)"
	@echo ""
	@echo "Git commands:"
	@echo "  make git-status    - Show git status"
	@echo "  make git-diff      - Show git diff"
	@echo "  make git-commit    - Commit changes (use MSG='message')"
	@echo "  make git-push      - Push to remote"
	@echo "  make git-pull      - Pull from remote"

# Test commands
test:
	@echo "Running tests..."
	pytest

test-verbose:
	@echo "Running tests with verbose output..."
	pytest -v

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=imgcreator --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

test-fast:
	@echo "Running fast tests (no coverage)..."
	pytest -x --tb=short

# Linting and formatting
lint:
	@echo "Running linter..."
	ruff check imgcreator/ tests/

lint-fix:
	@echo "Running linter with auto-fix..."
	ruff check --fix imgcreator/ tests/

format:
	@echo "Formatting code..."
	ruff format imgcreator/ tests/

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

# Installation
install:
	@echo "Installing package..."
	pip install -e .

dev-install:
	@echo "Installing with dev dependencies..."
	pip install -e ".[dev]"

# Git commands
git-status:
	@echo "Git status:"
	@git status

git-diff:
	@echo "Git diff:"
	@git diff

git-commit:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make git-commit MSG='your message'"; \
		exit 1; \
	fi
	@echo "Committing changes..."
	@git add .
	@git commit -m "$(MSG)"
	@echo "Committed: $(MSG)"

git-push:
	@echo "Pushing to remote..."
	@git push
	@echo "Push complete!"

git-pull:
	@echo "Pulling from remote..."
	@git pull
	@echo "Pull complete!"

# Combined workflows
test-all: lint test
	@echo "All checks passed!"

pre-commit: format lint-fix test
	@echo "Pre-commit checks complete!"

