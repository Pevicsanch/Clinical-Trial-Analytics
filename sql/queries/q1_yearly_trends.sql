-- Business Question: 1. Trial Landscape Overview
-- Purpose: Track the volume of new trial initiations over time (Yearly Trend).
-- This identifies growth patterns, seasonal trends, or impact of external events (e.g., pandemics, regulatory changes)
-- on clinical research activity.

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
