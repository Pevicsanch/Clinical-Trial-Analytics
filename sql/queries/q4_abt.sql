-- q4_abt.sql
-- Analytical Base Table for Q4: Geographic Distribution & Specialization
-- One row per study with geographic features aggregated from locations table.
-- Scope: studies in v_studies_clean with is_start_year_in_scope = 1.
--
-- Note: This ABT is study-level. For country-level or condition-level analysis,
-- use q4_country_condition.sql which provides the many-to-many joins needed
-- for specialization analysis.

WITH 
-- Geographic features per study (aggregated from locations)
study_geography AS (
    SELECT
        l.study_id,
        COUNT(DISTINCT l.location_id) AS n_sites,
        COUNT(DISTINCT l.country) AS n_countries,
        COUNT(DISTINCT l.city) AS n_cities,
        -- Primary country (mode - country with most sites)
        (
            SELECT l2.country 
            FROM locations l2 
            WHERE l2.study_id = l.study_id 
              AND l2.country IS NOT NULL AND l2.country != ''
            GROUP BY l2.country 
            ORDER BY COUNT(*) DESC 
            LIMIT 1
        ) AS primary_country,
        -- Flags
        CASE WHEN COUNT(DISTINCT l.country) > 1 THEN 1 ELSE 0 END AS is_multinational,
        CASE WHEN COUNT(DISTINCT l.location_id) = 1 THEN 1 ELSE 0 END AS is_single_site,
        CASE WHEN COUNT(DISTINCT l.location_id) >= 10 THEN 1 ELSE 0 END AS is_large_multisite,
        -- US presence
        MAX(CASE WHEN l.country = 'United States' THEN 1 ELSE 0 END) AS has_us_site,
        -- Country list (for reference, comma-separated)
        GROUP_CONCAT(DISTINCT l.country) AS countries_list
    FROM locations l
    WHERE l.country IS NOT NULL AND l.country != ''
    GROUP BY l.study_id
),

-- Sponsor features
lead_sponsor AS (
    SELECT
        study_id,
        MAX(agency_class) AS lead_agency_class,
        MAX(CASE WHEN UPPER(agency_class) = 'INDUSTRY' THEN 1 ELSE 0 END) AS is_industry_sponsor
    FROM sponsors
    WHERE UPPER(lead_or_collaborator) = 'LEAD'
    GROUP BY study_id
),

-- Condition count per study
condition_counts AS (
    SELECT
        study_id,
        COUNT(DISTINCT LOWER(TRIM(condition_name))) AS n_conditions
    FROM conditions
    WHERE condition_name IS NOT NULL AND TRIM(condition_name) != ''
    GROUP BY study_id
)

SELECT
    -- ============================================================
    -- IDENTIFICATION
    -- ============================================================
    s.study_id,
    s.nct_id,
    
    -- ============================================================
    -- TEMPORAL
    -- ============================================================
    s.start_year,
    CASE
        WHEN s.start_year BETWEEN 1990 AND 1999 THEN '1990-1999'
        WHEN s.start_year BETWEEN 2000 AND 2009 THEN '2000-2009'
        WHEN s.start_year BETWEEN 2010 AND 2019 THEN '2010-2019'
        WHEN s.start_year >= 2020 THEN '2020+'
        ELSE 'Other'
    END AS start_cohort,
    
    -- ============================================================
    -- STUDY CHARACTERISTICS
    -- ============================================================
    s.study_type,
    CASE WHEN UPPER(s.study_type) = 'INTERVENTIONAL' THEN 1 ELSE 0 END AS is_interventional,
    
    -- Phase (standardized)
    CASE
        WHEN s.phase IS NULL OR s.phase = '' OR s.phase = 'NA' THEN 'Not Applicable'
        WHEN s.phase LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
        WHEN s.phase = 'PHASE1' THEN 'Phase 1'
        WHEN s.phase = 'PHASE2' THEN 'Phase 2'
        WHEN s.phase = 'PHASE3' THEN 'Phase 3'
        WHEN s.phase = 'PHASE4' THEN 'Phase 4'
        WHEN s.phase LIKE '%PHASE1%' AND s.phase LIKE '%PHASE2%' THEN 'Phase 1/2'
        WHEN s.phase LIKE '%PHASE2%' AND s.phase LIKE '%PHASE3%' THEN 'Phase 2/3'
        ELSE 'Other'
    END AS phase_group,
    
    -- Status
    s.status,
    CASE
        WHEN UPPER(s.status) = 'COMPLETED' THEN 'Completed'
        WHEN UPPER(s.status) IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 'Stopped'
        WHEN UPPER(s.status) IN ('RECRUITING', 'NOT_YET_RECRUITING', 
                                  'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 'Active'
        ELSE 'Other'
    END AS outcome_group,
    
    -- Enrollment
    s.enrollment,
    CASE WHEN s.enrollment IS NOT NULL AND s.enrollment > 0 THEN 1 ELSE 0 END AS has_enrollment,
    
    -- ============================================================
    -- GEOGRAPHIC FEATURES (from study_geography CTE)
    -- ============================================================
    COALESCE(g.n_sites, 0) AS n_sites,
    COALESCE(g.n_countries, 0) AS n_countries,
    COALESCE(g.n_cities, 0) AS n_cities,
    g.primary_country,
    COALESCE(g.is_multinational, 0) AS is_multinational,
    COALESCE(g.is_single_site, 0) AS is_single_site,
    COALESCE(g.is_large_multisite, 0) AS is_large_multisite,
    COALESCE(g.has_us_site, 0) AS has_us_site,
    g.countries_list,
    
    -- Has location data flag
    CASE WHEN g.study_id IS NOT NULL THEN 1 ELSE 0 END AS has_location_data,
    
    -- ============================================================
    -- SPONSOR FEATURES
    -- ============================================================
    sp.lead_agency_class,
    COALESCE(sp.is_industry_sponsor, 0) AS is_industry_sponsor,
    
    -- ============================================================
    -- CONDITION FEATURES
    -- ============================================================
    COALESCE(cc.n_conditions, 0) AS n_conditions

FROM v_studies_clean s
LEFT JOIN study_geography g ON s.study_id = g.study_id
LEFT JOIN lead_sponsor sp ON s.study_id = sp.study_id
LEFT JOIN condition_counts cc ON s.study_id = cc.study_id

WHERE s.is_start_year_in_scope = 1

ORDER BY s.study_id;
