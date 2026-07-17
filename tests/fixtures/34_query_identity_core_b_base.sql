-- [query-identity stress corpus: CORE_B]
-- A second, fully independent cluster (HR/employee domain, shares zero
-- tables with CORE_A) -- proves the future algorithm distinguishes
-- multiple genuine clusters within one scan, not just "matches 20 or
-- doesn't". 35/36/37 are variants of this file the same way 21/22/23 are
-- variants of 20.
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
  AND E.HIRE_DT BETWEEN '20100101' AND '20261231';
