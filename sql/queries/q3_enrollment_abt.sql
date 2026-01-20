-- q3_enrollment_abt.sql
-- Analytical Base Table for Q3: Enrollment Performance Analysis
-- One row per study with enrollment metrics and covariates.
-- Scope: studies with valid start_year in analysis range (1990–2025).
--
-- USAGE: Pass :extraction_date parameter from notebook for reproducibility.
--   pd.read_sql_query(sql, conn, params={"extraction_date": "2026-01-18"})

-- ============================================================
-- ENROLLMENT METRICS
-- ============================================================
-- enrollment: Reported enrollment (mix of ACTUAL and ANTICIPATED)
-- enrollment_type: ACTUAL vs ANTICIPATED (if available)
-- has_enrollment: Flag for enrollment > 0 (excludes missing/zero)
--
-- IMPORTANT: Missing enrollment appears non-random.
-- From Q2 analysis: trials with missing enrollment have 16% completion
-- vs 86% overall, suggesting correlation with early withdrawal before enrollment began.
-- Statistical characterization of missingness (MAR/MNAR) requires formal modeling.
-- ============================================================

WITH
-- Sponsor features (lead sponsor only)
-- Note: Uses MAX() aggregation; if multiple LEAD sponsors exist (data quality issue),
-- one is selected arbitrarily. has_multiple_leads flag identifies such cases.
lead_sponsor AS (
    SELECT
        study_id,
        MAX(agency) AS lead_agency,
        MAX(agency_class) AS lead_agency_class,
        MAX(CASE WHEN UPPER(agency_class) = 'INDUSTRY' THEN 1 ELSE 0 END) AS is_industry_sponsor,
        CASE WHEN COUNT(DISTINCT agency) > 1 THEN 1 ELSE 0 END AS has_multiple_leads
    FROM sponsors
    WHERE UPPER(lead_or_collaborator) = 'LEAD'
    GROUP BY study_id
),

-- Condition features (count and oncology flag)
condition_features AS (
    SELECT
        c.study_id,
        COUNT(DISTINCT LOWER(TRIM(c.condition_name))) AS n_conditions,
        MAX(CASE
            WHEN LOWER(TRIM(c.condition_name)) LIKE '%cancer%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%tumor%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%tumour%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%carcinoma%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%leukemia%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%lymphoma%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%melanoma%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%sarcoma%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%neoplasm%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%oncolog%'
            THEN 1 ELSE 0
        END) AS has_oncology_label
    FROM conditions c
    GROUP BY c.study_id
)

