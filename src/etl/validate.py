"""Validate loaded data with basic checks.

Performs data quality checks on loaded database.
"""

from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from loguru import logger

from src.config.settings import settings


def validate_data(engine: Engine | None = None) -> dict[str, Any]:
    """Run validation checks on loaded data.

    Args:
        engine: SQLAlchemy engine. If None, creates new engine.

    Returns:
        Dictionary with validation results.
    """
    if engine is None:
        engine = create_engine(settings.database_url, echo=False)

    logger.info("Running data validation checks")

    results: dict[str, Any] = {}

    with engine.connect() as conn:
        # 1. Count checks
        studies_count = conn.execute(text("SELECT COUNT(*) FROM studies")).scalar()
        conditions_count = conn.execute(text("SELECT COUNT(*) FROM conditions")).scalar()
        locations_count = conn.execute(text("SELECT COUNT(*) FROM locations")).scalar()
        sponsors_count = conn.execute(text("SELECT COUNT(*) FROM sponsors")).scalar()

        results["counts"] = {
            "studies": studies_count,
            "conditions": conditions_count,
            "locations": locations_count,
            "sponsors": sponsors_count,
        }

        # 2. Uniqueness check
        unique_nct_ids = conn.execute(
            text("SELECT COUNT(DISTINCT nct_id) FROM studies")
        ).scalar()
        results["uniqueness"] = {
            "unique_nct_ids": unique_nct_ids,
            "total_studies": studies_count,
            "is_unique": unique_nct_ids == studies_count,
        }

        # 3. Date checks
        start_date_not_null = conn.execute(
            text("SELECT COUNT(*) FROM studies WHERE start_date IS NOT NULL")
        ).scalar()
        start_date_pct = (
            (start_date_not_null / studies_count * 100) if studies_count > 0 else 0
        )

        # Check date consistency
        date_consistency = conn.execute(
            text("""
                SELECT COUNT(*) FROM studies
                WHERE completion_date IS NOT NULL
                  AND start_date IS NOT NULL
                  AND completion_date < start_date
            """)
        ).scalar()

        results["dates"] = {
            "start_date_not_null": start_date_not_null,
            "start_date_pct": round(start_date_pct, 2),
            "date_inconsistencies": date_consistency,
        }

        # 4. Foreign key checks
        orphaned_conditions = conn.execute(
            text("""
                SELECT COUNT(*) FROM conditions c
                LEFT JOIN studies s ON c.study_id = s.study_id
                WHERE s.study_id IS NULL
            """)
        ).scalar()

        orphaned_locations = conn.execute(
            text("""
                SELECT COUNT(*) FROM locations l
                LEFT JOIN studies s ON l.study_id = s.study_id
                WHERE s.study_id IS NULL
            """)
        ).scalar()

        orphaned_sponsors = conn.execute(
            text("""
                SELECT COUNT(*) FROM sponsors sp
                LEFT JOIN studies s ON sp.study_id = s.study_id
                WHERE s.study_id IS NULL
            """)
        ).scalar()

        results["foreign_keys"] = {
            "orphaned_conditions": orphaned_conditions,
            "orphaned_locations": orphaned_locations,
            "orphaned_sponsors": orphaned_sponsors,
        }

    # Log results
    logger.info("Validation results:")
    logger.info(f"  Studies: {results['counts']['studies']}")
    logger.info(f"  Conditions: {results['counts']['conditions']}")
    logger.info(f"  Locations: {results['counts']['locations']}")
    logger.info(f"  Sponsors: {results['counts']['sponsors']}")
    logger.info(f"  Unique NCT IDs: {results['uniqueness']['is_unique']}")
    logger.info(f"  Start date coverage: {results['dates']['start_date_pct']}%")
    logger.info(f"  Date inconsistencies: {results['dates']['date_inconsistencies']}")

    return results
