-- [query-identity stress corpus: HARD CASE, documented open question]
-- Two UNION ALL branches, each its own query block with its own FROM/
-- JOIN/WHERE: the first branch is exactly CORE_B's join graph and
-- predicates; the second branch adds TBCODE and a different filter.
-- Whether a UNION'd statement gets one combined signature (per-branch
-- signatures merged somehow) or is treated as N independent signatures
-- (one per branch, so this file would contribute both a CORE_B match *and*
-- a new, unrelated one) is a genuinely open design question -- table_scan.
-- scan_query_blocks already discovers UNION siblings as separate
-- QueryBlocks (see its docstring), so the raw material exists either way.
-- Not asserting a specific expected answer here on purpose; flagging it
-- as a case the implementation needs to make a deliberate choice about,
-- not stumble into by accident.
SELECT
    E.EMP_ID,
    E.EMP_NM,
    DP.DEPT_NM,
    PS.POS_NM,
    CASE
        WHEN PS.POS_GRD >= 5 THEN E.BASE_SAL * 1.20
        WHEN PS.POS_GRD >= 3 THEN E.BASE_SAL * 1.10
        ELSE E.BASE_SAL
    END AS ADJ_SAL
FROM TBEMP E
INNER JOIN TBDEPT DP
    ON E.DEPT_CD = DP.DEPT_CD
LEFT OUTER JOIN TBPOS PS
    ON E.POS_CD = PS.POS_CD
WHERE E.EMP_STAT_CD = 'A'
  AND DP.DEPT_TYPE_CD IN ('HQ', 'BR')
  AND E.HIRE_DT BETWEEN '20100101' AND '20261231'

UNION ALL

SELECT
    E.EMP_ID,
    E.EMP_NM,
    DP.DEPT_NM,
    PS.POS_NM,
    CASE
        WHEN PS.POS_GRD >= 5 THEN E.BASE_SAL * 1.20
        WHEN PS.POS_GRD >= 3 THEN E.BASE_SAL * 1.10
        ELSE E.BASE_SAL
    END AS ADJ_SAL
FROM TBEMP E
INNER JOIN TBDEPT DP
    ON E.DEPT_CD = DP.DEPT_CD
LEFT OUTER JOIN TBPOS PS
    ON E.POS_CD = PS.POS_CD
INNER JOIN TBCODE CD
    ON DP.DEPT_TYPE_CD = CD.CODE_CD
WHERE E.EMP_STAT_CD = 'I'
  AND CD.CODE_GRP_CD = 'DEPT_TYPE';
