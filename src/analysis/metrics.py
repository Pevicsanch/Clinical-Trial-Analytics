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
        .groupby(group_col, dropna=False, observed=False)
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
    stats = df.groupby(group_col, observed=False).agg(
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


def create_sponsor_category(lead_agency_class: pd.Series) -> pd.Series:
    """
    Create binary sponsor category from lead_agency_class.
    
    Parameters:
    -----------
    lead_agency_class : Series with sponsor class values
    
    Returns:
    --------
    Series with 'Industry' or 'Other'
    
    Note: 'Other' includes academic, government, non-profit, and missing.
    """
    return lead_agency_class.apply(
        lambda x: 'Industry' if x == 'INDUSTRY' else 'Other'
    )


def create_start_cohorts(
    start_year: pd.Series,
    bins: list = None,
    labels: list = None,
) -> pd.Series:
    """
    Create start-year cohorts for temporal analysis.
    
    Parameters:
    -----------
    start_year : Series with start years
    bins : List of bin edges (default: [1989, 1999, 2009, 2019, 2026])
    labels : List of labels (default: ['1990-1999', '2000-2009', ...])
    
    Returns:
    --------
    Categorical Series with cohort labels
    """
    from src.analysis.constants import COHORT_BINS, COHORT_LABELS
    
    bins = bins or COHORT_BINS
    labels = labels or COHORT_LABELS
    
    return pd.cut(start_year, bins=bins, labels=labels)


def calc_missingness_by_dimension(
    df: pd.DataFrame,
    dim: str,
    flag_col: str = "has_enrollment",
    label_map: dict | None = None,
    min_n: int = 50,
) -> pd.DataFrame:
    """
    Calculate % missing (flag=0) by a categorical dimension.
    
    Used for selection bias assessment before conditioning on data availability.
    
    Parameters:
    -----------
    df : DataFrame with the dimension and flag columns
    dim : Column name to group by (e.g., 'phase_group', 'is_industry_sponsor')
    flag_col : Binary column where 1=present, 0=missing (default: 'has_enrollment')
    label_map : Optional dict to map raw values to readable labels
    min_n : Minimum group size to include (filters noisy small groups)
    
    Returns:
    --------
    DataFrame with columns: [dim, n, pct_missing]
    Sorted by pct_missing descending.
    
    Example:
    --------
    >>> phase_miss = calc_missingness_by_dimension(df_abt, 'phase_group')
    >>> sponsor_miss = calc_missingness_by_dimension(
    ...     df_abt, 'is_industry_sponsor', 
    ...     label_map={1: 'Industry', 0: 'Non-industry'}
    ... )
    """
    if dim not in df.columns:
        raise KeyError(f"Column not found: {dim}")
    
    out = (
        df.groupby(dim, dropna=False)
        .agg(
            n=("study_id", "count"),
            pct_missing=(flag_col, lambda s: (1 - s.mean()) * 100),
        )
        .reset_index()
    )
    
    if label_map is not None:
        out[dim] = out[dim].map(label_map).fillna(out[dim])
    
    out = out[out["n"] >= min_n].copy()
    out = out.sort_values("pct_missing", ascending=False)
    
    return out


# ============================================================
# Effect Size Calculations
# ============================================================

def calc_cramers_v(chi2: float, n: int, min_dim: int) -> float:
    """
    Calculate Cramér's V effect size for chi-squared test.
    
    Parameters:
    -----------
    chi2 : Chi-square statistic
    n : Total sample size
    min_dim : min(rows - 1, cols - 1) from contingency table
    
    Returns:
    --------
    Cramér's V (0-1 scale)
    
    Interpretation (Cohen, 1988):
    - V < 0.1 : negligible
    - V < 0.3 : small
    - V < 0.5 : medium
    - V >= 0.5 : large
    
    Example:
    --------
    >>> ct = pd.crosstab(df['group'], df['outcome'])
    >>> chi2, p, dof, _ = chi2_contingency(ct)
    >>> v = calc_cramers_v(chi2, ct.sum().sum(), min(ct.shape) - 1)
    """
    if min_dim <= 0 or n <= 0:
        return 0.0
    return float(np.sqrt(chi2 / (n * min_dim)))


def interpret_effect_size(value: float, metric: str = "r") -> str:
    """
    Interpret effect size magnitude using standard thresholds.
    
    Parameters:
    -----------
    value : Effect size value (absolute value used)
    metric : Type of effect size:
        - "r" : correlation / rank-biserial (Cohen thresholds)
        - "v" : Cramér's V (same as r)
        - "d" : Cohen's d
        - "eta2" / "epsilon2" : variance explained
    
    Returns:
    --------
    String: 'negligible', 'small', 'medium', or 'large'
    """
    v = abs(value)
    
    if metric in ("r", "v", "cramers_v", "rank_biserial"):
        # Cohen (1988) for correlation-type
        if v < 0.1:
            return "negligible"
        elif v < 0.3:
            return "small"
        elif v < 0.5:
            return "medium"
        else:
            return "large"
    elif metric == "d":
        # Cohen's d
        if v < 0.2:
            return "negligible"
        elif v < 0.5:
            return "small"
        elif v < 0.8:
            return "medium"
        else:
            return "large"
    elif metric in ("eta2", "epsilon2", "eta_squared", "epsilon_squared"):
        # Variance explained (approximate thresholds)
        if v < 0.01:
            return "negligible"
        elif v < 0.06:
            return "small"
        elif v < 0.14:
            return "medium"
        else:
            return "large"
    else:
        # Default to r-type thresholds
        if v < 0.1:
            return "negligible"
        elif v < 0.3:
            return "small"
        elif v < 0.5:
            return "medium"
        else:
            return "large"


# ============================================================
# ABT Validation
# ============================================================

def validate_abt(
    df: pd.DataFrame,
    required_cols: list[str] | None = None,
    id_col: str = "study_id",
    year_col: str = "start_year",
    year_range: tuple[int, int] = (1990, 2026),
    raise_on_error: bool = True,
) -> dict:
    """
    Validate analytical base table for clinical trial analysis.
    
    Checks:
    - ID uniqueness
    - Required columns exist
    - Year column has no nulls and is in expected range
    
    Parameters:
    -----------
    df : DataFrame to validate
    required_cols : List of required column names (default: None)
    id_col : Column to check for uniqueness (default: 'study_id')
    year_col : Column to check for year range (default: 'start_year')
    year_range : Tuple of (min_year, max_year) (default: (1990, 2026))
    raise_on_error : If True, raise AssertionError on failure (default: True)
    
    Returns:
    --------
    dict with:
        - n_rows : Number of rows
        - n_unique_ids : Number of unique IDs
        - year_min : Minimum year value
        - year_max : Maximum year value
        - valid : Boolean indicating all checks passed
        - errors : List of error messages (empty if valid)
    
    Example:
    --------
    >>> result = validate_abt(df_abt, required_cols=['enrollment_type'])
    >>> if not result['valid']:
    ...     print(result['errors'])
    """
    errors = []
    n_rows = len(df)
    n_unique_ids = df[id_col].nunique() if id_col in df.columns else 0
    
    # Check ID column exists and is unique
    if id_col not in df.columns:
        errors.append(f"ID column '{id_col}' not found")
    elif n_unique_ids != n_rows:
        errors.append(f"ID column '{id_col}' is not unique: {n_unique_ids} unique vs {n_rows} rows")
    
    # Check required columns
    if required_cols:
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
    
    # Check year column
    year_min, year_max = None, None
    if year_col in df.columns:
        if df[year_col].isna().any():
            errors.append(f"Year column '{year_col}' has {df[year_col].isna().sum()} null values")
        else:
            year_min = int(df[year_col].min())
            year_max = int(df[year_col].max())
            if year_min < year_range[0]:
                errors.append(f"Year min ({year_min}) below expected range ({year_range[0]})")
            if year_max > year_range[1]:
                errors.append(f"Year max ({year_max}) above expected range ({year_range[1]})")
    
    result = {
        'n_rows': n_rows,
        'n_unique_ids': n_unique_ids,
        'year_min': year_min,
        'year_max': year_max,
        'valid': len(errors) == 0,
        'errors': errors,
    }
    
    if raise_on_error and errors:
        raise AssertionError(f"ABT validation failed: {'; '.join(errors)}")
    
    return result


# ============================================================
# Enrollment Coverage and Type Breakdown
# ============================================================

def calc_enrollment_coverage(
    df: pd.DataFrame,
    enrollment_col: str = "enrollment",
) -> tuple[pd.DataFrame, dict]:
    """
    Calculate enrollment coverage: positive, zero, missing.
    
    Parameters:
    -----------
    df : DataFrame with enrollment data
    enrollment_col : Column with enrollment counts (default: 'enrollment')
    
    Returns:
    --------
    Tuple of:
        - DataFrame with columns: Category, Count, Share
        - dict with n_positive, n_zero, n_missing, pct_positive
    
    Example:
    --------
    >>> coverage_df, coverage_stats = calc_enrollment_coverage(df_abt)
    >>> display(coverage_df.style.format({'Count': '{:,}', 'Share': '{:.1%}'}))
    """
    n_total = len(df)
    
    is_missing = df[enrollment_col].isna()
    is_zero = df[enrollment_col].fillna(-1) == 0
    is_positive = df[enrollment_col].fillna(0) > 0
    
    n_positive = is_positive.sum()
    n_zero = is_zero.sum()
    n_missing = is_missing.sum()
    
    # Build coverage table (only include zero row if > 0)
    rows = [
        {'Category': 'Enrollment > 0', 'Count': n_positive, 'Share': n_positive / n_total},
        {'Category': 'Enrollment missing (NULL)', 'Count': n_missing, 'Share': n_missing / n_total},
    ]
    if n_zero > 0:
        rows.insert(1, {'Category': 'Enrollment = 0 (placeholder)', 'Count': n_zero, 'Share': n_zero / n_total})
    
    coverage_df = pd.DataFrame(rows)
    
    stats = {
        'n_positive': n_positive,
        'n_zero': n_zero,
        'n_missing': n_missing,
        'n_total': n_total,
        'pct_positive': n_positive / n_total * 100,
    }
    
    return coverage_df, stats


def calc_enrollment_type_breakdown(
    df: pd.DataFrame,
    type_col: str = "enrollment_type",
    filter_positive: bool = True,
    enrollment_col: str = "enrollment",
) -> tuple[pd.DataFrame, dict]:
    """
    Bucket enrollment_type into ACTUAL, ANTICIPATED, OTHER/UNKNOWN.
    
    Parameters:
    -----------
    df : DataFrame with enrollment type data
    type_col : Column with enrollment type (default: 'enrollment_type')
    filter_positive : If True, only include rows with enrollment > 0 (default: True)
    enrollment_col : Column to filter on (default: 'enrollment')
    
    Returns:
    --------
    Tuple of:
        - DataFrame with columns: Enrollment Type, Count, Share
        - dict with pct_actual, pct_anticipated, pct_other
    
    Example:
    --------
    >>> type_df, type_pcts = calc_enrollment_type_breakdown(df_abt)
    >>> display(type_df)
    """
    from src.analysis.constants import ENROLLMENT_TYPE_BUCKETS
    
    # Filter to positive enrollment if requested
    if filter_positive:
        df_subset = df[df[enrollment_col].fillna(0) > 0].copy()
    else:
        df_subset = df.copy()
    
    n_total = len(df_subset)
    if n_total == 0:
        empty_df = pd.DataFrame({'Enrollment Type': ENROLLMENT_TYPE_BUCKETS, 'Count': 0, 'Share': 0.0})
        return empty_df, {'pct_actual': 0.0, 'pct_anticipated': 0.0, 'pct_other': 0.0}
    
    # Standardize and bucket
    type_clean = df_subset[type_col].fillna('').str.upper().str.strip()
    
    buckets = pd.Series('OTHER/UNKNOWN', index=df_subset.index)
    buckets[type_clean == 'ACTUAL'] = 'ACTUAL'
    buckets[type_clean == 'ANTICIPATED'] = 'ANTICIPATED'
    
    # Count
    counts = buckets.value_counts()
    
    type_df = pd.DataFrame({
        'Enrollment Type': counts.index,
        'Count': counts.values,
        'Share': counts.values / n_total
    }).reset_index(drop=True)
    
    # Percentages
    pcts = {
        'pct_actual': counts.get('ACTUAL', 0) / n_total * 100,
        'pct_anticipated': counts.get('ANTICIPATED', 0) / n_total * 100,
        'pct_other': counts.get('OTHER/UNKNOWN', 0) / n_total * 100,
        'n_total': n_total,
    }
    
    return type_df, pcts


# ============================================================
# Temporal Missingness Assessment
# ============================================================

def assess_temporal_missingness(
    df: pd.DataFrame,
    cohort_col: str = "start_cohort",
    year_col: str = "start_year",
    flag_col: str = "has_enrollment",
    cohort_order: list[str] | None = None,
    thresholds: tuple[float, float] = (5.0, 10.0),
) -> dict:
    """
    Assess temporal variation in missingness for selection bias check.
    
    Parameters:
    -----------
    df : DataFrame with cohort and flag columns
    cohort_col : Column with temporal cohorts (default: 'start_cohort')
    year_col : Column with year for Spearman correlation (default: 'start_year')
    flag_col : Binary column where 1=present, 0=missing (default: 'has_enrollment')
    cohort_order : List to order cohorts (default: uses COHORT_LABELS from constants)
    thresholds : Tuple of (moderate_threshold, substantial_threshold) in pp
    
    Returns:
    --------
    dict with:
        - cohort_stats : DataFrame by cohort (n, pct_missing)
        - rho : Spearman correlation coefficient
        - p_value : p-value for Spearman test
        - miss_min : Minimum missingness rate
        - miss_max : Maximum missingness rate
        - range_pp : Range in percentage points
        - severity : 'modest' | 'moderate' | 'substantial'
        - warning : Interpretation string for display
    
    Example:
    --------
    >>> result = assess_temporal_missingness(df_abt)
    >>> display(result['cohort_stats'])
    >>> print(result['warning'])
    """
    from scipy.stats import spearmanr
    from src.analysis.constants import COHORT_LABELS
    
    cohort_order = cohort_order or COHORT_LABELS
    moderate_thresh, substantial_thresh = thresholds
    
    # Calculate missingness by cohort
    cohort_stats = (
        df
        .groupby(cohort_col)
        .agg(
            n=("study_id", "count"),
            pct_missing=(flag_col, lambda x: (1 - x.mean()) * 100)
        )
        .reset_index()
    )
    
    # Reorder cohorts
    cohort_stats = cohort_stats.set_index(cohort_col).reindex(cohort_order).reset_index()
    
    # Spearman correlation with year
    rho, p_value = spearmanr(df[year_col], df[flag_col])
    
    # Calculate range
    miss_min = cohort_stats["pct_missing"].min()
    miss_max = cohort_stats["pct_missing"].max()
    range_pp = miss_max - miss_min
    
    # Assess severity
    if range_pp > substantial_thresh:
        severity = "substantial"
        warning = "**Warning:** Temporal analyses may be biased by time-varying selection."
    elif range_pp > moderate_thresh:
        severity = "moderate"
        warning = "Temporal analyses should be interpreted with caution due to time-varying missingness."
    else:
        severity = "modest"
        warning = "Missingness is relatively stable over time."
    
    return {
        'cohort_stats': cohort_stats,
        'rho': rho,
        'p_value': p_value,
        'miss_min': miss_min,
        'miss_max': miss_max,
        'range_pp': range_pp,
        'severity': severity,
        'warning': warning,
    }


# ============================================================
# Group Comparison Analysis
# ============================================================

def summarize_by_group(
    df: pd.DataFrame,
    group_col: str,
    value_col: str = "enrollment",
    order: list[str] | None = None,
) -> pd.DataFrame:
    """
    Create descriptive summary table by group.
    
    Parameters:
    -----------
    df : DataFrame with group and value columns
    group_col : Column to group by
    value_col : Numeric column to summarize (default: 'enrollment')
    order : Optional list to order groups
    
    Returns:
    --------
    DataFrame with columns: N, Median, Mean, Q1, Q3
    Index is the group column.
    
    Example:
    --------
    >>> summary = summarize_by_group(df_enr, "phase_group", order=PHASE_ORDER_CLINICAL)
    """
    summary = (
        df
        .groupby(group_col)[value_col]
        .agg(
            N="count",
            Median="median",
            Mean="mean",
            Q1=lambda x: x.quantile(0.25),
            Q3=lambda x: x.quantile(0.75),
        )
        .round(1)
    )
    
    if order is not None:
        # Reindex with order, keeping only groups that exist
        valid_order = [g for g in order if g in summary.index]
        extra = [g for g in summary.index if g not in order]
        summary = summary.reindex(valid_order + extra)
    
    return summary.dropna(subset=["N"])


def kruskal_with_epsilon(
    df: pd.DataFrame,
    group_col: str,
    value_col: str = "enrollment",
) -> dict:
    """
    Run Kruskal-Wallis H-test and compute epsilon-squared effect size.
    
    Parameters:
    -----------
    df : DataFrame with group and value columns
    group_col : Column defining groups
    value_col : Numeric column to compare (default: 'enrollment')
    
    Returns:
    --------
    dict with:
        - h_stat : Kruskal-Wallis H statistic
        - p_value : p-value
        - k : number of groups
        - n : total sample size
        - epsilon_sq : epsilon-squared effect size
        - effect_label : 'negligible', 'small', 'medium', or 'large'
    
    Notes:
    ------
    Epsilon-squared (ε²) is recommended for Kruskal-Wallis (Tomczak & Tomczak, 2014).
    Interpretation thresholds (approximate, from Cohen 1988 adapted):
        - ε² < 0.01 : negligible
        - ε² < 0.06 : small
        - ε² < 0.14 : medium
        - ε² >= 0.14 : large
    
    Example:
    --------
    >>> result = kruskal_with_epsilon(df_enr, "phase_group")
    >>> print(f"ε² = {result['epsilon_sq']:.4f} ({result['effect_label']})")
    """
    from scipy.stats import kruskal
    
    groups = [g[value_col].values for _, g in df.groupby(group_col)]
    h_stat, p_value = kruskal(*groups)
    
    n = len(df)
    k = len(groups)
    # Floor at 0: for k=2 and small H, formula can yield negative values
    epsilon_sq = max(0.0, (h_stat - k + 1) / (n - k))

    # Interpret effect size
    effect_label = interpret_effect_size(epsilon_sq, metric="epsilon2")
    
    return {
        'h_stat': h_stat,
        'p_value': p_value,
        'k': k,
        'n': n,
        'epsilon_sq': epsilon_sq,
        'effect_label': effect_label,
    }


def pairwise_mannwhitney(
    df: pd.DataFrame,
    group_col: str,
    value_col: str = "enrollment",
    pairs: list[tuple[str, str]] | None = None,
    correction: str = "bonferroni",
) -> pd.DataFrame:
    """
    Run pairwise Mann-Whitney U tests with multiple comparison correction.
    
    Parameters:
    -----------
    df : DataFrame with group and value columns
    group_col : Column defining groups
    value_col : Numeric column to compare (default: 'enrollment')
    pairs : List of (group1, group2) tuples to compare.
            If None, compares all pairs.
    correction : Multiple comparison method ('bonferroni' or 'none')
    
    Returns:
    --------
    DataFrame with columns:
        - Comparison : "Group1 vs Group2"
        - U : Mann-Whitney U statistic
        - p_value : raw p-value
        - p_adj : adjusted p-value (if correction applied)
        - r : rank-biserial correlation (effect size)
        - effect_label : interpretation of |r|
        - sig : significance stars (*** < 0.001, ** < 0.01, * < 0.05)
    
    Example:
    --------
    >>> posthoc = pairwise_mannwhitney(
    ...     df_phase, "phase_group",
    ...     pairs=[("Phase 1", "Phase 3"), ("Phase 2", "Phase 3")],
    ... )
    """
    from scipy.stats import mannwhitneyu
    from itertools import combinations
    
    # Get unique groups
    groups = df[group_col].unique()
    group_data = {g: df.loc[df[group_col] == g, value_col].values for g in groups}
    
    # Determine pairs to test
    if pairs is None:
        pairs = list(combinations(groups, 2))
    else:
        # Filter to valid pairs
        pairs = [(p1, p2) for p1, p2 in pairs if p1 in group_data and p2 in group_data]
    
    if not pairs:
        return pd.DataFrame()
    
    results = []
    for g1, g2 in pairs:
        d1, d2 = group_data[g1], group_data[g2]
        u, p = mannwhitneyu(d1, d2, alternative="two-sided")
        n1, n2 = len(d1), len(d2)
        
        # Rank-biserial correlation as effect size
        r = 1 - (2 * u) / (n1 * n2)
        
        results.append({
            'Comparison': f"{g1} vs {g2}",
            'n1': n1,
            'n2': n2,
            'U': u,
            'p_value': p,
            'r': r,
        })
    
    df_results = pd.DataFrame(results)
    
    # Apply correction
    n_tests = len(df_results)
    if correction == "bonferroni" and n_tests > 1:
        df_results['p_adj'] = (df_results['p_value'] * n_tests).clip(upper=1.0)
        p_col = 'p_adj'
    else:
        df_results['p_adj'] = df_results['p_value']
        p_col = 'p_value'
    
    # Effect size interpretation
    df_results['effect_label'] = df_results['r'].abs().apply(
        lambda x: interpret_effect_size(x, metric="r")
    )
    
    # Significance stars
    df_results['sig'] = df_results[p_col].apply(
        lambda p: "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    )
    
    return df_results


def analyze_enrollment_by_factor(
    df: pd.DataFrame,
    group_col: str,
    value_col: str = "enrollment",
    order: list[str] | None = None,
    posthoc_pairs: list[tuple[str, str]] | None = None,
) -> dict:
    """
    Complete enrollment analysis by a categorical factor.
    
    Combines descriptive summary, Kruskal-Wallis test, and optional post-hoc comparisons.
    
    Parameters:
    -----------
    df : DataFrame with group and value columns (should be pre-filtered)
    group_col : Column defining groups
    value_col : Numeric column to analyze (default: 'enrollment')
    order : Optional list to order groups in summary
    posthoc_pairs : Optional list of (group1, group2) pairs for post-hoc tests
    
    Returns:
    --------
    dict with:
        - summary : DataFrame with descriptive statistics
        - test : dict with Kruskal-Wallis results and epsilon_sq
        - posthoc : DataFrame with pairwise comparisons (if posthoc_pairs provided)
        - n_total : total sample size
        - n_groups : number of groups
    
    Example:
    --------
    >>> result = analyze_enrollment_by_factor(
    ...     df_phase, "phase_group",
    ...     order=PHASE_ORDER_CLINICAL,
    ...     posthoc_pairs=[("Phase 1", "Phase 3")],
    ... )
    >>> epsilon_sq_phase = result['test']['epsilon_sq']
    """
    # Filter to non-null group values
    df_clean = df[df[group_col].notna()].copy()
    
    # Descriptive summary
    summary = summarize_by_group(df_clean, group_col, value_col, order=order)
    
    # Kruskal-Wallis test
    test = kruskal_with_epsilon(df_clean, group_col, value_col)
    
    # Optional post-hoc
    posthoc = None
    if posthoc_pairs:
        posthoc = pairwise_mannwhitney(df_clean, group_col, value_col, pairs=posthoc_pairs)
    
    return {
        'summary': summary,
        'test': test,
        'posthoc': posthoc,
        'n_total': len(df_clean),
        'n_groups': test['k'],
        'n_excluded': len(df) - len(df_clean),
    }
