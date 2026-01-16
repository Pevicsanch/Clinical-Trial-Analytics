"""Unit tests for database schema."""

import sqlite3
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


def test_schema_tables_exist(temp_db):
    """Schema setup should create all required tables."""
    # Setup schema
    schema_file = Path(__file__).parent.parent / "sql" / "schema" / "01_create_tables.sql"

    with open(schema_file, "r") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()

    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}

    required_tables = {
        "studies",
        "conditions",
        "interventions",
        "outcomes",
        "sponsors",
        "locations",
        "study_design",
        "schema_metadata",
    }

    assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"

    conn.close()


def test_schema_views_exist(temp_db):
    """Schema should create expected views."""
    # Setup schema
    schema_file = Path(__file__).parent.parent / "sql" / "schema" / "01_create_tables.sql"

    with open(schema_file, "r") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()

    # Verify views exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = {row[0] for row in cursor.fetchall()}

    assert "v_study_complete" in views

    conn.close()
