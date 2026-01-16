-- ---------------------------------------------------------------------------
-- Views: cleaned / derived fields for analytics (keep raw untouched)
-- ---------------------------------------------------------------------------

DROP VIEW IF EXISTS v_studies_clean;

CREATE VIEW v_studies_clean AS
SELECT
  s.*,

  -- Extract start_year safely
  CAST(strftime('%Y', s.start_date) AS INTEGER) AS start_year,

  -- Valid date flag (must have start_date and parseable year)
  CASE
    WHEN s.start_date IS NULL OR s.start_date = '' THEN 0
    WHEN strftime('%Y', s.start_date) IS NULL THEN 0
    ELSE 1
  END AS has_valid_start_date,

  -- Bucket for analysis (avoid misleading min/max from outliers)
  CASE
    WHEN s.start_date IS NULL OR s.start_date = '' THEN 'missing'
    WHEN strftime('%Y', s.start_date) IS NULL THEN 'invalid'
    WHEN CAST(strftime('%Y', s.start_date) AS INTEGER) < 1990 THEN '<1990'
    WHEN CAST(strftime('%Y', s.start_date) AS INTEGER) > 2025 THEN '>2025'
    ELSE '1990–2025'
  END AS start_year_bucket,

  -- Boolean for “in scope” temporal analysis
  CASE
    WHEN s.start_date IS NULL OR s.start_date = '' THEN 0
    WHEN strftime('%Y', s.start_date) IS NULL THEN 0
    WHEN CAST(strftime('%Y', s.start_date) AS INTEGER) BETWEEN 1990 AND 2025 THEN 1
    ELSE 0
  END AS is_start_year_in_scope

FROM studies s;