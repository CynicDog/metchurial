-- [query-identity stress corpus: CORE_A]
-- Same tables/predicates as 20_query_identity_base.sql, but the
-- TBSAMPLE001 join is rewritten as an old-style comma-join with its join
-- condition moved into WHERE, instead of an explicit `JOIN ... ON`. This
-- is a genuine syntax difference relations.py already treats as
-- equivalent (a comma-join's predicate is recovered from the
-- WHERE-implicit visitor, same as an explicit JOIN's ON-clause) -- a core
-- signature built on top of that same join-edge extraction must land on
-- CORE_A here too, not just tolerate ANSI-JOIN-vs-ANSI-JOIN differences.
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
, TBSAMPLE001 D
WHERE A.ACCT_ID = D.ACCT_ID
  AND C.STAT_CD IN ('01', '02')
  AND B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'
GROUP BY A.ACCT_ID, B.CTRT_NO, C.STAT_CD, D.TBSAMPLE001, B.CTRT_TYPE_CD, B.BASE_AMT;
