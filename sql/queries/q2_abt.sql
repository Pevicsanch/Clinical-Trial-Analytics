-- q2_abt.sql
-- Analytical Base Table for Q2: Completion & Termination Analysis
-- One row per study with outcome, covariates, and time features.
-- Scope: studies with valid start_year in analysis range (1990–2025).
--
-- USAGE: Pass :extraction_date parameter from notebook for reproducibility.
--   pd.read_sql_query(sql, conn, params={"extraction_date": "2026-01-16"})

-- ============================================================
-- OUTCOME DEFINITIONS
-- ============================================================
-- outcome_group:
--   - Completed: COMPLETED
--   - Stopped: TERMINATED, WITHDRAWN, SUSPENDED
--   - Active (censored): RECRUITING, NOT_YET_RECRUITING, 
--                        ACTIVE_NOT_RECRUITING, ENROLLING_BY_INVITATION
--
-- For completion rate analysis: use Completed + Stopped only (resolved)
--   resolved_completion_rate = Completed / (Completed + Stopped)
-- For survival analysis: use time_days with event indicator
--
-- IMPORTANT: Stopped studies do NOT have a reliable stop_date.
--   completion_date ≠ stop_date. We set end_date = NULL for Stopped.
-- ============================================================

WITH 
-- Sponsor features (lead sponsor only, aggregated to handle duplicates)
lead_sponsor AS (
    SELECT
        study_id,
        MAX(agency) AS lead_agency,
        MAX(agency_class) AS lead_agency_class,
        MAX(CASE WHEN UPPER(agency_class) = 'INDUSTRY' THEN 1 ELSE 0 END) AS is_industry_sponsor
    FROM sponsors
    WHERE UPPER(lead_or_collaborator) = 'LEAD'
    GROUP BY study_id
),

