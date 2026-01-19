-- Business Question: 2. Completion Analysis
-- Purpose: Measure time-to-completion for trials that successfully finished.
-- This reveals how long different phases take to complete and whether
-- completion timelines vary across the development pipeline.

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
    COUNT(*) AS completed_trials,
    ROUND(AVG(JULIANDAY(completion_date) - JULIANDAY(start_date)) / 365.25, 1) AS avg_years_to_complete,
    ROUND(MIN(JULIANDAY(completion_date) - JULIANDAY(start_date)) / 365.25, 1) AS min_years,
    ROUND(MAX(JULIANDAY(completion_date) - JULIANDAY(start_date)) / 365.25, 1) AS max_years,
    ROUND(
        (SELECT AVG(JULIANDAY(completion_date) - JULIANDAY(start_date)) / 365.25
         FROM studies s2
         WHERE s2.status = 'COMPLETED'
           AND s2.start_date IS NOT NULL
           AND s2.completion_date IS NOT NULL
           AND s2.start_date != ''
           AND s2.completion_date != ''
           AND JULIANDAY(s2.completion_date) > JULIANDAY(s2.start_date)
           AND (CASE
                   WHEN s2.phase IS NULL OR s2.phase = '' THEN 'Not Applicable'
                   WHEN s2.phase = 'NA' THEN 'Not Applicable'
                   WHEN s2.phase LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
                   WHEN s2.phase = 'PHASE1' THEN 'Phase 1'
                   WHEN s2.phase = 'PHASE2' THEN 'Phase 2'
                   WHEN s2.phase = 'PHASE3' THEN 'Phase 3'
                   WHEN s2.phase = 'PHASE4' THEN 'Phase 4'
                   WHEN s2.phase LIKE '%PHASE1%' AND s2.phase LIKE '%PHASE2%' THEN 'Phase 1/2'
                   WHEN s2.phase LIKE '%PHASE2%' AND s2.phase LIKE '%PHASE3%' THEN 'Phase 2/3'
                   ELSE 'Other'
               END) = (CASE
                   WHEN s1.phase IS NULL OR s1.phase = '' THEN 'Not Applicable'
                   WHEN s1.phase = 'NA' THEN 'Not Applicable'
                   WHEN s1.phase LIKE '%EARLY_PHASE%' THEN 'Early Phase 1'
                   WHEN s1.phase = 'PHASE1' THEN 'Phase 1'
                   WHEN s1.phase = 'PHASE2' THEN 'Phase 2'
                   WHEN s1.phase = 'PHASE3' THEN 'Phase 3'
                   WHEN s1.phase = 'PHASE4' THEN 'Phase 4'
                   WHEN s1.phase LIKE '%PHASE1%' AND s1.phase LIKE '%PHASE2%' THEN 'Phase 1/2'
                   WHEN s1.phase LIKE '%PHASE2%' AND s1.phase LIKE '%PHASE3%' THEN 'Phase 2/3'
                   ELSE 'Other'
               END)
           AND (JULIANDAY(s2.completion_date) - JULIANDAY(s2.start_date)) / 365.25 <=
               ((SELECT AVG(JULIANDAY(completion_date) - JULIANDAY(start_date)) / 365.25
                 FROM studies
                 WHERE status = 'COMPLETED'
                   AND start_date IS NOT NULL
                   AND completion_date IS NOT NULL
                   AND start_date != ''
                   AND completion_date != ''
                   AND JULIANDAY(completion_date) > JULIANDAY(start_date)) * 2)
        ), 1) AS median_estimate_years
FROM studies s1
WHERE
    status = 'COMPLETED'
    AND start_date IS NOT NULL
    AND completion_date IS NOT NULL
    AND start_date != ''
    AND completion_date != ''
    AND JULIANDAY(completion_date) > JULIANDAY(start_date)
GROUP BY phase_group
HAVING completed_trials >= 10
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
