-- Business Question: 3. Enrollment Performance
-- Purpose: Analyze enrollment patterns across development phases.
-- This reveals which phases achieve higher enrollment and whether
-- enrollment scale aligns with phase-specific requirements.

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
    COUNT(*) AS total_trials,
    COUNT(CASE WHEN enrollment IS NOT NULL AND enrollment > 0 THEN 1 END) AS trials_with_enrollment,
    ROUND(AVG(CASE WHEN enrollment IS NOT NULL AND enrollment > 0 THEN enrollment END), 0) AS avg_enrollment,
    ROUND(MIN(CASE WHEN enrollment IS NOT NULL AND enrollment > 0 THEN enrollment END), 0) AS min_enrollment,
    ROUND(MAX(CASE WHEN enrollment IS NOT NULL AND enrollment > 0 THEN enrollment END), 0) AS max_enrollment,
    COUNT(CASE WHEN enrollment >= 100 THEN 1 END) AS trials_100plus,
    COUNT(CASE WHEN enrollment >= 500 THEN 1 END) AS trials_500plus,
    COUNT(CASE WHEN enrollment >= 1000 THEN 1 END) AS trials_1000plus
FROM studies
GROUP BY phase_group
HAVING total_trials >= 10
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
