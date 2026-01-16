"""Unit tests for ETL load functions."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_db():
    """Create a temporary database with schema."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    # Setup schema
    schema_file = Path(__file__).parent.parent / "sql" / "schema" / "01_create_tables.sql"
    with open(schema_file, "r") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_jsonl():
    """Create a sample JSONL file with test data."""
    sample_data = [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000001",
                    "briefTitle": "Test Study 1",
                },
                "statusModule": {
                    "overallStatus": "COMPLETED",
                    "startDateStruct": {"date": "2020-01"},
                },
                "designModule": {
                    "phases": ["PHASE2"],
                    "studyType": "INTERVENTIONAL",
                    "enrollmentInfo": {"count": 100, "type": "Actual"},
                },
                "conditionsModule": {
                    "conditions": ["Diabetes", "Obesity"],
                },
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "facility": "Test Hospital",
                            "city": "New York",
                            "country": "United States",
                        }
                    ]
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Test Pharma", "class": "INDUSTRY"},
                },
                "descriptionModule": {"briefSummary": "Test summary"},
            }
        }
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for record in sample_data:
            f.write(json.dumps(record) + "\n")
        jsonl_path = Path(f.name)

    yield jsonl_path

    # Cleanup
    if jsonl_path.exists():
        jsonl_path.unlink()


def test_no_orphan_foreign_keys(temp_db, sample_jsonl):
    """After loading, there should be no orphan foreign keys."""
    from src.etl.load import get_engine, load_conditions, load_locations, load_sponsors, load_studies
    from src.etl.transform import transform_raw_data, transform_related_tables

    # Override database path temporarily
    import src.config.settings as settings_module
    original_db_path = settings_module.settings.db_path
    settings_module.settings.db_path = str(temp_db)

    try:
        # Transform and load data
        engine = get_engine()
        transform_result = transform_raw_data(sample_jsonl)
        studies_data = transform_result["studies_raw"]

        # Load studies
        nct_id_to_study_id = load_studies(studies_data, engine)

        # Transform and load related tables
        related_data = transform_related_tables(sample_jsonl, nct_id_to_study_id)
        load_conditions(related_data["conditions"], engine)
        load_locations(related_data["locations"], engine)
        load_sponsors(related_data["sponsors"], engine)

        # Verify no orphan foreign keys
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()

        # Check conditions
        cursor.execute("""
            SELECT COUNT(*) FROM conditions c
            WHERE NOT EXISTS (SELECT 1 FROM studies s WHERE s.study_id = c.study_id)
        """)
        orphan_conditions = cursor.fetchone()[0]
        assert orphan_conditions == 0, f"Found {orphan_conditions} orphan conditions"

        # Check locations
        cursor.execute("""
            SELECT COUNT(*) FROM locations l
            WHERE NOT EXISTS (SELECT 1 FROM studies s WHERE s.study_id = l.study_id)
        """)
        orphan_locations = cursor.fetchone()[0]
        assert orphan_locations == 0, f"Found {orphan_locations} orphan locations"

        # Check sponsors
        cursor.execute("""
            SELECT COUNT(*) FROM sponsors sp
            WHERE NOT EXISTS (SELECT 1 FROM studies s WHERE s.study_id = sp.study_id)
        """)
        orphan_sponsors = cursor.fetchone()[0]
        assert orphan_sponsors == 0, f"Found {orphan_sponsors} orphan sponsors"

        conn.close()

    finally:
        # Restore original settings
        settings_module.settings.db_path = original_db_path
