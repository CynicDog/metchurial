-- [query-identity stress corpus: CORE_A]
-- Same join graph and predicates as 20_query_identity_base.sql, but the
-- FROM-clause table order is permuted (D joined first, then B, then A's
-- second relationship to C established last) -- the join *graph* (which
-- tables connect to which, via which type) is identical to 20's, just
-- discovered in a different traversal order. A core signature must sort/
-- canonicalize the edge set before hashing, so this must still land on
-- CORE_A.
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
FROM TBSAMPLE001 D
INNER JOIN TBACCT A
    ON A.ACCT_ID = D.ACCT_ID
INNER JOIN TBCTRT B
    ON A.ACCT_ID = B.ACCT_ID
LEFT OUTER JOIN TBSTAT C
    ON B.CTRT_NO = C.CTRT_NO
WHERE C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'
GROUP BY A.ACCT_ID, B.CTRT_NO, C.STAT_CD, D.TBSAMPLE001, B.CTRT_TYPE_CD, B.BASE_AMT;
