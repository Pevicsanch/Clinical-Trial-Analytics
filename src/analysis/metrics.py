"""
Analytical metrics for clinical trial analysis.

This module provides reusable functions for calculating rates and metrics
that can be used across multiple notebooks (Q2, Q3, Q4).
"""

import numpy as np
import pandas as pd


def wilson_ci(
    successes: int,
    n: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a binomial proportion.
    
    Wilson interval is preferred over normal approximation because it:
    - Has better coverage for small samples
    - Never produces intervals outside [0, 1]
    - Performs well for proportions near 0 or 1
    
    Parameters:
    -----------
    successes : Number of successes (e.g., completed trials)
    n : Total number of trials
    confidence : Confidence level (default: 0.95 for 95% CI)
    
    Returns:
    --------
    Tuple of (lower_bound, upper_bound) as proportions (0-1 scale)
    
    Example:
    --------
    >>> wilson_ci(85, 100)  # 85% success rate
    (0.766, 0.908)
    """
    if n == 0:
        return (0.0, 0.0)
    
    # Z-score for confidence level
    from scipy import stats
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    p = successes / n
    
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    
    return (max(0, center - margin), min(1, center + margin))


def calc_completion_rate(
    df: pd.DataFrame,
    group_col: str,
    min_n: int = 20,
    include_ci: bool = True,
    confidence: float = 0.95,
) -> pd.DataFrame:
    """
    Calculate resolved completion rate with confidence intervals, grouped by a factor.
    
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
    include_ci : Whether to include Wilson confidence intervals (default: True)
    confidence : Confidence level for CI (default: 0.95)
    
    Returns:
    --------
    DataFrame with columns:
        - {group_col} : grouping variable (NA preserved, caller can rename)
        - n_resolved : count of resolved trials in group
        - n_completed : count of completed trials in group
        - completion_rate_pct : percentage (0–100 scale)
        - ci_lower_pct : lower bound of CI (0-100 scale) [if include_ci=True]
        - ci_upper_pct : upper bound of CI (0-100 scale) [if include_ci=True]
    
    Sorted by n_resolved descending (neutral; caller can re-sort by rate).
    
    Example:
    --------
    >>> phase_rates = calc_completion_rate(df_abt, 'phase_group')
    >>> # Display with CIs: "85.6% [84.7-86.4%]"
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
    
    # Add Wilson confidence intervals
    if include_ci:
        ci_bounds = stats.apply(
            lambda row: wilson_ci(
                int(row['n_completed']),
                int(row['n_resolved']),
                confidence
            ),
            axis=1
        )
        stats['ci_lower_pct'] = ci_bounds.apply(lambda x: x[0] * 100)
        stats['ci_upper_pct'] = ci_bounds.apply(lambda x: x[1] * 100)
    
    # Filter small groups (statistical reliability)
    stats = stats[stats['n_resolved'] >= min_n].copy()
    
    # Default sort by sample size; caller can re-sort by rate if needed
    return stats.sort_values('n_resolved', ascending=False)


def test_rate_difference(
    df: pd.DataFrame,
    group_col: str,
    outcome_col: str = 'is_completed',
) -> dict:
    """
    Chi-square test for independence between group and outcome.
    
    Tests whether completion rates differ significantly across groups.
    
    Parameters:
    -----------
    df : DataFrame (should be pre-filtered to resolved trials)
    group_col : Column defining groups to compare
    outcome_col : Binary outcome column (default: 'is_completed')
    
    Returns:
    --------
    Dict with:
        - chi2 : Chi-square statistic
        - p_value : P-value (two-sided)
        - dof : Degrees of freedom
        - significant : Boolean (p < 0.05)
        - interpretation : Human-readable result
    
    Example:
    --------
    >>> result = test_rate_difference(df_resolved, 'sponsor_category')
    >>> print(result['interpretation'])
    "Significant difference (χ²=45.2, p<0.001)"
    """
    from scipy.stats import chi2_contingency
    
    # Create contingency table
    contingency = pd.crosstab(df[group_col], df[outcome_col])
    
    # Chi-square test
    chi2, p_value, dof, expected = chi2_contingency(contingency)
    
    # Format interpretation
    if p_value < 0.001:
        p_str = "p<0.001"
    elif p_value < 0.01:
        p_str = f"p={p_value:.3f}"
    else:
        p_str = f"p={p_value:.2f}"
    
    significant = p_value < 0.05
    interpretation = (
        f"{'Significant' if significant else 'No significant'} difference "
        f"(χ²={chi2:.1f}, {p_str})"
    )
    
    return {
        'chi2': chi2,
        'p_value': p_value,
        'dof': dof,
        'significant': significant,
        'interpretation': interpretation,
    }


def calc_enrollment_presence(
    df: pd.DataFrame,
    group_col: str,
    enrollment_col: str = 'enrollment',
) -> pd.DataFrame:
    """
    Analyze enrollment data presence by group.
    
    Distinguishes between trials that have enrollment data (enrolled patients)
    and those that don't (missing/zero = "failure to launch").
    
    Parameters:
    -----------
    df : DataFrame with enrollment data
    group_col : Column to group by (e.g., 'failure_type')
    enrollment_col : Column with enrollment counts (default: 'enrollment')
    
    Returns:
    --------
    DataFrame with columns:
        - {group_col} : grouping variable
        - n_total : total trials in group
        - n_with_enrollment : trials with enrollment > 0
        - n_missing_or_zero : trials with enrollment == 0 or NaN
        - pct_with_enrollment : percentage with enrollment data
        - median_nonzero : median enrollment (among those with data)
    
    Example:
    --------
    >>> presence = calc_enrollment_presence(df_stopped, 'failure_type')
    >>> # Shows Withdrawn has ~99% missing enrollment (failure to launch)
    """
    stats = df.groupby(group_col).agg(
        n_total=('study_id', 'count'),
        n_with_enrollment=(
            enrollment_col, lambda x: (x > 0).sum()
        ),
        n_missing_or_zero=(
            enrollment_col, lambda x: ((x == 0) | x.isna()).sum()
        ),
        pct_with_enrollment=(
            enrollment_col, lambda x: (x > 0).mean() * 100
        ),
        median_nonzero=(
            enrollment_col,
            lambda x: x[x > 0].median() if (x > 0).any() else np.nan
        )
    ).round(1)
    
    return stats.reset_index()


def calc_crosstab_analysis(
    df: pd.DataFrame,
    row_col: str,
    col_col: str,
    row_order: list = None,
    col_order: list = None,
    include_test: bool = True,
) -> dict:
    """
    Create crosstab with counts, percentages, and chi-square test.
    
    Parameters:
    -----------
    df : DataFrame with categorical columns
    row_col : Column for rows (e.g., 'phase_group')
    col_col : Column for columns (e.g., 'failure_type')
    row_order : Optional list to order rows
    col_order : Optional list to order columns
    include_test : Whether to run chi-square test (default: True)
    
    Returns:
    --------
    Dict with:
        - counts : DataFrame of counts
        - pct_row : DataFrame of row percentages (sum to 100% per row)
        - pct_col : DataFrame of column percentages (sum to 100% per col)
        - test : Chi-square test result dict (if include_test=True)
    
    Example:
    --------
    >>> result = calc_crosstab_analysis(df_stopped, 'phase_group', 'failure_type')
    >>> display(result['pct_row'])  # Row percentages
    >>> print(result['test']['interpretation'])
    """
    # Counts
    counts = pd.crosstab(df[row_col], df[col_col], margins=True)
    
    # Row percentages (how each row distributes across columns)
    pct_row = pd.crosstab(df[row_col], df[col_col], normalize='index') * 100
    
    # Column percentages (how each column distributes across rows)
    pct_col = pd.crosstab(df[row_col], df[col_col], normalize='columns') * 100
    
    # Reorder if specified
    if row_order:
        available_rows = [r for r in row_order if r in counts.index]
        counts = counts.loc[available_rows + ['All']] if 'All' in counts.index else counts.loc[available_rows]
        pct_row = pct_row.loc[[r for r in row_order if r in pct_row.index]]
        pct_col = pct_col.loc[[r for r in row_order if r in pct_col.index]]
    
    if col_order:
        available_cols = [c for c in col_order if c in counts.columns]
        counts = counts[available_cols + ['All']] if 'All' in counts.columns else counts[available_cols]
        pct_row = pct_row[[c for c in col_order if c in pct_row.columns]]
        pct_col = pct_col[[c for c in col_order if c in pct_col.columns]]
    
    result = {
        'counts': counts,
        'pct_row': pct_row.round(1),
        'pct_col': pct_col.round(1),
    }
    
    if include_test:
        result['test'] = test_rate_difference(df, row_col, col_col)
    
    return result
