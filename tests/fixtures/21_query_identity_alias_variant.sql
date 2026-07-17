-- [query-identity stress corpus: CORE_A]
-- Same tables/joins/predicates as 20_query_identity_base.sql -- every
-- correlation name renamed (A/B/C/D -> X/Y/Z/W), SELECT-list column order
-- shuffled. A core-signature algorithm must alias-normalize before hashing,
-- so this must land on the same core signature as 20.
SELECT
    Z.STAT_CD,
    X.ACCT_ID,
    W.TBSAMPLE001,
    Y.CTRT_NO,
    CASE
        WHEN Y.CTRT_TYPE_CD = '01' THEN Y.BASE_AMT * 1.05
        WHEN Y.CTRT_TYPE_CD = '02' THEN Y.BASE_AMT * 1.10
        ELSE Y.BASE_AMT
    END AS ADJ_AMT
FROM TBACCT X
INNER JOIN TBCTRT Y
    ON X.ACCT_ID = Y.ACCT_ID
LEFT OUTER JOIN TBSTAT Z
    ON Y.CTRT_NO = Z.CTRT_NO
JOIN TBSAMPLE001 W
    ON X.ACCT_ID = W.ACCT_ID
WHERE Z.STAT_CD IN ('01', '02')
  AND Y.CTRT_TYPE_CD <> '99'
  AND X.OPEN_DT BETWEEN '20200101' AND '20261231'
GROUP BY X.ACCT_ID, Y.CTRT_NO, Z.STAT_CD, W.TBSAMPLE001, Y.CTRT_TYPE_CD, Y.BASE_AMT;
