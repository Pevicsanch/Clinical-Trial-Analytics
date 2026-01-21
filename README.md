# Clinical Trial Analytics

Exploratory analysis of clinical trial data from [ClinicalTrials.gov](https://clinicaltrials.gov), the largest public registry of clinical studies.

This project extracts trial metadata via the ClinicalTrials.gov API, loads it into a local SQLite database, and provides Jupyter notebooks that investigate patterns in trial design, completion, enrollment, geography, and duration.

## Quick Start

### Option 1: Docker (recommended)

```bash
git clone <repo-url>
cd Clinical-Trial-Analytics

docker compose up
```

Open http://localhost:8888 (token: `clinical-trials`)

On first run, the container automatically downloads and loads ~100K trials from ClinicalTrials.gov (~10 minutes). Subsequent starts are instant.

### Option 2: Local installation

Requires Python 3.11+ and [uv](https://github.com/astral-sh/uv).

```bash
make install    # Install dependencies + Jupyter kernel
make setup      # Create database schema
make etl        # Download and load data (~10 min)
make nb         # Launch Jupyter
```

## Research Questions

Each notebook addresses a specific analytical question:

| # | Question | Notebook |
|---|----------|----------|
| 1 | **Trial Landscape:** What is the distribution of trials by phase, status, and therapeutic area? How has this evolved over time? | `01_trial_landscape_v2` |
| 2 | **Completion Analysis:** Which factors are associated with higher completion rates? What patterns appear in terminated or withdrawn trials? | `02_completion_analysis` |
| 3 | **Enrollment Performance:** What are the trends in patient enrollment? Which conditions attract the most participants? | `03_enrollment_performance` |
| 4 | **Geographic Insights:** How are trials distributed globally? Are there regional specializations in therapeutic areas? | `04_geographic_insights` |
| 5 | **Duration Analysis:** What is the typical trial duration by phase? Which trials take significantly longer than expected? | `05_duration_analysis` |

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

make test         # Run tests (12 unit tests)
make check        # Lint code (ruff)
make clean        # Remove cache files
```

## Data Source

All data comes from the [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api). The API is public and requires no authentication. By default, the ETL fetches up to 100,000 studies; this can be adjusted via `--max-records`.

## Notes

- The database is SQLite — portable and requires no server setup
- Notebooks use Plotly for interactive charts
- Analysis is descriptive; causal claims require additional study design information not available in registry data
- See [DEVELOPMENT.md](DEVELOPMENT.md) for notes on the development process and AI-assisted workflow

