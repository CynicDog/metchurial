-- [query-identity stress corpus: CORE_B]
-- Identical to 34_query_identity_core_b_base.sql plus one extra
-- SELECT-list column (DP.DEPT_TYPE_CD, projected directly). Tables/joins/
-- predicates untouched -- must land on CORE_B's core signature, mirroring
-- 22 vs. 20.
SELECT
    E.EMP_ID,
    E.EMP_NM,
    DP.DEPT_NM,
    DP.DEPT_TYPE_CD,
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
  AND E.HIRE_DT BETWEEN '20100101' AND '20261231';
