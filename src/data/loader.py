"""
Data loading utilities for clinical trial analysis.

This module provides functions for loading SQL queries and connecting
to the analysis database.
"""

import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd


def load_sql_query(
    query_name: str,
    conn: sqlite3.Connection,
    sql_path: Path,
    params: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Load and execute a SQL query from a file.
    
    Parameters:
    -----------
    query_name : Name of the SQL file (e.g., 'q1_study_base.sql')
    conn : SQLite database connection
    sql_path : Path to the queries folder
    params : Optional dict of parameters for parameterized queries
    
    Returns:
    --------
    DataFrame with query results
    
    Raises:
    -------
    FileNotFoundError : If the SQL file doesn't exist
    ValueError : If the SQL file is empty
    AssertionError : If the query returns no rows
    """
    query_path = sql_path / query_name
    if not query_path.exists():
        raise FileNotFoundError(f"SQL file not found: {query_path}")
    
    with open(query_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Remove trailing semicolon for parameterized queries (SQLite requirement)
    sql = sql.rstrip().rstrip(';')
    
    if not sql.strip():
        raise ValueError(f"SQL file is empty: {query_path}")
    
    df = pd.read_sql_query(sql, conn, params=params)
    assert not df.empty, f"Query returned no rows: {query_name}"
    return df


def get_db_connection(db_path: Path, read_only: bool = True) -> sqlite3.Connection:
    """
    Create a database connection with validation.
    
    Parameters:
    -----------
    db_path : Path to the SQLite database file
    read_only : If True, open in read-only mode (prevents accidental writes)
    
    Returns:
    --------
    SQLite connection object
    
    Raises:
    -------
    AssertionError : If the database file doesn't exist
    """
    assert db_path.exists(), f"Database not found at {db_path}"
    if read_only:
        # URI mode with read-only flag
        uri = f"file:{db_path}?mode=ro"
        return sqlite3.connect(uri, uri=True)
    return sqlite3.connect(str(db_path))
