-- [query-identity stress corpus: CORE_A]
-- Base query for the CORE_A cluster (see issue: SQL query identification /
-- similarity scoring). 21/22/23 must resolve to the same core signature as
-- this file -- same tables, same join graph, same predicates -- differing
-- only in things a core signature must deliberately ignore (aliasing,
-- SELECT-list column count, how a derived column is calculated).
SELECT
    A.ACCT_ID,
    B.CTRT_NO,
    C.STAT_CD,
    D.TBSAMPLE001,
    CASE
        WHEN B.CTRT_TYPE_CD = '01' THEN B.BASE_AMT * 1.05
        WHEN B.CTRT_TYPE_CD = '02' THEN B.BASE_AMT * 1.10
        ELSE B.BASE_AMT
    END AS ADJ_AMT
FROM TBACCT A
INNER JOIN TBCTRT B
    ON A.ACCT_ID = B.ACCT_ID
LEFT OUTER JOIN TBSTAT C
    ON B.CTRT_NO = C.CTRT_NO
JOIN TBSAMPLE001 D
    ON A.ACCT_ID = D.ACCT_ID
WHERE C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'
GROUP BY A.ACCT_ID, B.CTRT_NO, C.STAT_CD, D.TBSAMPLE001, B.CTRT_TYPE_CD, B.BASE_AMT;
