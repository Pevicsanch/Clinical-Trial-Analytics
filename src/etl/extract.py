"""Extract raw data from ClinicalTrials.gov API.

Saves raw JSON data to data/raw/ directory.
"""

from pathlib import Path

from loguru import logger

from src.config.settings import settings
from src.data.api_client import ClinicalTrialsAPI


def extract_raw_data(max_records: int | None = None) -> tuple[Path, Path]:
    """Extract raw data from API and save to disk.

    Args:
        max_records: Maximum number of records to fetch.

    Returns:
        Tuple of (data_file_path, metadata_file_path).
    """
    logger.info("Starting data extraction")

    output_dir = settings.raw_data_dir
    max_records = max_records or settings.api_max_records

    with ClinicalTrialsAPI() as api:
        data_file, metadata_file = api.save_raw_data(output_dir, max_records)

    logger.success(f"Extraction complete: {data_file.name}")
    return data_file, metadata_file
