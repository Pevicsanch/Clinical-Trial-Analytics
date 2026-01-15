"""Load transformed data into SQLite database.

Handles insertion with duplicate handling and foreign key relationships.
"""

from pathlib import Path
from typing import Any

import polars as pl
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config.settings import settings


def get_engine() -> Engine:
    """Get SQLAlchemy engine for database connection.

    Returns:
        SQLAlchemy engine instance.
    """
    return create_engine(settings.database_url, echo=settings.db_echo)


def load_studies(studies_data: list[dict[str, Any]], engine: Engine) -> dict[str, int]:
    """Load studies into database and return nct_id to study_id mapping.

    Args:
        studies_data: List of study dictionaries.
        engine: SQLAlchemy engine.

    Returns:
        Dictionary mapping nct_id to study_id.
    """
    logger.info(f"Loading {len(studies_data)} studies")

    nct_id_to_study_id: dict[str, int] = {}

    with engine.connect() as conn:
        # Batch insert for better performance
        batch_size = 100
        studies_to_insert = []

        for study in studies_data:
            nct_id = study.pop("_nct_id")  # Remove temporary key

            # Check if study already exists
            result = conn.execute(
                text("SELECT study_id FROM studies WHERE nct_id = :nct_id"),
                {"nct_id": nct_id},
            )
            existing = result.fetchone()

            if existing:
                # Study exists, use existing study_id
                study_id = existing[0]
                logger.debug(f"Study {nct_id} already exists (study_id: {study_id})")
                nct_id_to_study_id[nct_id] = study_id
            else:
                # Prepare for batch insert
                study["_nct_id"] = nct_id  # Store temporarily for mapping
                studies_to_insert.append(study)

                # Insert in batches
                if len(studies_to_insert) >= batch_size:
                    _insert_studies_batch(conn, studies_to_insert, nct_id_to_study_id)
                    studies_to_insert = []

        # Insert remaining studies
        if studies_to_insert:
            _insert_studies_batch(conn, studies_to_insert, nct_id_to_study_id)

        conn.commit()

    logger.success(f"Loaded {len(nct_id_to_study_id)} studies")
    return nct_id_to_study_id


def _insert_studies_batch(
    conn, studies_batch: list[dict[str, Any]], nct_id_to_study_id: dict[str, int]
):
    """Insert a batch of studies and update nct_id mapping.

    Args:
        conn: Database connection.
        studies_batch: List of study dictionaries to insert.
        nct_id_to_study_id: Dictionary to update with nct_id -> study_id mapping.
    """
    if not studies_batch:
        return

    # Build batch insert
    columns = list(studies_batch[0].keys())
    columns.remove("_nct_id")  # Remove temporary key from columns

    # Insert all studies
    for study in studies_batch:
        nct_id = study.pop("_nct_id")
        columns_str = ", ".join(study.keys())
        placeholders = ", ".join([f":{k}" for k in study.keys()])
        insert_sql = f"""
            INSERT INTO studies ({columns_str})
            VALUES ({placeholders})
        """
        conn.execute(text(insert_sql), study)
        study["_nct_id"] = nct_id  # Restore for mapping

    # Get inserted study_ids
    for study in studies_batch:
        nct_id = study.pop("_nct_id")
        result = conn.execute(
            text("SELECT study_id FROM studies WHERE nct_id = :nct_id"),
            {"nct_id": nct_id},
        )
        study_id = result.fetchone()[0]
        nct_id_to_study_id[nct_id] = study_id
        logger.debug(f"Inserted study {nct_id} (study_id: {study_id})")


def load_conditions(conditions_data: list[dict[str, Any]], engine: Engine) -> int:
    """Load conditions into database.

    Args:
        conditions_data: List of condition dictionaries.
        engine: SQLAlchemy engine.

    Returns:
        Number of conditions inserted.
    """
    if not conditions_data:
        return 0

    logger.info(f"Loading {len(conditions_data)} conditions")

    with engine.connect() as conn:
        for condition in conditions_data:
            columns = ", ".join(condition.keys())
            placeholders = ", ".join([f":{k}" for k in condition.keys()])
            insert_sql = f"""
                INSERT INTO conditions ({columns})
                VALUES ({placeholders})
            """

            conn.execute(text(insert_sql), condition)

        conn.commit()  # Single commit for all conditions

    logger.success(f"Loaded {len(conditions_data)} conditions")
    return len(conditions_data)


def load_locations(locations_data: list[dict[str, Any]], engine: Engine) -> int:
    """Load locations into database.

    Args:
        locations_data: List of location dictionaries.
        engine: SQLAlchemy engine.

    Returns:
        Number of locations inserted.
    """
    if not locations_data:
        return 0

    logger.info(f"Loading {len(locations_data)} locations")

    with engine.connect() as conn:
        for location in locations_data:
            columns = ", ".join(location.keys())
            placeholders = ", ".join([f":{k}" for k in location.keys()])
            insert_sql = f"""
                INSERT INTO locations ({columns})
                VALUES ({placeholders})
            """

            conn.execute(text(insert_sql), location)

        conn.commit()  # Single commit for all locations

    logger.success(f"Loaded {len(locations_data)} locations")
    return len(locations_data)


def load_sponsors(sponsors_data: list[dict[str, Any]], engine: Engine) -> int:
    """Load sponsors into database.

    Args:
        sponsors_data: List of sponsor dictionaries.
        engine: SQLAlchemy engine.

    Returns:
        Number of sponsors inserted.
    """
    if not sponsors_data:
        return 0

    logger.info(f"Loading {len(sponsors_data)} sponsors")

    with engine.connect() as conn:
        for sponsor in sponsors_data:
            columns = ", ".join(sponsor.keys())
            placeholders = ", ".join([f":{k}" for k in sponsor.keys()])
            insert_sql = f"""
                INSERT INTO sponsors ({columns})
                VALUES ({placeholders})
            """

            conn.execute(text(insert_sql), sponsor)

        conn.commit()  # Single commit for all sponsors

    logger.success(f"Loaded {len(sponsors_data)} sponsors")
    return len(sponsors_data)


def load_all(
    studies_data: list[dict[str, Any]],
    conditions_data: list[dict[str, Any]],
    locations_data: list[dict[str, Any]],
    sponsors_data: list[dict[str, Any]],
    engine: Engine | None = None,
) -> dict[str, int]:
    """Load all data into database in correct order.

    Args:
        studies_data: List of study dictionaries.
        conditions_data: List of condition dictionaries.
        locations_data: List of location dictionaries.
        sponsors_data: List of sponsor dictionaries.
        engine: SQLAlchemy engine. If None, creates new engine.

    Returns:
        Dictionary with counts of loaded records.
    """
    if engine is None:
        engine = get_engine()

    logger.info("Starting data load")

    # 1. Load studies first (to get study_id)
    nct_id_to_study_id = load_studies(studies_data, engine)

    # 2. Load related tables
    conditions_count = load_conditions(conditions_data, engine)
    locations_count = load_locations(locations_data, engine)
    sponsors_count = load_sponsors(sponsors_data, engine)

    logger.success("Data load complete")

    return {
        "studies": len(nct_id_to_study_id),
        "conditions": conditions_count,
        "locations": locations_count,
        "sponsors": sponsors_count,
    }
