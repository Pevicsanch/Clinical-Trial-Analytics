-- q3_study_condition_map.sql
-- Granular study × condition map for Q3 enrollment analysis
-- One row per study-condition pair
-- Aggregation (sum, median, count) performed in Python to avoid double-counting
--
-- USAGE: Load with pd.read_sql_query() and aggregate in Python
-- Example:
--   df_map = pd.read_sql_query(sql, conn)
--   df_agg = df_map.groupby('condition_name').agg({
--       'study_id': 'nunique',
--       'enrollment': ['sum', 'median', 'count']
--   })

WITH study_base AS (
    SELECT
        s.study_id,
        s.nct_id,
        s.enrollment,
        s.phase,
        s.study_type,
        s.status,
        v.start_year,

        -- Sponsor info
        COALESCE(ls.is_industry_sponsor, 0) AS is_industry_sponsor,

        -- Outcome flags
        CASE WHEN UPPER(s.status) = 'COMPLETED' THEN 1 ELSE 0 END AS is_completed

    FROM studies s
    JOIN v_studies_clean v ON s.study_id = v.study_id
    LEFT JOIN (
        SELECT
            study_id,
            MAX(CASE WHEN UPPER(agency_class) = 'INDUSTRY' THEN 1 ELSE 0 END) AS is_industry_sponsor
        FROM sponsors
        WHERE UPPER(lead_or_collaborator) = 'LEAD'
        GROUP BY study_id
    ) ls ON s.study_id = ls.study_id

    WHERE v.is_start_year_in_scope = 1
      AND s.enrollment IS NOT NULL
      AND s.enrollment > 0
)

SELECT
    sb.study_id,
    sb.nct_id,

    -- Normalized condition name (consistent with ABT normalization)
    LOWER(TRIM(c.condition_name)) AS condition_name,

    -- Study-level metrics (repeated for each condition)
    sb.enrollment,
    sb.phase,
    sb.study_type,
    sb.status,
    sb.start_year,
    sb.is_industry_sponsor,
    sb.is_completed

FROM study_base sb
JOIN conditions c ON sb.study_id = c.study_id

-- No aggregation here - each study contributes once per condition
-- Python will aggregate correctly:
--   trial_count = df.groupby('condition_name')['study_id'].nunique()
--   total_enrollment = df.groupby('condition_name')['enrollment'].sum()
--   median_enrollment = df.groupby('condition_name')['enrollment'].median()
