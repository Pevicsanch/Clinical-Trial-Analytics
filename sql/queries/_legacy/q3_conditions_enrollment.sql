-- q3_conditions_enrollment.sql
-- Aggregate enrollment metrics by condition
-- Used in Section 4 of Q3 enrollment analysis

WITH study_enrollment AS (
    SELECT
        s.study_id,
        s.nct_id,
        s.enrollment,
        s.phase,
        s.study_type,
        COALESCE(ls.is_industry_sponsor, 0) AS is_industry_sponsor,
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
    c.condition_name,

    -- Count metrics
    COUNT(DISTINCT c.study_id) AS trial_count,

    -- Enrollment aggregations
    SUM(se.enrollment) AS total_enrollment,
    CAST(AVG(se.enrollment) AS INTEGER) AS mean_enrollment,
    MIN(se.enrollment) AS min_enrollment,
    MAX(se.enrollment) AS max_enrollment,

    -- Characteristics
    ROUND(AVG(se.is_completed) * 100, 1) AS completion_rate_pct,
    ROUND(AVG(se.is_industry_sponsor) * 100, 1) AS pct_industry

FROM conditions c
JOIN study_enrollment se ON c.study_id = se.study_id
GROUP BY c.condition_name
HAVING COUNT(DISTINCT c.study_id) >= 50  -- Minimum sample size for reliability
ORDER BY total_enrollment DESC
