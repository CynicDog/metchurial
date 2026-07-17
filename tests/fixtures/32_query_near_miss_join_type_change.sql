-- [query-identity stress corpus: NEAR_MISS of CORE_A]
-- Identical to 20_query_identity_base.sql except TBSTAT's join is
-- INNER instead of LEFT OUTER -- semantically different (rows with no
-- matching status are now dropped, not null-padded), so the join *type*
-- differs and this must NOT land on CORE_A's core signature. But it's the
-- smallest possible edit (one keyword) against an otherwise-identical
-- query, so it should score extremely high similarity -- the clearest
-- case for why join type has to be part of the signature's edge identity,
-- not just which two tables are connected.
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
INNER JOIN TBSTAT C
    ON B.CTRT_NO = C.CTRT_NO
JOIN TBSAMPLE001 D
    ON A.ACCT_ID = D.ACCT_ID
WHERE C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'
GROUP BY A.ACCT_ID, B.CTRT_NO, C.STAT_CD, D.TBSAMPLE001, B.CTRT_TYPE_CD, B.BASE_AMT;
