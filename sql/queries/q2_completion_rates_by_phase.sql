-- Business Question: 2. Completion Analysis
-- Purpose: Calculate completion rates by phase to assess pipeline efficiency.
-- This reveals which phases have higher attrition and whether early-stage trials
-- successfully advance to completion or face higher termination rates.

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
    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) AS completed,
    COUNT(CASE WHEN status = 'TERMINATED' THEN 1 END) AS terminated,
    COUNT(CASE WHEN status = 'WITHDRAWN' THEN 1 END) AS withdrawn,
    COUNT(CASE WHEN status = 'SUSPENDED' THEN 1 END) AS suspended,
    COUNT(CASE WHEN status IN ('RECRUITING', 'NOT_YET_RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION') THEN 1 END) AS active,
    ROUND(COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) * 100.0 / COUNT(*), 1) AS completion_rate,
    ROUND(COUNT(CASE WHEN status = 'TERMINATED' THEN 1 END) * 100.0 / COUNT(*), 1) AS termination_rate,
    ROUND(COUNT(CASE WHEN status = 'WITHDRAWN' THEN 1 END) * 100.0 / COUNT(*), 1) AS withdrawal_rate
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
