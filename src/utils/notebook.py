"""
Notebook utilities for clinical trial analysis.

Helpers for managing notebook execution, dependency validation, and common patterns
used across Q2, Q3, Q4 notebooks.
"""

from __future__ import annotations

from pathlib import Path


def find_project_root(
    start: Path | None = None,
    markers: tuple[str, ...] = ("pyproject.toml", ".git"),
) -> Path:
    """
    Walk up from `start` until a marker file/directory is found.
    
    Parameters:
    -----------
    start : Starting path (default: current working directory)
    markers : Tuple of filenames to look for (default: pyproject.toml, .git)
    
    Returns:
    --------
    Path to project root directory
    
    Raises:
    -------
    FileNotFoundError if no marker is found
    
    Example:
    --------
    >>> PROJECT_ROOT = find_project_root()
    >>> sys.path.insert(0, str(PROJECT_ROOT))
    """
    start = start or Path.cwd()
    for p in [start, *start.parents]:
        if any((p / m).exists() for m in markers):
            return p
    raise FileNotFoundError(
        f"Project root not found. Looked for markers {markers} from {start}. "
        "Run the notebook from within the repo or adjust root detection."
    )


def check_dependencies(
    required_vars: dict[str, str],
    required_cols: dict[str, set] | None = None,
    caller_globals: dict | None = None,
) -> None:
    """
    Validate that required variables exist and DataFrames have required columns.
    
    Use at the start of notebook cells that depend on previous sections.
    Provides clear error messages for out-of-order execution.
    
    Parameters:
    -----------
    required_vars : dict mapping variable name -> section where it's created
        Example: {"df_enr": "Section 1.2", "df_abt": "Section 1.1"}
    required_cols : dict mapping DataFrame name -> set of required columns
        Example: {"df_cond": {"condition_name", "trial_count"}}
    caller_globals : globals() from the calling cell (required)
    
    Raises:
    -------
    ValueError if caller_globals is not provided
    RuntimeError with clear message about what's missing
    
    Example:
    --------
    >>> # At the start of Section 4.4
    >>> check_dependencies(
    ...     required_vars={"df_cond": "Section 4.1", "df_enr": "Section 1.2"},
    ...     required_cols={"df_cond": {"condition_name", "trial_count"}},
    ...     caller_globals=globals(),
    ... )
    """
    if caller_globals is None:
        raise ValueError(
            "Must pass globals() as caller_globals argument: "
            "check_dependencies(..., caller_globals=globals())"
        )
    
    # Check variables exist
    missing = [
        f"`{var}` ({section})"
        for var, section in required_vars.items()
        if var not in caller_globals
    ]
    if missing:
        raise RuntimeError(
            f"Missing variables: {', '.join(missing)}. "
            "Run prerequisite sections first."
        )
    
    # Check DataFrame columns
    if required_cols:
        for df_name, cols in required_cols.items():
            df = caller_globals.get(df_name)
            if df is not None and hasattr(df, "columns"):
                missing_cols = cols - set(df.columns)
                if missing_cols:
                    raise RuntimeError(
                        f"`{df_name}` missing columns: {sorted(missing_cols)}. "
                        f"Re-run {required_vars.get(df_name, 'prerequisite section')}."
                    )


def register_shared_vars(**kwargs) -> dict:
    """
    Create a dictionary of shared variables with None defaults.
    
    Use to document cross-section dependencies at notebook start.
    Variables initialized as None will fail fast if used before assignment.
    
    Parameters:
    -----------
    **kwargs : variable_name=description pairs
    
    Returns:
    --------
    dict with all keys set to None (ready for unpacking)
    
    Example:
    --------
    >>> # At notebook start
    >>> shared = register_shared_vars(
    ...     epsilon_sq_phase="Effect size from Section 2.1",
    ...     rho="Spearman correlation from Section 3.3",
    ... )
    >>> epsilon_sq_phase = shared['epsilon_sq_phase']  # None initially
    """
    return {name: None for name in kwargs}
