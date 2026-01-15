-- ============================================================================
-- Business Question #1: Trial Landscape Analysis
-- ============================================================================
--
-- Question: What is the current landscape of clinical trials?
--
-- This query provides three analytical outputs:
-- 1. Phase × Status distribution (cross-tabulation of research activity)
-- 2. Yearly trial initiation trend (temporal evolution)
-- 3. Top 20 therapeutic areas by trial count (research priorities)
--
-- Note: This query focuses on STRUCTURE (counts, distribution).
-- Scale metrics (enrollment) are analyzed in Business Question #3.
-- ============================================================================


-- ============================================================================
-- OUTPUT 1: Phase × Status Distribution
-- ============================================================================
-- Insight: Where is research activity concentrated?
-- Use: Understand which phases have most active/completed/recruiting trials

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


-- ============================================================================
-- OUTPUT 2: Yearly Trial Initiation Trend
-- ============================================================================
-- Insight: Temporal evolution of clinical trial activity
-- Use: Detect growth patterns, identify peak years

SELECT
    CAST(strftime('%Y', start_date) AS INTEGER) AS start_year,
    COUNT(*) AS trial_count,
    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) AS completed_count,
    COUNT(CASE WHEN status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 1 END) AS recruiting_count
FROM studies
WHERE
    start_date IS NOT NULL
    AND start_date != ''
    AND CAST(strftime('%Y', start_date) AS INTEGER) >= 1990
    AND CAST(strftime('%Y', start_date) AS INTEGER) <= 2025
GROUP BY start_year
HAVING trial_count >= 5
ORDER BY start_year;


-- ============================================================================
-- OUTPUT 3: Top 20 Therapeutic Areas by Trial Count
-- ============================================================================
-- Insight: Which diseases/conditions are most studied?
-- Use: Identify therapeutic priorities and research focus

SELECT
    c.condition_name,
    COUNT(DISTINCT c.study_id) AS trial_count,
    ROUND(COUNT(DISTINCT c.study_id) * 100.0 / (SELECT COUNT(*) FROM studies), 2) AS percentage_of_trials,
    COUNT(DISTINCT CASE WHEN s.status = 'COMPLETED' THEN s.study_id END) AS completed_trials,
    COUNT(DISTINCT CASE WHEN s.status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION') THEN s.study_id END) AS recruiting_trials
FROM conditions c
JOIN studies s ON c.study_id = s.study_id
GROUP BY c.condition_name
HAVING trial_count >= 10
ORDER BY trial_count DESC
LIMIT 20;
