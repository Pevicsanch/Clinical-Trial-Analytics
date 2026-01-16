-- Q1.2 Trial initiations by year and phase group (analysis scope: 1990–2025)
-- Output shape: one row per (start_year, phase_group)

WITH base AS (
  SELECT
    start_year,
    CASE
      WHEN phase IS NULL OR phase = '' THEN 'Not Applicable'
      WHEN phase = 'NA' THEN 'Not Applicable'
      WHEN phase LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
      WHEN phase = 'PHASE1' THEN 'Phase 1'
      WHEN phase LIKE '%PHASE1%' AND phase LIKE '%PHASE2%' THEN 'Phase 1/2'
      WHEN phase = 'PHASE2' THEN 'Phase 2'
      WHEN phase LIKE '%PHASE2%' AND phase LIKE '%PHASE3%' THEN 'Phase 2/3'
      WHEN phase = 'PHASE3' THEN 'Phase 3'
      WHEN phase = 'PHASE4' THEN 'Phase 4'
      ELSE 'Other'
    END AS phase_group
  FROM v_studies_clean
  WHERE is_start_year_in_scope = 1
)
SELECT
  start_year,
  phase_group,
  COUNT(*) AS trial_count
FROM base
GROUP BY start_year, phase_group
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