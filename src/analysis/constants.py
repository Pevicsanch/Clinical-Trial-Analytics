"""
Analysis constants for clinical trial data.

This module contains business-logic mappings for aggregating clinical trial
phases and statuses into meaningful groups for reporting and visualization.

These are analytical decisions, not visualization settings.
"""

# ============================================================
# Phase Order (Individual Phases)
# ============================================================
# Clinical development order for individual phase display

PHASE_ORDER = [
    'Early Phase 1',
    'Phase 1',
    'Phase 1/2',
    'Phase 2',
    'Phase 2/3',
    'Phase 3',
    'Phase 4',
    'Not Applicable',
    'Other',
]

# For charts that exclude non-phase-designated studies
PHASE_ORDER_CLINICAL = [
    'Early Phase 1',
    'Phase 1',
    'Phase 1/2',
    'Phase 2',
    'Phase 2/3',
    'Phase 3',
    'Phase 4',
]

# Enrollment size buckets (ascending order)
ENROLLMENT_ORDER = [
    'Unknown',
    '<50',
    '50-99',
    '100-499',
    '500-999',
    '1000+',
]


# ============================================================
# Phase Aggregation
# ============================================================
# Maps 9 registry phases → 3 pipeline stages (+ Not Applicable/Other)
# Used for temporal trend analysis where granular phases are too noisy.

PHASE_AGG_MAP = {
    'Early Phase 1': 'Early (Early Phase 1 + Phase 1)',
    'Phase 1': 'Early (Early Phase 1 + Phase 1)',
    'Phase 1/2': 'Mid (Phase 1/2 + Phase 2 + Phase 2/3)',
    'Phase 2': 'Mid (Phase 1/2 + Phase 2 + Phase 2/3)',
    'Phase 2/3': 'Mid (Phase 1/2 + Phase 2 + Phase 2/3)',
    'Phase 3': 'Late (Phase 3 + Phase 4)',
    'Phase 4': 'Late (Phase 3 + Phase 4)',
    'Not Applicable': 'Not Applicable',
    'Other': 'Other',
}

# Display order for aggregated phases (excludes Not Applicable)
PHASE_AGG_ORDER = [
    'Early (Early Phase 1 + Phase 1)',
    'Mid (Phase 1/2 + Phase 2 + Phase 2/3)',
    'Late (Phase 3 + Phase 4)',
]

# Color palette for aggregated phases
PHASE_AGG_COLORS = {
    'Early (Early Phase 1 + Phase 1)': '#93c5fd',        # Light blue
    'Mid (Phase 1/2 + Phase 2 + Phase 2/3)': '#3b82f6',  # Blue
    'Late (Phase 3 + Phase 4)': '#1e40af',               # Dark blue
    'Not Applicable': '#d1d5db',                          # Light gray
}


# ============================================================
# Status Aggregation
# ============================================================
# Maps 10 registry statuses → 4 semantic groups
# Used for temporal trend analysis to show lifecycle patterns.

STATUS_AGG_MAP = {
    'Completed': 'Completed',
    'Recruiting': 'Active/Recruiting',
    'Active, not recruiting': 'Active/Recruiting',
    'Not yet recruiting': 'Active/Recruiting',
    'Enrolling by invitation': 'Active/Recruiting',
    'Terminated': 'Stopped',
    'Withdrawn': 'Stopped',
    'Suspended': 'Stopped',
    'Unknown': 'Unknown/Other',
    'Other': 'Unknown/Other',
}

# Display order for aggregated statuses
STATUS_AGG_ORDER = [
    'Completed',
    'Active/Recruiting',
    'Stopped',
    'Unknown/Other',
]

# Color palette for aggregated statuses
STATUS_AGG_COLORS = {
    'Completed': '#22c55e',       # Green
    'Active/Recruiting': '#3b82f6',  # Blue
    'Stopped': '#ef4444',         # Red
    'Unknown/Other': '#9ca3af',   # Gray
}


# ============================================================
# Outcome Colors (for Q2 Completion Analysis)
# ============================================================
# Semantic colors for trial outcomes

OUTCOME_COLORS = {
    'Completed': '#22c55e',      # Green (success)
    'Stopped': '#ef4444',        # Red (failure)
    'Active': '#3b82f6',         # Blue (ongoing)
}

# Failure type breakdown
FAILURE_TYPES = ['Terminated', 'Withdrawn', 'Suspended']

FAILURE_COLORS = {
    'Terminated': '#ef4444',     # Red
    'Withdrawn': '#f97316',      # Orange
    'Suspended': '#eab308',      # Yellow
}


# ============================================================
# Temporal Cohorts (for trend analysis)
# ============================================================

COHORT_BINS = [1989, 1999, 2009, 2019, 2026]
COHORT_LABELS = ['1990-1999', '2000-2009', '2010-2019', '2020-2025']
