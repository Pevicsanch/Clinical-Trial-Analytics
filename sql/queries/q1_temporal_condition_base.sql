-- q1_temporal_condition_base.sql
-- Temporal base table for therapeutic-area (condition label) trends.
-- One row per (study_id × condition_name).
-- Notebook handles aggregation by year/month and condition.
-- Scope: validated start_year within 1990–2025 analysis window.

SELECT
  s.study_id,
  s.start_date,
  s.start_year,

  -- Period key: first day of month (for monthly aggregation)
  date(s.start_date, 'start of month') AS month_start,

  -- Condition label (registry free-text)
  c.condition_name

FROM v_studies_clean s
JOIN conditions c
  ON s.study_id = c.study_id

WHERE s.is_start_year_in_scope = 1
  AND s.start_date IS NOT NULL
  AND c.condition_name IS NOT NULL
  AND c.condition_name != '';