-- Condition counts and oncology flag per study (normalized strings)
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
    -- OUTCOME
    -- ============================================================
    s.status AS status_raw,
    
    -- Outcome group (3 categories)
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN 'Completed'
        WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 'Stopped'
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 'Active'
        ELSE 'Other'
    END AS outcome_group,
    
    -- Failure type (for Stopped studies only)
    CASE
        WHEN UPPER(s.status) = 'TERMINATED' THEN 'Terminated'
        WHEN UPPER(s.status) = 'WITHDRAWN' THEN 'Withdrawn'
        WHEN UPPER(s.status) = 'SUSPENDED' THEN 'Suspended'
        ELSE NULL
    END AS failure_type,
    
    -- Binary indicators for modeling
    CASE WHEN UPPER(s.status) = 'COMPLETED' THEN 1 ELSE 0 END AS is_completed,
    CASE WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 1 ELSE 0 END AS is_stopped,
    CASE WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                   'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 1 ELSE 0 END AS is_active,

    -- Success indicator for resolved-outcome modeling (NULL for Active)
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN 1
        WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 0
        ELSE NULL
    END AS is_successful,

    -- Resolved outcome label (NULL for Active)
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN 'Completed'
        WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 'Stopped'
        ELSE NULL
    END AS resolved_outcome,
    
    -- ============================================================
    -- PHASE (covariate)
    -- ============================================================
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
    
    -- Aggregated phase (for simpler models)
    CASE
        WHEN s.phase IS NULL OR TRIM(s.phase) = '' OR UPPER(TRIM(s.phase)) = 'NA' THEN 'Not Applicable'
        WHEN UPPER(s.phase) LIKE '%EARLY_PHASE%' OR UPPER(TRIM(s.phase)) = 'PHASE1' THEN 'Early'
        WHEN UPPER(s.phase) LIKE '%PHASE1%' AND UPPER(s.phase) LIKE '%PHASE2%' THEN 'Mid'
        WHEN UPPER(TRIM(s.phase)) = 'PHASE2' THEN 'Mid'
        WHEN UPPER(s.phase) LIKE '%PHASE2%' AND UPPER(s.phase) LIKE '%PHASE3%' THEN 'Mid'
        WHEN UPPER(TRIM(s.phase)) IN ('PHASE3', 'PHASE4') THEN 'Late'
        ELSE 'Other'
    END AS phase_agg,
    
    -- ============================================================
    -- STUDY TYPE (covariate)
    -- ============================================================
    s.study_type,
    CASE WHEN UPPER(s.study_type) = 'INTERVENTIONAL' THEN 1 ELSE 0 END AS is_interventional,
    
    -- ============================================================
    -- ENROLLMENT (covariate)
    -- ============================================================
    s.enrollment,
    s.enrollment_type,
    CASE WHEN s.enrollment IS NOT NULL AND s.enrollment > 0 THEN 1 ELSE 0 END AS has_enrollment,
    CASE WHEN UPPER(s.enrollment_type) = 'ACTUAL' THEN 1 ELSE 0 END AS is_enrollment_actual,
    
    -- Enrollment buckets (for stratification)
    CASE
        WHEN s.enrollment IS NULL OR s.enrollment = 0 THEN 'Unknown'
        WHEN s.enrollment < 50 THEN '<50'
        WHEN s.enrollment < 100 THEN '50-99'
        WHEN s.enrollment < 500 THEN '100-499'
        WHEN s.enrollment < 1000 THEN '500-999'
        ELSE '1000+'
    END AS enrollment_bucket,
    
    -- ============================================================
    -- SPONSOR FEATURES (covariate)
    -- ============================================================
    ls.lead_agency,
    ls.lead_agency_class,
    COALESCE(ls.is_industry_sponsor, 0) AS is_industry_sponsor,
    
    -- ============================================================
    -- CONDITION/THERAPEUTIC FEATURES (covariate)
    -- ============================================================
    COALESCE(cf.n_conditions, 0) AS n_conditions,
    CASE WHEN COALESCE(cf.n_conditions, 0) > 0 THEN 1 ELSE 0 END AS has_conditions,
    COALESCE(cf.has_oncology_label, 0) AS has_oncology_label,
    
    -- ============================================================
    -- TIME FEATURES
    -- ============================================================
    s.start_date,
    v.start_year,
    s.completion_date,
    s.primary_completion_date,
    
    -- Extraction date (passed as parameter for reproducibility)
    date(:extraction_date) AS extraction_date,
    
    -- End date (for time calculation)
    -- IMPORTANT: Stopped studies do NOT have a reliable stop_date.
    -- completion_date is NOT the stop date for terminated/withdrawn trials.
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN COALESCE(s.completion_date, s.primary_completion_date)
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN date(:extraction_date)
        -- Stopped: no reliable stop_date available
        ELSE NULL
    END AS end_date,
    
    -- Time in days (from start to end) - only defined for Completed and Active
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' 
             AND s.start_date IS NOT NULL 
             AND COALESCE(s.completion_date, s.primary_completion_date) IS NOT NULL
        THEN julianday(COALESCE(s.completion_date, s.primary_completion_date)) - julianday(s.start_date)
        
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION')
             AND s.start_date IS NOT NULL
        THEN julianday(date(:extraction_date)) - julianday(s.start_date)
        
        -- Stopped: cannot calculate time-to-stop without stop_date
        ELSE NULL
    END AS time_days,
    
    -- ============================================================
    -- SURVIVAL ANALYSIS FEATURES
    -- ============================================================
    -- Event indicator for time-to-completion analysis:
    -- event = 1 if Completed, 0 if Active (censored)
    -- Stopped is excluded from this analysis (no time_days)
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN 1
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 0
        ELSE NULL
    END AS event_completed,
    
    -- Resolved indicator: 1 if Completed or Stopped (for completion rate analysis)
    CASE WHEN UPPER(s.status) IN ('COMPLETED', 'TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 1 ELSE 0 END AS is_resolved

FROM v_studies_clean v
JOIN studies s ON v.study_id = s.study_id
LEFT JOIN lead_sponsor ls ON s.study_id = ls.study_id
LEFT JOIN condition_features cf ON s.study_id = cf.study_id

WHERE 
    -- Scope: valid start year in analysis range
    v.is_start_year_in_scope = 1
    AND s.start_date IS NOT NULL
    -- Exclude unknown/other statuses for cleaner analysis
    AND UPPER(s.status) IN (
        'COMPLETED', 
        'TERMINATED', 'WITHDRAWN', 'SUSPENDED',
        'RECRUITING', 'NOT_YET_RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION'
    )
