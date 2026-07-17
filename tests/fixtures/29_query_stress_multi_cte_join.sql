-- [query-identity stress corpus: STRESS, deep CTE + join nesting]
-- Four CTEs, each its own multi-table ANSI JOIN with its own predicates,
-- consumed by an outer query that joins the CTEs together. Exercises
-- join-graph/predicate extraction across nested query-block scopes at
-- once -- each CTE is its own scope with its own alias map, and the outer
-- query's join graph is built from CTE names, not base tables directly.
-- Also a regression stress case for the CTE-body grammar fix (issue #4):
-- before that fix, none of these four CTE bodies had any parse path into
-- the tree at all, let alone as part of one larger statement.
WITH ACTIVE_ACCT AS (
    SELECT
        A.ACCT_ID,
        A.BR_CD,
        A.CHANNEL_CD,
        A.OPEN_DT
    FROM TBACCT A
    INNER JOIN TBSTAT S
        ON A.ACCT_ID = S.ACCT_ID
    WHERE S.STAT_CD = '01'
      AND A.OPEN_DT >= '20200101'
),
ACTIVE_CTRT AS (
    SELECT
        B.ACCT_ID,
        B.CTRT_NO,
        B.CTRT_TYPE_CD,
        B.BASE_AMT,
        G.PROD_NM,
        G.PROD_RISK_CD
    FROM TBCTRT B
    LEFT OUTER JOIN TBPROD G
        ON B.PROD_CD = G.PROD_CD
    WHERE B.CTRT_TYPE_CD <> '99'
),
BRANCH_INFO AS (
    SELECT
        F.BR_CD,
        F.BR_NM,
        H.EMP_NM AS MGR_NM
    FROM TBBRANCH F
    LEFT OUTER JOIN TBEMP H
        ON F.MGR_EMP_ID = H.EMP_ID
    WHERE F.BR_STAT_CD = 'A'
),
CODE_LOOKUP AS (
    SELECT
        E.CODE_CD,
        E.CODE_NM
    FROM TBCODE E
    WHERE E.CODE_GRP_CD = 'CTRT_TYPE'
)
SELECT
    AA.ACCT_ID,
    AC.CTRT_NO,
    AC.PROD_NM,
    BI.BR_NM,
    BI.MGR_NM,
    CL.CODE_NM,
    CASE
        WHEN AC.CTRT_TYPE_CD = '01' THEN AC.BASE_AMT * 1.05
        WHEN AC.CTRT_TYPE_CD = '02' THEN AC.BASE_AMT * 1.10
        ELSE AC.BASE_AMT
    END AS ADJ_AMT
FROM ACTIVE_ACCT AA
INNER JOIN ACTIVE_CTRT AC
    ON AA.ACCT_ID = AC.ACCT_ID
LEFT OUTER JOIN BRANCH_INFO BI
    ON AA.BR_CD = BI.BR_CD
LEFT OUTER JOIN CODE_LOOKUP CL
    ON AC.CTRT_TYPE_CD = CL.CODE_CD
WHERE AC.PROD_RISK_CD IN ('L', 'M', 'H')
ORDER BY AA.ACCT_ID, AC.CTRT_NO;
