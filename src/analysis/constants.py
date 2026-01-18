"""
Analysis constants for clinical trial data.

This module contains business-logic mappings for aggregating clinical trial
phases and statuses into meaningful groups for reporting and visualization.

These are analytical decisions, not visualization settings.
"""

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

# Display order for aggregated phases (excludes Not Applicable for trend charts)
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
