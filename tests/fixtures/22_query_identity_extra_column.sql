-- [query-identity stress corpus: CORE_A]
-- Identical to 20_query_identity_base.sql except for one extra SELECT-list
-- column (B.CTRT_TYPE_CD, projected directly). Tables/joins/predicates are
-- untouched -- a core signature built from the FROM/JOIN/WHERE skeleton
-- alone must still land on the same core signature as 20, since it never
-- looks at the SELECT list at all.
SELECT
    A.ACCT_ID,
    B.CTRT_NO,
    B.CTRT_TYPE_CD,
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
GROUP BY A.ACCT_ID, B.CTRT_NO, B.CTRT_TYPE_CD, C.STAT_CD, D.TBSAMPLE001, B.BASE_AMT;
