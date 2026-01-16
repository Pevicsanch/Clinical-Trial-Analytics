-- Business Question: 3. Enrollment Performance
-- Purpose: Compare enrollment across trial statuses (completed, recruiting, terminated).
-- This reveals whether terminated trials stopped earlier due to enrollment challenges
-- and whether recruiting trials are achieving adequate scale.

SELECT
    CASE
        WHEN status = 'COMPLETED' THEN 'Completed'
        WHEN status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 'Recruiting'
        WHEN status = 'ACTIVE_NOT_RECRUITING' THEN 'Active, not recruiting'
        WHEN status = 'TERMINATED' THEN 'Terminated'
        WHEN status = 'WITHDRAWN' THEN 'Withdrawn'
        WHEN status = 'SUSPENDED' THEN 'Suspended'
        ELSE 'Other'
    END AS status_group,
    COUNT(*) AS total_trials,
    COUNT(CASE WHEN enrollment IS NOT NULL AND enrollment > 0 THEN 1 END) AS trials_with_enrollment,
    ROUND(AVG(CASE WHEN enrollment IS NOT NULL AND enrollment > 0 THEN enrollment END), 0) AS avg_enrollment,
    ROUND(MIN(CASE WHEN enrollment IS NOT NULL AND enrollment > 0 THEN enrollment END), 0) AS min_enrollment,
    ROUND(MAX(CASE WHEN enrollment IS NOT NULL AND enrollment > 0 THEN enrollment END), 0) AS max_enrollment,
    COUNT(CASE WHEN enrollment >= 100 THEN 1 END) AS trials_100plus,
    COUNT(CASE WHEN enrollment < 50 AND enrollment > 0 THEN 1 END) AS trials_under_50
FROM studies
GROUP BY status_group
HAVING total_trials >= 10
ORDER BY avg_enrollment DESC;
