# Tests

Minimal high-signal unit tests for core ETL functionality.

## Running Tests

```bash
# Run all tests (verbose)
pytest tests/ -v

# Run all tests (quiet)
pytest tests/ -q

# Run with coverage
pytest tests/ --cov=src
```

## Test Coverage

### `test_transform.py`
- **Date parsing:** YYYY-MM → YYYY-MM-01, YYYY → YYYY-01-01
- **Phase parsing:** Single/multiple phases, None/empty handling

### `test_schema.py`
- **Schema smoke test:** Verify all tables and views exist after schema creation

### `test_load.py`
- **FK integrity:** No orphan foreign keys after loading sample data

## Design Principles

- **Fast:** All tests complete in < 1 second
- **Deterministic:** No external API calls, no randomness
- **Isolated:** Use temporary databases and fixtures
- **High signal:** Test critical transform logic and data integrity
