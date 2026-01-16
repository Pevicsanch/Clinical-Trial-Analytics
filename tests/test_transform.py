"""Unit tests for ETL transform functions."""

import pytest

from src.etl.transform import parse_date, parse_phase


class TestDateParsing:
    """Test date parsing logic."""

    def test_parse_date_yyyy_mm_format(self):
        """YYYY-MM format should become YYYY-MM-01."""
        assert parse_date("2023-06") == "2023-06-01"
        assert parse_date("2020-01") == "2020-01-01"
        assert parse_date("2021-12") == "2021-12-01"

    def test_parse_date_yyyy_mm_dd_format(self):
        """YYYY-MM-DD format should remain unchanged."""
        assert parse_date("2023-06-15") == "2023-06-15"
        assert parse_date("2020-01-01") == "2020-01-01"

    def test_parse_date_yyyy_format(self):
        """YYYY format should become YYYY-01-01."""
        assert parse_date("2023") == "2023-01-01"
        assert parse_date("2020") == "2020-01-01"

    def test_parse_date_none_and_empty(self):
        """None and empty strings should return None."""
        assert parse_date(None) is None
        assert parse_date("") is None

    def test_parse_date_invalid(self):
        """Invalid dates should return None."""
        assert parse_date("invalid-date") is None
        assert parse_date("2023-13-01") is None  # Invalid month


class TestPhaseParsing:
    """Test phase parsing logic."""

    def test_parse_phase_single(self):
        """Single phase should be returned as-is."""
        assert parse_phase(["PHASE1"]) == "PHASE1"
        assert parse_phase(["PHASE2"]) == "PHASE2"
        assert parse_phase(["NA"]) == "NA"

    def test_parse_phase_multiple(self):
        """Multiple phases should be joined with comma."""
        assert parse_phase(["PHASE1", "PHASE2"]) == "PHASE1, PHASE2"
        assert parse_phase(["PHASE2", "PHASE3"]) == "PHASE2, PHASE3"

    def test_parse_phase_none_and_empty(self):
        """None and empty list should return None."""
        assert parse_phase(None) is None
        assert parse_phase([]) is None

    def test_parse_phase_early_phase(self):
        """Early phase should be handled correctly."""
        assert parse_phase(["EARLY_PHASE1"]) == "EARLY_PHASE1"
