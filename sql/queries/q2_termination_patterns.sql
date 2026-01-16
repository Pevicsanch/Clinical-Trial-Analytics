-- Business Question: 2. Completion Analysis
-- Purpose: Analyze termination and withdrawal patterns across phases and time.
-- This identifies whether certain phases or periods show higher failure rates,
-- helping to understand operational risks and decision points.

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
    CASE
        WHEN status IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN status
        ELSE 'Other'
    END AS failure_type,
    COUNT(*) AS trial_count,
    ROUND(AVG(CASE
        WHEN enrollment IS NOT NULL AND enrollment > 0 THEN enrollment
        ELSE NULL
    END), 0) AS avg_enrollment_at_stop
FROM studies
WHERE status IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED', 'COMPLETED', 'ACTIVE_NOT_RECRUITING')
GROUP BY phase_group, failure_type
HAVING trial_count >= 5
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
    END,
    trial_count DESC;
