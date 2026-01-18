-- Q1.3 Top condition labels (analysis scope: 1990–2025)
-- Note: condition_name is a registry label (not a standardized therapeutic area taxonomy).

WITH scope AS (
  SELECT study_id, status
  FROM v_studies_clean
  WHERE is_start_year_in_scope = 1
),
totals AS (
  SELECT COUNT(*) AS n_trials_in_scope
  FROM scope
)
SELECT
  c.condition_name,
  COUNT(DISTINCT c.study_id) AS trial_count,
  ROUND(
    COUNT(DISTINCT c.study_id) * 100.0 / (SELECT n_trials_in_scope FROM totals),
    2
  ) AS pct_of_trials_in_scope,
  COUNT(DISTINCT CASE WHEN s.status = 'COMPLETED' THEN c.study_id END) AS completed_trials,
  COUNT(DISTINCT CASE WHEN s.status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION') THEN c.study_id END) AS recruiting_trials
FROM conditions c
JOIN scope s ON c.study_id = s.study_id
GROUP BY c.condition_name
HAVING trial_count >= 10
ORDER BY trial_count DESC
LIMIT 20;