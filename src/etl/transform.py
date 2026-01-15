"""Transform raw JSON data to tabular format.

Converts ClinicalTrials.gov API JSON to flat tables for database loading.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl
from loguru import logger


def parse_date(date_str: str | None) -> str | None:
    """Parse date string to YYYY-MM-DD format.

    Handles partial dates (YYYY-MM) by setting day to 01.

    Args:
        date_str: Date string in various formats.

    Returns:
        Date string in YYYY-MM-DD format or None.
    """
    if not date_str:
        return None

    try:
        # Handle YYYY-MM format
        if len(date_str) == 7 and date_str[4] == "-":
            return f"{date_str}-01"

        # Handle YYYY-MM-DD format
        if len(date_str) == 10:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str

        # Try parsing other formats
        for fmt in ["%Y-%m-%d", "%Y-%m", "%Y"]:
            try:
                dt = datetime.strptime(date_str[:10], fmt)
                if fmt == "%Y":
                    return f"{date_str[:4]}-01-01"
                elif fmt == "%Y-%m":
                    return f"{date_str[:7]}-01"
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None
    except Exception as e:
        logger.warning(f"Error parsing date {date_str}: {str(e)}")
        return None


def parse_phase(phase_list: list[str] | None) -> str | None:
    """Parse phase list to comma-separated string.

    Args:
        phase_list: List of phase strings.

    Returns:
        Comma-separated string or None.
    """
    if not phase_list:
        return None
    return ", ".join(phase_list)


def transform_study(study: dict[str, Any]) -> dict[str, Any]:
    """Transform a single study record to studies table format.

    Args:
        study: Raw study JSON from API.

    Returns:
        Dictionary with studies table fields.
    """
    protocol_section = study.get("protocolSection", {})
    identification = protocol_section.get("identificationModule", {})
    status = protocol_section.get("statusModule", {})
    design = protocol_section.get("designModule", {})
    eligibility = protocol_section.get("eligibilityModule", {})
    description = protocol_section.get("descriptionModule", {})

    # Extract dates
    start_date = status.get("startDateStruct", {}).get("date")
    completion_date = status.get("completionDateStruct", {}).get("date")
    primary_completion_date = status.get("primaryCompletionDateStruct", {}).get("date")

    # Extract enrollment (from designModule, not statusModule)
    enrollment_info = design.get("enrollmentInfo", {})
    enrollment = enrollment_info.get("count")
    enrollment_type = enrollment_info.get("type")

    return {
        "nct_id": identification.get("nctId"),
        "acronym": identification.get("acronym"),
        "title": identification.get("briefTitle"),
        "brief_summary": description.get("briefSummary"),
        "status": status.get("overallStatus"),
        "phase": parse_phase(design.get("phases")),
        "study_type": design.get("studyType"),
        "start_date": parse_date(start_date),
        "completion_date": parse_date(completion_date),
        "primary_completion_date": parse_date(primary_completion_date),
        "enrollment": enrollment if enrollment else None,
        "enrollment_type": enrollment_type,
    }


def transform_conditions(study: dict[str, Any], study_id: int) -> list[dict[str, Any]]:
    """Transform conditions for a study.

    Args:
        study: Raw study JSON from API.
        study_id: Foreign key to studies table.

    Returns:
        List of condition dictionaries.
    """
    protocol_section = study.get("protocolSection", {})
    conditions_module = protocol_section.get("conditionsModule", {})
    conditions_list = conditions_module.get("conditions", [])

    result = []
    for condition in conditions_list:
        result.append(
            {
                "study_id": study_id,
                "condition_name": condition,
                "mesh_term": None,  # Not available in v2 API
            }
        )

    return result


def transform_locations(study: dict[str, Any], study_id: int) -> list[dict[str, Any]]:
    """Transform locations for a study.

    Args:
        study: Raw study JSON from API.
        study_id: Foreign key to studies table.

    Returns:
        List of location dictionaries.
    """
    protocol_section = study.get("protocolSection", {})
    contacts = protocol_section.get("contactsLocationsModule", {})
    locations_list = contacts.get("locations", [])

    result = []
    for location in locations_list:
        facility = location.get("facility")
        city = location.get("city")
        state = location.get("state")
        zip_code = location.get("zip")
        country = location.get("country")
        location_status = location.get("status")

        result.append(
            {
                "study_id": study_id,
                "facility": facility,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "country": country,
                "continent": None,  # Can be derived later
                "status": location_status,
            }
        )

    return result


def transform_sponsors(study: dict[str, Any], study_id: int) -> list[dict[str, Any]]:
    """Transform sponsors for a study.

    Args:
        study: Raw study JSON from API.
        study_id: Foreign key to studies table.

    Returns:
        List of sponsor dictionaries.
    """
    protocol_section = study.get("protocolSection", {})
    sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
    lead_sponsor = sponsor_module.get("leadSponsor", {})
    collaborators = sponsor_module.get("collaborators", [])

    result = []

    # Lead sponsor
    if lead_sponsor.get("name"):
        result.append(
            {
                "study_id": study_id,
                "agency": lead_sponsor.get("name"),
                "agency_class": lead_sponsor.get("class"),
                "lead_or_collaborator": "Lead",
            }
        )

    # Collaborators
    for collaborator in collaborators:
        if collaborator.get("name"):
            result.append(
                {
                    "study_id": study_id,
                    "agency": collaborator.get("name"),
                    "agency_class": collaborator.get("class"),
                    "lead_or_collaborator": "Collaborator",
                }
            )

    return result


def transform_raw_data(data_file: Path) -> dict[str, pl.DataFrame]:
    """Transform raw JSONL file to tabular DataFrames.

    Args:
        data_file: Path to JSONL file with raw studies.

    Returns:
        Dictionary with keys: 'studies', 'conditions', 'locations', 'sponsors'.
    """
    logger.info(f"Transforming raw data from {data_file}")

    studies_list = []
    conditions_list = []
    locations_list = []
    sponsors_list = []

    with open(data_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                study = json.loads(line.strip())
                nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")

                if not nct_id:
                    logger.warning(f"Line {line_num}: Missing nct_id, skipping")
                    continue

                # Transform study (will get study_id after insert)
                study_data = transform_study(study)
                studies_list.append(study_data)

                # Store nct_id for later mapping
                study_data["_nct_id"] = nct_id

            except json.JSONDecodeError as e:
                logger.error(f"Line {line_num}: JSON decode error: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Line {line_num}: Error transforming study: {str(e)}")
                continue

    logger.info(f"Transformed {len(studies_list)} studies")

    # Create DataFrames
    studies_df = pl.DataFrame(studies_list)

    # For now, we'll return the raw lists and create DataFrames after we have study_id
    # We need to insert studies first to get study_id, then transform related tables
    return {
        "studies": studies_df,
        "studies_raw": studies_list,  # Keep raw for second pass
    }


def transform_related_tables(
    data_file: Path, nct_id_to_study_id: dict[str, int]
) -> dict[str, list[dict[str, Any]]]:
    """Transform related tables (conditions, locations, sponsors) after studies are loaded.

    Args:
        data_file: Path to JSONL file with raw studies.
        nct_id_to_study_id: Mapping from nct_id to study_id.

    Returns:
        Dictionary with 'conditions', 'locations', 'sponsors' lists.
    """
    logger.info("Transforming related tables")

    conditions_list = []
    locations_list = []
    sponsors_list = []

    with open(data_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                study = json.loads(line.strip())
                nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")

                if not nct_id:
                    continue

                study_id = nct_id_to_study_id.get(nct_id)
                if not study_id:
                    logger.warning(f"Study {nct_id} not found in mapping")
                    continue

                # Transform related tables
                conditions_list.extend(transform_conditions(study, study_id))
                locations_list.extend(transform_locations(study, study_id))
                sponsors_list.extend(transform_sponsors(study, study_id))

            except Exception as e:
                logger.error(f"Line {line_num}: Error: {str(e)}")
                continue

    logger.info(
        f"Transformed: {len(conditions_list)} conditions, "
        f"{len(locations_list)} locations, {len(sponsors_list)} sponsors"
    )

    return {
        "conditions": conditions_list,
        "locations": locations_list,
        "sponsors": sponsors_list,
    }
