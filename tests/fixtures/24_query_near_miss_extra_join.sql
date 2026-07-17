-- [query-identity stress corpus: NEAR_MISS of CORE_A]
-- Same base as 20_query_identity_base.sql plus one additional JOIN
-- (TBCODE E) that nothing else in the query depends on. This changes the
-- join graph, so it must NOT land on CORE_A's core signature -- but it
-- should score highly similar to it (same base tables, same predicates,
-- one added edge), not be treated as unrelated.
SELECT
    A.ACCT_ID,
    B.CTRT_NO,
    C.STAT_CD,
    D.TBSAMPLE001,
    E.CODE_NM,
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
LEFT OUTER JOIN TBCODE E
    ON B.CTRT_TYPE_CD = E.CODE_CD
WHERE C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'
GROUP BY A.ACCT_ID, B.CTRT_NO, C.STAT_CD, D.TBSAMPLE001, E.CODE_NM, B.CTRT_TYPE_CD, B.BASE_AMT;
