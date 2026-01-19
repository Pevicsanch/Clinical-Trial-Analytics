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
    df : DataFrame with required columns:
        - study_id : unique trial identifier
        - is_resolved : 1 if Completed or Stopped, 0 if Active
        - is_completed : 1 if Completed, 0 otherwise
    group_col : Column to group by (NA values kept as separate group)
    min_n : Minimum sample size to include group (default: 20)
    
    Returns:
    --------
    DataFrame with columns:
        - {group_col} : grouping variable (NA preserved, caller can rename)
        - n_resolved : count of resolved trials in group
        - n_completed : count of completed trials in group
        - completion_rate_pct : percentage (0–100 scale)
    
    Sorted by n_resolved descending (neutral; caller can re-sort by rate).
    
    Example:
    --------
    >>> phase_rates = calc_completion_rate(df_abt, 'phase_group')
    >>> phase_rates.sort_values('completion_rate_pct', ascending=False)
    """
    # Filter to resolved trials only (exclude Active)
    resolved = df[df['is_resolved'] == 1].copy()
    
    # Use nunique for study_id to guard against accidental duplicates
    # dropna=False keeps NA as a separate group (caller decides how to label)
    stats = (
        resolved
        .groupby(group_col, dropna=False)
        .agg(
            n_resolved=('study_id', 'nunique'),
            n_completed=('is_completed', 'sum')
        )
        .reset_index()
    )
    
    # Calculate rate as percentage (0-100 scale, stakeholder friendly)
    stats['completion_rate_pct'] = stats['n_completed'] / stats['n_resolved'] * 100
    
    # Filter small groups (statistical reliability)
    stats = stats[stats['n_resolved'] >= min_n].copy()
    
    # Default sort by sample size; caller can re-sort by rate if needed
    return stats.sort_values('n_resolved', ascending=False)
