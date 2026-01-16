-- Business Question: 4. Geographic Insights
-- Purpose: Identify cities with highest trial concentration.
-- This highlights major research hubs and regional centers of excellence,
-- revealing where trial infrastructure is most developed.

SELECT
    l.city,
    l.country,
    COUNT(DISTINCT l.study_id) AS total_trials,
    COUNT(DISTINCT CASE WHEN s.status = 'COMPLETED' THEN l.study_id END) AS completed_trials,
    COUNT(DISTINCT CASE WHEN s.status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION') THEN l.study_id END) AS recruiting_trials,
    ROUND(
        COUNT(DISTINCT CASE WHEN s.status = 'COMPLETED' THEN l.study_id END) * 100.0 /
        COUNT(DISTINCT l.study_id),
        1
    ) AS completion_rate
FROM locations l
JOIN studies s ON l.study_id = s.study_id
WHERE l.city IS NOT NULL AND l.city != ''
  AND l.country IS NOT NULL AND l.country != ''
GROUP BY l.city, l.country
HAVING total_trials >= 20
ORDER BY total_trials DESC
LIMIT 30;
