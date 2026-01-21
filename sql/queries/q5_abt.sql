-- q5_abt.sql
-- Analytical Base Table for Q5: Duration Analysis
-- One row per study with duration features, covariates, and survival indicators.
-- Scope: studies with valid start_year in analysis range (1990–2025).
--
-- ============================================================
-- DURATION ANALYSIS FRAMEWORK
-- ============================================================
-- 
-- KEY INSIGHT: Duration analysis requires survival analysis due to CENSORING.
--
-- POPULATION DEFINITION:
--   - Completed: event observed (end_date = completion_date)
--   - Active: right-censored (end_date = extraction_date, event = 0)
--   - Stopped: EXCLUDED from time-to-event analysis
--     (completion_date ≠ stop_date; we don't know when they actually stopped)
--
-- SURVIVAL ANALYSIS SETUP:
--   - Time: duration_days (start → end)
--   - Event: event_completed (1 = completed, 0 = censored/active)
--   - Covariates: phase, therapeutic area, sponsor, enrollment size, etc.
--
-- WHAT WE CAN ANSWER:
--   1. Median time-to-completion by phase/condition (Kaplan-Meier)
--   2. Which factors are associated with longer duration (Cox PH)
--   3. Which trials are "slower than expected" (residual analysis)
--
-- WHAT WE CANNOT ANSWER:
--   - Time-to-failure for stopped trials (no reliable stop_date)
--   - Competing risks analysis (would need stop_date)
--
-- ============================================================

WITH 
-- Sponsor features (lead sponsor only)
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

-- Condition features (count, primary condition, therapeutic flags)
condition_features AS (
    SELECT
        c.study_id,
        COUNT(DISTINCT LOWER(TRIM(c.condition_name))) AS n_conditions,
        -- Primary condition (first alphabetically as proxy - imperfect but consistent)
        MIN(LOWER(TRIM(c.condition_name))) AS primary_condition,
        -- Therapeutic area flags
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
        END) AS is_oncology,
        MAX(CASE 
            WHEN LOWER(TRIM(c.condition_name)) LIKE '%diabetes%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%diabetic%'
            THEN 1 ELSE 0 
        END) AS is_diabetes,
        MAX(CASE 
            WHEN LOWER(TRIM(c.condition_name)) LIKE '%heart%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%cardiac%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%cardiovascular%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%coronary%'
            THEN 1 ELSE 0 
        END) AS is_cardiovascular,
        MAX(CASE 
            WHEN LOWER(TRIM(c.condition_name)) LIKE '%alzheimer%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%parkinson%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%dementia%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%neurodegenerat%'
            THEN 1 ELSE 0 
        END) AS is_neurological,
        MAX(CASE 
            WHEN LOWER(TRIM(c.condition_name)) LIKE '%depression%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%anxiety%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%schizophren%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%bipolar%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%psychiatric%'
            THEN 1 ELSE 0 
        END) AS is_psychiatric,
        MAX(CASE 
            WHEN LOWER(TRIM(c.condition_name)) LIKE '%hiv%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%aids%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%hepatitis%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%covid%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%influenza%'
              OR LOWER(TRIM(c.condition_name)) LIKE '%infection%'
            THEN 1 ELSE 0 
        END) AS is_infectious,
        MAX(CASE 
            WHEN LOWER(TRIM(c.condition_name)) LIKE '%healthy%'
            THEN 1 ELSE 0 
        END) AS is_healthy_volunteers
    FROM conditions c
    GROUP BY c.study_id
),

-- Geographic features (site count, multinational flag)
geography AS (
    SELECT
        l.study_id,
        COUNT(DISTINCT l.location_id) AS n_sites,
        COUNT(DISTINCT l.country) AS n_countries,
        CASE WHEN COUNT(DISTINCT l.country) > 1 THEN 1 ELSE 0 END AS is_multinational,
        CASE WHEN COUNT(DISTINCT l.location_id) = 1 THEN 1 ELSE 0 END AS is_single_site
    FROM locations l
    WHERE l.country IS NOT NULL AND l.country != ''
    GROUP BY l.study_id
),

-- Study design features
design_features AS (
    SELECT
        study_id,
        allocation,
        intervention_model,
        masking,
        primary_purpose,
        -- Randomization flag
        CASE WHEN UPPER(allocation) = 'RANDOMIZED' THEN 1 ELSE 0 END AS is_randomized,
        -- Blinding flags
        CASE 
            WHEN UPPER(masking) LIKE '%DOUBLE%' OR UPPER(masking) LIKE '%TRIPLE%' OR UPPER(masking) LIKE '%QUADRUPLE%' 
            THEN 1 ELSE 0 
        END AS is_blinded
    FROM study_design
)

