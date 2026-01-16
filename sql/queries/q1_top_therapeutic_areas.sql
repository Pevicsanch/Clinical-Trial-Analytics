-- Business Question: 1. Trial Landscape Overview
-- Purpose: Identify the top therapeutic areas (Conditions) being studied.
-- This highlights the organization's or industry's research priorities and high-competition areas.

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
