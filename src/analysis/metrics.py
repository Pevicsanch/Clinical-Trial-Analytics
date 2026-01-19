"""
Analytical metrics for clinical trial analysis.

This module provides reusable functions for calculating rates and metrics
that can be used across multiple notebooks (Q2, Q3, Q4).
"""

import pandas as pd


def calc_completion_rate(
    df: pd.DataFrame,
    group_col: str,
    min_n: int = 20,
) -> pd.DataFrame:
    """
    Calculate resolved completion rate, grouped by a factor.
    
    Uses only resolved trials (Completed + Stopped) to avoid censoring bias.
    Active trials are excluded because their final outcome is not yet observed.
    
    Parameters:
    -----------
    df : ABT dataframe (full, will be filtered to resolved)
    group_col : Column to group by
    min_n : Minimum sample size to include group (default: 20)
    
    Returns:
    --------
    DataFrame with columns: [group_col, n_resolved, n_completed, completion_rate]
    Sorted by n_resolved descending (caller can re-sort as needed).
    
    Example:
    --------
    >>> phase_rates = calc_completion_rate(df_abt, 'phase_group')
    >>> phase_rates.sort_values('completion_rate', ascending=False)
    """
    # Filter to resolved trials only (exclude Active)
    resolved = df[df['is_resolved'] == 1].copy()
    
    # Use nunique for study_id to guard against accidental duplicates
    stats = (
        resolved
        .groupby(group_col, dropna=False)
        .agg(
            n_resolved=('study_id', 'nunique'),
            n_completed=('is_completed', 'sum')
        )
        .reset_index()
    )
    
    # Calculate rate (0-100 scale)
    stats['completion_rate'] = stats['n_completed'] / stats['n_resolved'] * 100
    
    # Filter small groups (statistical reliability)
    stats = stats[stats['n_resolved'] >= min_n].copy()
    
    # Default sort by sample size; caller can re-sort by rate if needed
    return stats.sort_values('n_resolved', ascending=False)
