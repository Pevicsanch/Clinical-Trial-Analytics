-- Q1.2 Yearly Trial Initiations
-- Purpose: Count trials by start year to describe initiation volume over time.
-- Note: Completion counts for recent years are expected to be lower due to reporting lag and time-to-completion.

WITH base AS (
  SELECT
    CAST(strftime('%Y', start_date) AS INTEGER) AS start_year,
    status
  FROM studies
  WHERE start_date IS NOT NULL
    AND start_date != ''
)
SELECT
  start_year,
  COUNT(*) AS trial_count,
  COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) AS completed_count,
  COUNT(CASE WHEN status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 1 END) AS recruiting_count
FROM base
WHERE start_year BETWEEN 1990 AND 2025
GROUP BY start_year
HAVING trial_count >= 5
ORDER BY start_year;