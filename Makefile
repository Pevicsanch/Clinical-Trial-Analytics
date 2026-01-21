# Clinical Trial Analytics - Makefile

.PHONY: help install setup etl nb sql check format test qa clean
.DEFAULT_GOAL := help

KERNEL_NAME := clinical-trials
POE := uv run poe

help: ## Show available commands
	@echo "\n📊 Clinical Trial Analytics\n"
	@echo "First time:"
	@echo "  make install  →  make etl  →  make nb"
	@echo ""
	@echo "Commands:"
	@echo "  install   Install dependencies and Jupyter kernel"
	@echo "  setup     Create database schema"
	@echo "  etl       Download and load clinical trial data (~10 min)"
	@echo "  nb        Launch Jupyter notebooks"
	@echo "  sql       Open SQLite console"
	@echo ""
	@echo "Dev:"
	@echo "  check     Lint code"
	@echo "  test      Run tests"
	@echo "  clean     Clean cache files"

# =============================================================================
# Setup
# =============================================================================
install: ## Install dependencies and register Jupyter kernel
	@echo "Installing dependencies..."
	@uv sync --all-groups
	@uv pip install -e . --quiet
	@echo "Registering Jupyter kernel '$(KERNEL_NAME)'..."
	@uv run python -m ipykernel install --user --name=$(KERNEL_NAME) --display-name="Clinical Trials (Python 3.11+)"
	@echo "\n✓ Installation complete"
	@echo "  Next: make setup && make etl"

setup: ## Create database schema
	@$(POE) setup

# =============================================================================
# Data Pipeline
# =============================================================================
etl: ## Extract, transform, and load data from ClinicalTrials.gov
	@$(POE) etl

sql: ## Open SQLite console
	@$(POE) sql

# =============================================================================
# Analysis
# =============================================================================
nb: ## Launch Jupyter notebooks
	@$(POE) nb

# =============================================================================
# Development
# =============================================================================
check: ## Lint code
	@$(POE) check

format: ## Format code
	@$(POE) format

test: ## Run tests
	@$(POE) test

qa: ## Run all quality checks (format + lint + test)
	@$(POE) qa

config: ## Show current configuration
	@$(POE) config

# =============================================================================
# Utilities
# =============================================================================
fix-kernels: ## Update all notebooks to use the correct Jupyter kernel
	@echo "Updating notebook kernels to '$(KERNEL_NAME)'..."
	@for nb in notebooks/*.ipynb; do \
		python3 -c "import json; \
d=json.load(open('$$nb')); \
d['metadata']['kernelspec']={'display_name':'Clinical Trials (Python 3.11+)','language':'python','name':'$(KERNEL_NAME)'}; \
json.dump(d,open('$$nb','w'),indent=1)"; \
	done
	@echo "✓ All notebooks updated"

clean: ## Clean cache files
	@echo "Cleaning..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✓ Done"

uninstall-kernel: ## Remove Jupyter kernel
	@jupyter kernelspec uninstall $(KERNEL_NAME) -y 2>/dev/null || true
	@echo "✓ Kernel '$(KERNEL_NAME)' removed"
