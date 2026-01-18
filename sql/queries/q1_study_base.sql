-- q1_study_base.sql
-- Base table for Q1 distribution analysis (phase, status).
-- One row per study. Notebook handles aggregation.
-- Scope: studies with validated start_year in analysis range (1990–2025).

SELECT
  study_id,

  -- Raw fields for traceability
  phase AS phase_raw,
  status AS status_raw,

  -- Phase (normalized display label)
  -- Note: combo phases checked before singletons to avoid false matches
  CASE
    WHEN phase IS NULL OR phase = '' OR phase = 'NA' THEN 'Not Applicable'
    WHEN phase LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
    WHEN phase LIKE '%PHASE1%' AND phase LIKE '%PHASE2%' THEN 'Phase 1/2'
    WHEN phase LIKE '%PHASE2%' AND phase LIKE '%PHASE3%' THEN 'Phase 2/3'
    WHEN phase = 'PHASE1' THEN 'Phase 1'
    WHEN phase = 'PHASE2' THEN 'Phase 2'
    WHEN phase = 'PHASE3' THEN 'Phase 3'
    WHEN phase = 'PHASE4' THEN 'Phase 4'
    ELSE 'Other'
  END AS phase_group,

  -- Phase sort order (aligned with phase_group logic)
  CASE
    WHEN phase IS NULL OR phase = '' OR phase = 'NA' THEN 8
    WHEN phase LIKE '%EARLY_PHASE%' THEN 1
    WHEN phase LIKE '%PHASE1%' AND phase LIKE '%PHASE2%' THEN 3
    WHEN phase LIKE '%PHASE2%' AND phase LIKE '%PHASE3%' THEN 5
    WHEN phase = 'PHASE1' THEN 2
    WHEN phase = 'PHASE2' THEN 4
    WHEN phase = 'PHASE3' THEN 6
    WHEN phase = 'PHASE4' THEN 7
    ELSE 9
  END AS phase_order,

  -- Status (normalized display label)
  CASE
    WHEN UPPER(status) = 'COMPLETED' THEN 'Completed'
    WHEN UPPER(status) = 'RECRUITING' THEN 'Recruiting'
    WHEN UPPER(status) = 'ACTIVE_NOT_RECRUITING' THEN 'Active, not recruiting'
    WHEN UPPER(status) = 'NOT_YET_RECRUITING' THEN 'Not yet recruiting'
    WHEN UPPER(status) = 'ENROLLING_BY_INVITATION' THEN 'Enrolling by invitation'
    WHEN UPPER(status) = 'TERMINATED' THEN 'Terminated'
    WHEN UPPER(status) = 'WITHDRAWN' THEN 'Withdrawn'
    WHEN UPPER(status) = 'SUSPENDED' THEN 'Suspended'
    WHEN UPPER(status) = 'UNKNOWN' THEN 'Unknown'
    ELSE 'Other'
  END AS status_group,

  -- Status sort order (reporting priority)
  CASE
    WHEN UPPER(status) = 'COMPLETED' THEN 1
    WHEN UPPER(status) = 'RECRUITING' THEN 2
    WHEN UPPER(status) = 'ACTIVE_NOT_RECRUITING' THEN 3
    WHEN UPPER(status) = 'NOT_YET_RECRUITING' THEN 4
    WHEN UPPER(status) = 'ENROLLING_BY_INVITATION' THEN 5
    WHEN UPPER(status) = 'TERMINATED' THEN 6
    WHEN UPPER(status) = 'WITHDRAWN' THEN 7
    WHEN UPPER(status) = 'SUSPENDED' THEN 8
    WHEN UPPER(status) = 'UNKNOWN' THEN 9
    ELSE 10
  END AS status_order

FROM v_studies_clean
WHERE is_start_year_in_scope = 1;
