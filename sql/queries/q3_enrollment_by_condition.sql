-- Business Question: 3. Enrollment Performance
-- Purpose: Identify which therapeutic areas achieve higher enrollment.
-- This highlights conditions where patient recruitment is more successful
-- and reveals competitive or challenging recruitment landscapes.

SELECT
    c.condition_name,
    COUNT(DISTINCT c.study_id) AS total_trials,
    COUNT(DISTINCT CASE WHEN s.enrollment IS NOT NULL AND s.enrollment > 0 THEN c.study_id END) AS trials_with_enrollment,
    ROUND(AVG(CASE WHEN s.enrollment IS NOT NULL AND s.enrollment > 0 THEN s.enrollment END), 0) AS avg_enrollment,
    COUNT(DISTINCT CASE WHEN s.enrollment >= 100 THEN c.study_id END) AS trials_100plus,
    COUNT(DISTINCT CASE WHEN s.enrollment >= 500 THEN c.study_id END) AS trials_500plus,
    ROUND(
        COUNT(DISTINCT CASE WHEN s.enrollment IS NOT NULL AND s.enrollment > 0 THEN c.study_id END) * 100.0 /
        COUNT(DISTINCT c.study_id),
        1
    ) AS pct_with_enrollment
FROM conditions c
JOIN studies s ON c.study_id = s.study_id
GROUP BY c.condition_name
HAVING total_trials >= 50
ORDER BY avg_enrollment DESC
LIMIT 20;
