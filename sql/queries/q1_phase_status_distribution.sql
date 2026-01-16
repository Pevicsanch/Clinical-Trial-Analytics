-- Business Question: 1. Trial Landscape Overview
-- Purpose: Analyze the distribution of clinical trials across different phases and statuses.
-- This view helps stakeholders understand the maturity of the pipeline (e.g., how many early vs late stage trials)
-- and the operational status (recruiting, active, completed).

SELECT
    CASE
        WHEN phase IS NULL OR phase = '' THEN 'Not Applicable'
        WHEN phase = 'NA' THEN 'Not Applicable'
        WHEN phase LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
        WHEN phase = 'PHASE1' THEN 'Phase 1'
        WHEN phase = 'PHASE2' THEN 'Phase 2'
        WHEN phase = 'PHASE3' THEN 'Phase 3'
        WHEN phase = 'PHASE4' THEN 'Phase 4'
        WHEN phase LIKE '%PHASE1%' AND phase LIKE '%PHASE2%' THEN 'Phase 1/2'
        WHEN phase LIKE '%PHASE2%' AND phase LIKE '%PHASE3%' THEN 'Phase 2/3'
        ELSE 'Other'
    END AS phase_group,
    CASE
        WHEN status = 'COMPLETED' THEN 'Completed'
        WHEN status = 'RECRUITING' THEN 'Recruiting'
        WHEN status = 'ACTIVE_NOT_RECRUITING' THEN 'Active, not recruiting'
        WHEN status = 'NOT_YET_RECRUITING' THEN 'Not yet recruiting'
        WHEN status = 'TERMINATED' THEN 'Terminated'
        WHEN status = 'SUSPENDED' THEN 'Suspended'
        WHEN status = 'WITHDRAWN' THEN 'Withdrawn'
        WHEN status = 'ENROLLING_BY_INVITATION' THEN 'Enrolling by invitation'
        WHEN status = 'AVAILABLE' THEN 'Available'
        WHEN status = 'NO_LONGER_AVAILABLE' THEN 'No longer available'
        WHEN status = 'TEMPORARILY_NOT_AVAILABLE' THEN 'Temporarily not available'
        WHEN status = 'APPROVED_FOR_MARKETING' THEN 'Approved for marketing'
        WHEN status = 'WITHHELD' THEN 'Withheld'
        WHEN status = 'UNKNOWN' THEN 'Unknown'
        ELSE status
    END AS status_label,
    COUNT(*) AS trial_count
FROM studies
GROUP BY phase_group, status_label
ORDER BY
    CASE phase_group
        WHEN 'Early Phase 1' THEN 1
        WHEN 'Phase 1' THEN 2
        WHEN 'Phase 1/2' THEN 3
        WHEN 'Phase 2' THEN 4
        WHEN 'Phase 2/3' THEN 5
        WHEN 'Phase 3' THEN 6
        WHEN 'Phase 4' THEN 7
        WHEN 'Not Applicable' THEN 8
        ELSE 9
    END,
    trial_count DESC;
