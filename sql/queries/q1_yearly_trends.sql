-- Q1.2 Trial Initiations Over Time by Phase
-- Purpose:
--   Describe how clinical trial initiation volume evolves over time and
--   how the composition of registered studies varies across development phases.
--
-- Methodological notes:
--   - Uses validated start years only (analysis scope: 1990–2025).
--   - Includes all phase groups, including "Not Applicable".
--   - No volume thresholding is applied at query level; any filtering
--     for visualization or readability should be handled downstream.

SELECT
  start_year,
  phase_group,
  COUNT(*) AS trial_count
FROM v_studies_clean
WHERE
  is_start_year_in_scope = 1
GROUP BY
  start_year,
  phase_group
ORDER BY
  start_year,
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
  END;