-- [query-identity stress corpus: STRESS, wide join graph]
-- A 9-table ANSI JOIN chain (mixing INNER/LEFT OUTER/JOIN...USING), each
-- table contributing its own predicate -- exercises join-graph and
-- predicate-set extraction at a scale closer to a real enterprise
-- reporting query than the smaller CORE_A-family fixtures. Also a
-- regression stress case for the ANSI-JOIN grammar fix itself (issue #4):
-- a wide chain like this used to fall into the tiered driver's Tier-3
-- token-shredding safety valve for every JOIN past the first.
SELECT
    A.ACCT_ID,
    B.CTRT_NO,
    C.STAT_CD,
    D.TBSAMPLE001,
    E.CODE_NM,
    F.BR_NM,
    G.PROD_NM,
    H.EMP_NM,
    I.CHNL_NM,
    CASE
        WHEN B.CTRT_TYPE_CD = '01' THEN B.BASE_AMT * 1.05
        WHEN B.CTRT_TYPE_CD = '02' THEN B.BASE_AMT * 1.10
        WHEN B.CTRT_TYPE_CD = '03' THEN B.BASE_AMT * 1.15
        ELSE B.BASE_AMT
    END AS ADJ_AMT,
    CASE
        WHEN G.PROD_RISK_CD = 'H' THEN 'HIGH'
        WHEN G.PROD_RISK_CD = 'M' THEN 'MEDIUM'
        ELSE 'LOW'
    END AS RISK_LVL
FROM TBACCT A
INNER JOIN TBCTRT B
    ON A.ACCT_ID = B.ACCT_ID
LEFT OUTER JOIN TBSTAT C
    ON B.CTRT_NO = C.CTRT_NO
    AND C.STAT_CD <> '99'
JOIN TBSAMPLE001 D
    USING (ACCT_ID)
LEFT OUTER JOIN TBCODE E
    ON B.CTRT_TYPE_CD = E.CODE_CD
INNER JOIN TBBRANCH F
    ON A.BR_CD = F.BR_CD
    AND F.BR_STAT_CD = 'A'
LEFT OUTER JOIN TBPROD G
    ON B.PROD_CD = G.PROD_CD
LEFT OUTER JOIN TBEMP H
    ON A.MGR_EMP_ID = H.EMP_ID
INNER JOIN TBCHNL I
    ON A.CHANNEL_CD = I.CHNL_CD
WHERE C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'
  AND G.PROD_RISK_CD IN ('L', 'M', 'H')
  AND F.BR_TYPE_CD <> 'CLOSED'
ORDER BY A.ACCT_ID, B.CTRT_NO;
