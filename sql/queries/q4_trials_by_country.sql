-- Business Question: 4. Geographic Insights
-- Purpose: Identify which countries host the most clinical trials.
-- This reveals global research concentration and helps understand
-- geographic diversity in trial execution.

SELECT
    l.country,
    COUNT(DISTINCT l.study_id) AS total_trials,
    COUNT(DISTINCT CASE WHEN s.status = 'COMPLETED' THEN l.study_id END) AS completed_trials,
    COUNT(DISTINCT CASE WHEN s.status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION') THEN l.study_id END) AS recruiting_trials,
    COUNT(DISTINCT CASE WHEN s.status = 'TERMINATED' THEN l.study_id END) AS terminated_trials,
    ROUND(
        COUNT(DISTINCT CASE WHEN s.status = 'COMPLETED' THEN l.study_id END) * 100.0 /
        COUNT(DISTINCT l.study_id),
        1
    ) AS completion_rate
FROM locations l
JOIN studies s ON l.study_id = s.study_id
WHERE l.country IS NOT NULL AND l.country != ''
GROUP BY l.country
HAVING total_trials >= 10
ORDER BY total_trials DESC
LIMIT 30;
