-- q1_temporal_base.sql
-- Temporal base table for trends analysis (phase, status).
-- One row per study. Notebook handles aggregation by year/month.
-- Scope: validated start_year within 1990–2025 analysis window.

SELECT
  s.study_id,
  s.start_date,
  s.start_year,

  -- Period key: first day of month (for monthly aggregation)
  date(s.start_date, 'start of month') AS month_start,

  -- Phase group (display label)
  CASE
    WHEN s.phase IS NULL OR s.phase = '' OR s.phase = 'NA' THEN 'Not Applicable'
    WHEN s.phase LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
    WHEN s.phase LIKE '%PHASE1%' AND s.phase LIKE '%PHASE2%' THEN 'Phase 1/2'
    WHEN s.phase LIKE '%PHASE2%' AND s.phase LIKE '%PHASE3%' THEN 'Phase 2/3'
    WHEN s.phase = 'PHASE1' THEN 'Phase 1'
    WHEN s.phase = 'PHASE2' THEN 'Phase 2'
    WHEN s.phase = 'PHASE3' THEN 'Phase 3'
    WHEN s.phase = 'PHASE4' THEN 'Phase 4'
    ELSE 'Other'
  END AS phase_group,

  -- Phase sort order (combos before singletons)
  CASE
    WHEN s.phase IS NULL OR s.phase = '' OR s.phase = 'NA' THEN 8
    WHEN s.phase LIKE '%EARLY_PHASE%' THEN 1
    WHEN s.phase LIKE '%PHASE1%' AND s.phase LIKE '%PHASE2%' THEN 3
    WHEN s.phase LIKE '%PHASE2%' AND s.phase LIKE '%PHASE3%' THEN 5
    WHEN s.phase = 'PHASE1' THEN 2
    WHEN s.phase = 'PHASE2' THEN 4
    WHEN s.phase = 'PHASE3' THEN 6
    WHEN s.phase = 'PHASE4' THEN 7
    ELSE 9
  END AS phase_order,

  -- Status group (display label)
  CASE
    WHEN UPPER(s.status) = 'COMPLETED' THEN 'Completed'
    WHEN UPPER(s.status) = 'RECRUITING' THEN 'Recruiting'
    WHEN UPPER(s.status) = 'ACTIVE_NOT_RECRUITING' THEN 'Active, not recruiting'
    WHEN UPPER(s.status) = 'NOT_YET_RECRUITING' THEN 'Not yet recruiting'
    WHEN UPPER(s.status) = 'ENROLLING_BY_INVITATION' THEN 'Enrolling by invitation'
    WHEN UPPER(s.status) = 'TERMINATED' THEN 'Terminated'
    WHEN UPPER(s.status) = 'WITHDRAWN' THEN 'Withdrawn'
    WHEN UPPER(s.status) = 'SUSPENDED' THEN 'Suspended'
    WHEN UPPER(s.status) = 'UNKNOWN' THEN 'Unknown'
    ELSE 'Other'
  END AS status_group,

  -- Status sort order
  CASE
    WHEN UPPER(s.status) = 'COMPLETED' THEN 1
    WHEN UPPER(s.status) = 'RECRUITING' THEN 2
    WHEN UPPER(s.status) = 'ACTIVE_NOT_RECRUITING' THEN 3
    WHEN UPPER(s.status) = 'NOT_YET_RECRUITING' THEN 4
    WHEN UPPER(s.status) = 'ENROLLING_BY_INVITATION' THEN 5
    WHEN UPPER(s.status) = 'TERMINATED' THEN 6
    WHEN UPPER(s.status) = 'WITHDRAWN' THEN 7
    WHEN UPPER(s.status) = 'SUSPENDED' THEN 8
    WHEN UPPER(s.status) = 'UNKNOWN' THEN 9
    ELSE 10
  END AS status_order

FROM v_studies_clean s
WHERE s.is_start_year_in_scope = 1
  AND s.start_date IS NOT NULL;