SELECT
    -- ============================================================
    -- IDENTIFICATION
    -- ============================================================
    s.study_id,
    s.nct_id,

    -- ============================================================
    -- ENROLLMENT METRICS (PRIMARY ANALYSIS VARIABLES)
    -- ============================================================
    s.enrollment,
    s.enrollment_type,

    -- Binary flags for filtering and analysis
    CASE WHEN s.enrollment IS NOT NULL AND s.enrollment > 0 THEN 1 ELSE 0 END AS has_enrollment,
    CASE WHEN UPPER(s.enrollment_type) = 'ACTUAL' THEN 1 ELSE 0 END AS is_enrollment_actual,
    CASE WHEN s.enrollment IS NULL THEN 1 ELSE 0 END AS is_enrollment_missing,
    CASE WHEN s.enrollment = 0 THEN 1 ELSE 0 END AS is_enrollment_zero,

    -- Enrollment buckets for stratification (Missing/Zero separated)
    CASE
        WHEN s.enrollment IS NULL THEN 'Missing'
        WHEN s.enrollment = 0 THEN 'Zero'
        WHEN s.enrollment < 50 THEN 'Small (<50)'
        WHEN s.enrollment < 200 THEN 'Medium (50-199)'
        WHEN s.enrollment < 1000 THEN 'Large (200-999)'
        ELSE 'Mega (1000+)'
    END AS enrollment_bucket,

    -- Extreme outlier flag (for sensitivity analysis)
    CASE WHEN s.enrollment > 5000 THEN 1 ELSE 0 END AS is_extreme_enrollment,

    -- ============================================================
    -- STUDY CHARACTERISTICS (COVARIATES)
    -- ============================================================

    -- Phase
    s.phase AS phase_raw,
    CASE
        WHEN s.phase IS NULL OR TRIM(s.phase) = '' OR UPPER(TRIM(s.phase)) = 'NA' THEN 'Not Applicable'
        WHEN UPPER(s.phase) LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
        WHEN UPPER(s.phase) LIKE '%PHASE1%' AND UPPER(s.phase) LIKE '%PHASE2%' THEN 'Phase 1/2'
        WHEN UPPER(s.phase) LIKE '%PHASE2%' AND UPPER(s.phase) LIKE '%PHASE3%' THEN 'Phase 2/3'
        WHEN UPPER(TRIM(s.phase)) = 'PHASE1' THEN 'Phase 1'
        WHEN UPPER(TRIM(s.phase)) = 'PHASE2' THEN 'Phase 2'
        WHEN UPPER(TRIM(s.phase)) = 'PHASE3' THEN 'Phase 3'
        WHEN UPPER(TRIM(s.phase)) = 'PHASE4' THEN 'Phase 4'
        ELSE 'Other'
    END AS phase_group,

    -- Study type (Interventional vs Observational)
    s.study_type,
    CASE WHEN UPPER(s.study_type) = 'INTERVENTIONAL' THEN 1 ELSE 0 END AS is_interventional,

    -- Sponsor type
    ls.lead_agency,
    ls.lead_agency_class,
    COALESCE(ls.is_industry_sponsor, 0) AS is_industry_sponsor,
    COALESCE(ls.has_multiple_leads, 0) AS has_multiple_leads,

    -- Condition features
    COALESCE(cf.n_conditions, 0) AS n_conditions,
    COALESCE(cf.has_oncology_label, 0) AS has_oncology_label,

    -- ============================================================
    -- TEMPORAL FEATURES
    -- ============================================================
    s.start_date,
    v.start_year,

    -- Completion dates (for QA and consistency checks)
    s.completion_date,
    s.primary_completion_date,

    -- Extraction date (reproducibility)
    date(:extraction_date) AS extraction_date,

    -- Temporal cohorts for trend analysis
    CASE
        WHEN v.start_year < 2000 THEN '1990-1999'
        WHEN v.start_year < 2010 THEN '2000-2009'
        WHEN v.start_year < 2020 THEN '2010-2019'
        ELSE '2020-2025'
    END AS start_cohort,

    -- Years since 2000 (for regression interpretability)
    v.start_year - 2000 AS years_since_2000,

    -- ============================================================
    -- OUTCOME (for secondary analysis: enrollment vs completion)
    -- ============================================================
    s.status AS status_raw,
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN 'Completed'
        WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 'Stopped'
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING',
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 'Active'
        ELSE 'Other'
    END AS outcome_group,

    CASE WHEN UPPER(s.status) = 'COMPLETED' THEN 1 ELSE 0 END AS is_completed,
    CASE WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 1 ELSE 0 END AS is_stopped,

    -- Resolved trials only (for completion analysis)
    CASE WHEN UPPER(s.status) IN ('COMPLETED', 'TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 1 ELSE 0 END AS is_resolved

FROM v_studies_clean v
JOIN studies s ON v.study_id = s.study_id
LEFT JOIN lead_sponsor ls ON s.study_id = ls.study_id
LEFT JOIN condition_features cf ON s.study_id = cf.study_id

WHERE
    -- Scope: valid start year in analysis range
    v.is_start_year_in_scope = 1
    AND s.start_date IS NOT NULL
    -- Include all trials (we'll filter by has_enrollment in notebook)
    AND UPPER(s.status) IN (
        'COMPLETED',
        'TERMINATED', 'WITHDRAWN', 'SUSPENDED',
        'RECRUITING', 'NOT_YET_RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION'
    )
