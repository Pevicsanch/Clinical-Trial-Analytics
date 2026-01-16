-- Business Question: 4. Geographic Insights
-- Purpose: Analyze how many sites trials use across different phases.
-- This reveals operational complexity and geographic distribution patterns,
-- showing whether larger trials spread across more locations.

WITH site_counts AS (
    SELECT
        s.study_id,
        s.phase,
        s.status,
        s.enrollment,
        COUNT(DISTINCT l.facility || '|' || l.city || '|' || l.country) AS site_count,
        COUNT(DISTINCT l.country) AS country_count
    FROM studies s
    LEFT JOIN locations l ON s.study_id = l.study_id
    WHERE l.facility IS NOT NULL AND l.facility != ''
    GROUP BY s.study_id, s.phase, s.status, s.enrollment
)
SELECT
    CASE
        WHEN phase IS NULL OR phase = '' THEN 'Not Applicable'
        WHEN phase = 'NA' THEN 'Not Applicable'
        WHEN phase LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
        WHEN phase = 'PHASE1' THEN 'Phase 1'
        WHEN phase = 'PHASE2' THEN 'Phase 2'
        WHEN phase = 'PHASE3' THEN 'Phase 3'
        WHEN phase = 'PHASE4' THEN 'Phase 4'
        WHEN phase LIKE '%PHASE1%' AND phase LIKE '%PHASE2%' THEN 'Phase 1/2'
        WHEN phase LIKE '%PHASE2%' AND phase LIKE '%PHASE3%' THEN 'Phase 2/3'
        ELSE 'Other'
    END AS phase_group,
    COUNT(*) AS trials_with_sites,
    ROUND(AVG(site_count), 1) AS avg_sites_per_trial,
    ROUND(AVG(country_count), 1) AS avg_countries_per_trial,
    MAX(site_count) AS max_sites,
    COUNT(CASE WHEN site_count = 1 THEN 1 END) AS single_site_trials,
    COUNT(CASE WHEN site_count >= 10 THEN 1 END) AS multisite_10plus,
    COUNT(CASE WHEN country_count >= 5 THEN 1 END) AS multinational_5plus
FROM site_counts
GROUP BY phase_group
HAVING trials_with_sites >= 10
ORDER BY
    CASE phase_group
        WHEN 'Early Phase 1' THEN 1
        WHEN 'Phase 1' THEN 2
        WHEN 'Phase 1/2' THEN 3
        WHEN 'Phase 2' THEN 4
        WHEN 'Phase 2/3' THEN 5
        WHEN 'Phase 3' THEN 6
        WHEN 'Phase 4' THEN 7
        WHEN 'Not Applicable' THEN 8
        ELSE 9
    END;
