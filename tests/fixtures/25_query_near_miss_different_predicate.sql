-- [query-identity stress corpus: NEAR_MISS of CORE_A]
-- Same tables/joins as 20_query_identity_base.sql, but the WHERE clause's
-- predicate set genuinely differs: STAT_CD narrowed to a single value
-- instead of an IN-list, and the OPEN_DT range condition dropped entirely
-- in favor of a new condition on a column the base query never
-- references. Must NOT land on CORE_A's core signature (predicate set
-- differs) but should still score similar (same tables, same join graph).
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
WHERE C.STAT_CD = '01'
  AND A.CHANNEL_CD = 'WEB'
GROUP BY A.ACCT_ID, B.CTRT_NO, C.STAT_CD, D.TBSAMPLE001, B.CTRT_TYPE_CD, B.BASE_AMT;