SELECT
    -- ============================================================
    -- IDENTIFICATION
    -- ============================================================
    s.study_id,
    s.nct_id,
    
    -- ============================================================
    -- STATUS & OUTCOME
    -- ============================================================
    s.status AS status_raw,
    
    -- Status group
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN 'Completed'
        WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 'Stopped'
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 'Active'
        ELSE 'Other'
    END AS status_group,
    
    -- Binary indicators
    CASE WHEN UPPER(s.status) = 'COMPLETED' THEN 1 ELSE 0 END AS is_completed,
    CASE WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 1 ELSE 0 END AS is_stopped,
    CASE WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                   'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 1 ELSE 0 END AS is_active,
    
    -- ============================================================
    -- PHASE (key covariate for duration)
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
    
    -- ============================================================
    -- STUDY TYPE
    -- ============================================================
    s.study_type,
    CASE WHEN UPPER(s.study_type) = 'INTERVENTIONAL' THEN 1 ELSE 0 END AS is_interventional,
    
    -- ============================================================
    -- ENROLLMENT
    -- ============================================================
    s.enrollment,
    s.enrollment_type,
    CASE WHEN s.enrollment IS NOT NULL AND s.enrollment > 0 THEN 1 ELSE 0 END AS has_enrollment,
    
    -- Log enrollment (for modeling - add 1 to handle zeros)
    CASE 
        WHEN s.enrollment IS NOT NULL AND s.enrollment > 0 
        THEN LOG(s.enrollment + 1) / LOG(10)  -- log10
        ELSE NULL 
    END AS log_enrollment,
    
    -- Enrollment buckets
    CASE
        WHEN s.enrollment IS NULL OR s.enrollment = 0 THEN 'Unknown'
        WHEN s.enrollment < 50 THEN '<50'
        WHEN s.enrollment < 100 THEN '50-99'
        WHEN s.enrollment < 500 THEN '100-499'
        WHEN s.enrollment < 1000 THEN '500-999'
        ELSE '1000+'
    END AS enrollment_bucket,
    
    -- ============================================================
    -- SPONSOR FEATURES
    -- ============================================================
    ls.lead_agency,
    ls.lead_agency_class,
    COALESCE(ls.is_industry_sponsor, 0) AS is_industry_sponsor,
    
    -- ============================================================
    -- THERAPEUTIC AREA / CONDITIONS
    -- ============================================================
    COALESCE(cf.n_conditions, 0) AS n_conditions,
    cf.primary_condition,
    COALESCE(cf.is_oncology, 0) AS is_oncology,
    COALESCE(cf.is_diabetes, 0) AS is_diabetes,
    COALESCE(cf.is_cardiovascular, 0) AS is_cardiovascular,
    COALESCE(cf.is_neurological, 0) AS is_neurological,
    COALESCE(cf.is_psychiatric, 0) AS is_psychiatric,
    COALESCE(cf.is_infectious, 0) AS is_infectious,
    COALESCE(cf.is_healthy_volunteers, 0) AS is_healthy_volunteers,
    
    -- Derived therapeutic area (single label, priority order)
    CASE
        WHEN COALESCE(cf.is_oncology, 0) = 1 THEN 'Oncology'
        WHEN COALESCE(cf.is_cardiovascular, 0) = 1 THEN 'Cardiovascular'
        WHEN COALESCE(cf.is_diabetes, 0) = 1 THEN 'Metabolic'
        WHEN COALESCE(cf.is_neurological, 0) = 1 THEN 'Neurology'
        WHEN COALESCE(cf.is_psychiatric, 0) = 1 THEN 'Psychiatry'
        WHEN COALESCE(cf.is_infectious, 0) = 1 THEN 'Infectious Disease'
        WHEN COALESCE(cf.is_healthy_volunteers, 0) = 1 THEN 'Healthy Volunteers'
        ELSE 'Other'
    END AS therapeutic_area,
    
    -- ============================================================
    -- GEOGRAPHIC / OPERATIONAL FEATURES
    -- ============================================================
    COALESCE(geo.n_sites, 0) AS n_sites,
    COALESCE(geo.n_countries, 0) AS n_countries,
    COALESCE(geo.is_multinational, 0) AS is_multinational,
    COALESCE(geo.is_single_site, 0) AS is_single_site,
    CASE WHEN COALESCE(geo.n_sites, 0) > 0 THEN 1 ELSE 0 END AS has_location_data,
    
    -- Log sites (for modeling)
    CASE 
        WHEN geo.n_sites IS NOT NULL AND geo.n_sites > 0 
        THEN LOG(geo.n_sites + 1) / LOG(10)
        ELSE NULL 
    END AS log_sites,
    
    -- ============================================================
    -- DESIGN FEATURES
    -- ============================================================
    df.allocation,
    df.intervention_model,
    df.masking,
    df.primary_purpose,
    COALESCE(df.is_randomized, 0) AS is_randomized,
    COALESCE(df.is_blinded, 0) AS is_blinded,
    
    -- ============================================================
    -- TIME FEATURES (critical for duration analysis)
    -- ============================================================
    s.start_date,
    v.start_year,
    s.completion_date,
    s.primary_completion_date,
    
    -- Extraction date (for censoring calculation)
    date(:extraction_date) AS extraction_date,
    
    -- Start cohort
    CASE
        WHEN v.start_year BETWEEN 1990 AND 1999 THEN '1990-1999'
        WHEN v.start_year BETWEEN 2000 AND 2009 THEN '2000-2009'
        WHEN v.start_year BETWEEN 2010 AND 2019 THEN '2010-2019'
        WHEN v.start_year >= 2020 THEN '2020+'
        ELSE 'Other'
    END AS start_cohort,
    
    -- ============================================================
    -- DURATION CALCULATION
    -- ============================================================
    -- End date:
    --   Completed → completion_date (or primary_completion_date)
    --   Active → extraction_date (censoring date)
    --   Stopped → NULL (we don't know when they stopped)
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' 
        THEN COALESCE(s.completion_date, s.primary_completion_date)
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') 
        THEN date(:extraction_date)
        ELSE NULL
    END AS end_date,
    
    -- Duration in days (start → end)
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' 
             AND s.start_date IS NOT NULL 
             AND COALESCE(s.completion_date, s.primary_completion_date) IS NOT NULL
        THEN julianday(COALESCE(s.completion_date, s.primary_completion_date)) - julianday(s.start_date)
        
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION')
             AND s.start_date IS NOT NULL
        THEN julianday(date(:extraction_date)) - julianday(s.start_date)
        
        ELSE NULL  -- Stopped: no reliable end_date
    END AS duration_days,
    
    -- Duration in years (for interpretability)
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' 
             AND s.start_date IS NOT NULL 
             AND COALESCE(s.completion_date, s.primary_completion_date) IS NOT NULL
        THEN (julianday(COALESCE(s.completion_date, s.primary_completion_date)) - julianday(s.start_date)) / 365.25
        
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION')
             AND s.start_date IS NOT NULL
        THEN (julianday(date(:extraction_date)) - julianday(s.start_date)) / 365.25
        
        ELSE NULL
    END AS duration_years,
    
    -- ============================================================
    -- SURVIVAL ANALYSIS INDICATORS
    -- ============================================================
    -- Event indicator: 1 = completed (event observed), 0 = active (censored)
    -- NULL = stopped (excluded from survival analysis)
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN 1
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 0
        ELSE NULL  -- Stopped excluded
    END AS event_completed,
    
    -- Indicator for "valid for survival analysis" (has duration_days and event indicator)
    CASE
        WHEN UPPER(s.status) IN ('COMPLETED', 'RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION')
             AND s.start_date IS NOT NULL
             AND (
                 (UPPER(s.status) = 'COMPLETED' AND COALESCE(s.completion_date, s.primary_completion_date) IS NOT NULL)
                 OR UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                         'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION')
             )
        THEN 1
        ELSE 0
    END AS is_valid_for_survival
    
FROM v_studies_clean v
JOIN studies s ON v.study_id = s.study_id
LEFT JOIN lead_sponsor ls ON s.study_id = ls.study_id
LEFT JOIN condition_features cf ON s.study_id = cf.study_id
LEFT JOIN geography geo ON s.study_id = geo.study_id
LEFT JOIN design_features df ON s.study_id = df.study_id

WHERE 
    -- Scope: valid start year in analysis range
    v.is_start_year_in_scope = 1
    AND s.start_date IS NOT NULL
    -- Include all status types (we filter in notebook based on analysis)
    AND UPPER(s.status) IN (
        'COMPLETED', 
        'TERMINATED', 'WITHDRAWN', 'SUSPENDED',
        'RECRUITING', 'NOT_YET_RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION'
    )

ORDER BY s.study_id;
