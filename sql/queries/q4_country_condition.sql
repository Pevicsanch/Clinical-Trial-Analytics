-- q4_country_condition.sql
-- Country × Condition matrix for regional specialization analysis (Q4.2)
-- One row per unique (country, condition_standardized) combination.
--
-- Used to calculate Location Quotients and test for regional specialization.
-- Note: A single trial can appear multiple times if it has multiple countries
-- AND multiple conditions. This is intentional for specialization analysis.

WITH 
-- Study-country pairs (one row per country per study)
study_countries AS (
    SELECT DISTINCT
        l.study_id,
        l.country
    FROM locations l
    JOIN v_studies_clean s ON l.study_id = s.study_id
    WHERE l.country IS NOT NULL AND l.country != ''
      AND s.is_start_year_in_scope = 1
),

-- Study-condition pairs with standardized names
study_conditions AS (
    SELECT DISTINCT
        c.study_id,
        LOWER(TRIM(c.condition_name)) AS condition_standardized
    FROM conditions c
    JOIN v_studies_clean s ON c.study_id = s.study_id
    WHERE c.condition_name IS NOT NULL AND TRIM(c.condition_name) != ''
      AND s.is_start_year_in_scope = 1
),

-- Cross join: country × condition (for trials that have both)
country_condition_pairs AS (
    SELECT
        sc.country,
        scond.condition_standardized,
        sc.study_id
    FROM study_countries sc
    JOIN study_conditions scond ON sc.study_id = scond.study_id
),

-- Aggregate to country × condition counts
country_condition_counts AS (
    SELECT
        country,
        condition_standardized,
        COUNT(DISTINCT study_id) AS n_trials
    FROM country_condition_pairs
    GROUP BY country, condition_standardized
),

-- Country totals (across all conditions)
country_totals AS (
    SELECT
        country,
        COUNT(DISTINCT study_id) AS country_total_trials
    FROM study_countries
    GROUP BY country
),

-- Condition totals (across all countries)
condition_totals AS (
    SELECT
        condition_standardized,
        COUNT(DISTINCT study_id) AS condition_global_trials
    FROM study_conditions
    GROUP BY condition_standardized
),

-- Grand total (unique studies with both location and condition data)
grand_total AS (
    SELECT COUNT(DISTINCT sc.study_id) AS global_total
    FROM study_countries sc
    JOIN study_conditions scond ON sc.study_id = scond.study_id
)

SELECT
    ccc.country,
    ccc.condition_standardized,
    ccc.n_trials,
    ct.country_total_trials,
    cond.condition_global_trials,
    gt.global_total,
    
    -- Location Quotient (LQ)
    -- LQ = (n_trials / country_total) / (condition_global / global_total)
    -- LQ > 1 means country is relatively specialized in this condition
    ROUND(
        (CAST(ccc.n_trials AS REAL) / ct.country_total_trials) /
        (CAST(cond.condition_global_trials AS REAL) / gt.global_total),
        3
    ) AS location_quotient,
    
    -- Share of country's trials in this condition (%)
    ROUND(ccc.n_trials * 100.0 / ct.country_total_trials, 2) AS country_share_pct,
    
    -- Share of condition's global trials in this country (%)
    ROUND(ccc.n_trials * 100.0 / cond.condition_global_trials, 2) AS condition_in_country_pct

FROM country_condition_counts ccc
JOIN country_totals ct ON ccc.country = ct.country
JOIN condition_totals cond ON ccc.condition_standardized = cond.condition_standardized
CROSS JOIN grand_total gt

-- Filter to meaningful combinations (avoid noise)
WHERE ct.country_total_trials >= 50           -- Country has at least 50 trials
  AND cond.condition_global_trials >= 100     -- Condition has at least 100 trials globally
  AND ccc.n_trials >= 5                       -- At least 5 trials for this combination

ORDER BY ccc.country, ccc.n_trials DESC;
