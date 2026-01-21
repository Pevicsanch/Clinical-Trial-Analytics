#!/bin/bash
set -e

DB_PATH="data/database/clinical_trials.db"

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║     Clinical Trial Analytics               ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check if database exists and has data
if [ ! -f "$DB_PATH" ] || [ ! -s "$DB_PATH" ]; then
    echo "📦 First run detected. Setting up database..."
    echo ""
    
    echo "→ Creating database schema..."
    uv run python scripts/setup_database_simple.py
    
    echo ""
    echo "→ Downloading data from ClinicalTrials.gov..."
    echo "  (This takes ~10 minutes on first run)"
    echo ""
    uv run python scripts/run_etl.py
    
    echo ""
    echo "✓ Setup complete!"
    echo ""
else
    echo "✓ Database found ($(du -h $DB_PATH | cut -f1))"
    echo ""
fi

echo "════════════════════════════════════════════════════════════"
echo ""
echo "  ✓ Ready! Open your browser:"
echo ""
echo "    URL:   http://localhost:8888"
echo "    Token: clinical-trials"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

exec uv run jupyter notebook \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --allow-root \
    --NotebookApp.token='clinical-trials' \
    --NotebookApp.notebook_dir='notebooks' \
    --log-level=WARN
