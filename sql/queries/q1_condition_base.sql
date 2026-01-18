-- q1_condition_base.sql
-- Base table for Q1 condition label analysis.
-- One row per (study_id × condition_name).
-- Scope: studies with validated start_year in analysis range (1990–2025).
-- Note: A study may have multiple condition labels; aggregation in notebook.

SELECT
  c.study_id,
  c.condition_name
FROM conditions c
JOIN v_studies_clean s
  ON c.study_id = s.study_id
WHERE s.is_start_year_in_scope = 1;
