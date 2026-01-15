# Clinical Trial Analytics - Makefile

.PHONY: help setup config etl db sql nb check format test qa clean install
.DEFAULT_GOAL := help

POE := uv run poe

help: ## Show available commands
	@echo "\n📊 Clinical Trial Analytics\n"
	@echo "Quick start:"
	@echo "  make setup  →  make etl  →  make nb"
	@echo ""
	@echo "Commands:"
	@echo "  setup     First-time setup (create database)"
	@echo "  etl       Extract, transform, and load data"
	@echo "  nb        Launch Jupyter notebooks"
	@echo "  sql       Open SQLite console"
	@echo ""
	@echo "Dev:"
	@echo "  check     Lint code"
	@echo "  qa        Run all checks"
	@echo "  clean     Clean cache"

# Setup
setup: ## First-time setup
	@$(POE) setup

config: ## Show configuration
	@$(POE) config

# Data
etl: ## Extract, transform, and load data
	@$(POE) etl

db: ## Create database (alias for setup)
	@$(POE) build-db

sql: ## Open SQLite console
	@$(POE) sql

# Analysis
nb: ## Launch notebooks
	@$(POE) nb

# Development
check: ## Lint code
	@$(POE) check

format: ## Format code
	@$(POE) format

test: ## Run tests
	@$(POE) test

qa: ## Run quality checks
	@$(POE) qa

# Utilities
clean: ## Clean cache
	@echo "Cleaning cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf htmlcov/ .coverage
	@echo "✓ Done"

install: ## Install dependencies
	@echo "Syncing dependencies..."
	@uv sync --all-groups
	@uv pip install -e .
	@echo "✓ Done"
