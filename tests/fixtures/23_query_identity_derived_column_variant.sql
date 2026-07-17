-- [query-identity stress corpus: CORE_A]
-- Identical to 20_query_identity_base.sql except ADJ_AMT is calculated
-- differently (a flat +5% via multiplication by a literal, instead of the
-- tiered CASE expression) -- same tables/joins/predicates, so this must
-- still land on the same core signature as 20. This is the "someone
-- rewrote the derivative column's formula, nothing else changed" case.
SELECT
    A.ACCT_ID,
    B.CTRT_NO,
    C.STAT_CD,
    D.TBSAMPLE001,
    ROUND(B.BASE_AMT * 1.05, 2) AS ADJ_AMT
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
GROUP BY A.ACCT_ID, B.CTRT_NO, C.STAT_CD, D.TBSAMPLE001, B.BASE_AMT;
