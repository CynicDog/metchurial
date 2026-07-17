-- [query-identity stress corpus: CORE_B]
-- Same tables/joins/predicates as 34_query_identity_core_b_base.sql,
-- correlation names renamed (E/DP/P -> X/Y/Z) and SELECT-list order
-- shuffled. Must land on CORE_B's core signature, mirroring 21 vs. 20.
SELECT
    Z.POS_NM,
    X.EMP_ID,
    X.EMP_NM,
    Y.DEPT_NM,
    CASE
        WHEN Z.POS_GRD >= 5 THEN X.BASE_SAL * 1.20
        WHEN Z.POS_GRD >= 3 THEN X.BASE_SAL * 1.10
        ELSE X.BASE_SAL
    END AS ADJ_SAL
FROM TBEMP X
INNER JOIN TBDEPT Y
    ON X.DEPT_CD = Y.DEPT_CD
LEFT OUTER JOIN TBPOS Z
    ON X.POS_CD = Z.POS_CD
WHERE X.EMP_STAT_CD = 'A'
  AND Y.DEPT_TYPE_CD IN ('HQ', 'BR')
  AND X.HIRE_DT BETWEEN '20100101' AND '20261231';
