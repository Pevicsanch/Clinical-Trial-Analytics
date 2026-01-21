# Clinical Trial Analytics

Exploratory analysis of clinical trial data from [ClinicalTrials.gov](https://clinicaltrials.gov), the largest public registry of clinical studies.

This project extracts trial metadata via the ClinicalTrials.gov API, loads it into a local SQLite database, and provides a series of Jupyter notebooks that investigate patterns in trial design, completion, enrollment, geography, and duration.

## Quick Start

```bash
# 1. Install dependencies and set up Jupyter kernel
make install

# 2. Create database schema
make setup

# 3. Download and load data (~10 minutes, ~100K trials)
make etl

# 4. Launch notebooks
make nb
```

## What's Inside

### Notebooks

| Notebook | Focus |
|----------|-------|
| `01_trial_landscape_v2` | Overview of trial phases, status distribution, and therapeutic areas |
| `02_completion_analysis` | Completion vs. termination rates by phase and sponsor type |
| `03_enrollment_performance` | Target vs. actual enrollment; factors associated with under-enrollment |
| `04_geographic_insights` | Geographic concentration (HHI), country-level distribution, temporal shifts |
| `05_duration_analysis` | Trial duration modeling with survival analysis (Kaplan-Meier, Cox PH) |

Each notebook is self-contained with its own data loading, analysis, and interpretation.

### Data Pipeline

The ETL process:

1. **Extract** — Fetches study records from the ClinicalTrials.gov API (paginated, handles rate limits)
2. **Transform** — Parses nested JSON into normalized tables (studies, conditions, locations, sponsors)
3. **Load** — Inserts into SQLite with referential integrity
4. **Validate** — Checks for duplicates, orphan foreign keys, date consistency

Run `make etl` to execute the full pipeline. Data is stored locally in `data/database/clinical_trials.db`.

## Project Structure

```
├── notebooks/          # Jupyter notebooks (analysis)
├── sql/
│   ├── schema/         # Table definitions, indexes, views
│   └── queries/        # Reusable SQL for each notebook
├── src/
│   ├── etl/            # Extract, transform, load, validate
│   ├── data/           # API client, data loaders
│   ├── analysis/       # Shared metrics, constants, visualization helpers
│   └── config/         # Settings (paths, API config)
├── scripts/            # CLI entry points (run_etl.py, setup_database_simple.py)
├── tests/              # Unit tests for transforms and schema
└── Makefile            # All commands
```

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

Dependencies are managed in `pyproject.toml`. Key libraries: `polars`, `pandas`, `sqlalchemy`, `plotly`, `statsmodels`, `lifelines`.

## Available Commands

```bash
make install      # Install dependencies + register Jupyter kernel
make setup        # Create empty database with schema
make etl          # Run full ETL pipeline
make nb           # Launch Jupyter notebooks

make check        # Lint code (ruff)
make test         # Run tests (pytest)
make clean        # Remove cache files
make fix-kernels  # Update all notebooks to correct kernel
```

## Data Source

All data comes from the [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api). The API is public and requires no authentication. By default, the ETL fetches up to 100,000 studies; this can be adjusted via `--max-records`.

## Notes

- The database is SQLite — portable and requires no server setup
- Notebooks use Plotly for interactive charts
- Analysis is descriptive; causal claims require additional study design information not available in registry data

## License

MIT
