-- [query-identity stress corpus: HARD CASE, documented non-goal]
-- Semantically close to CORE_A (same base tables, roughly the same
-- filtering intent) but the TBSTAT relationship is expressed as a
-- correlated EXISTS subquery instead of a JOIN -- no join edge for
-- TBSTAT exists in this statement's tree at all, it's a predicate inside
-- a nested search_condition. A *structural* signature (this project's
-- whole approach, see the issue) cannot and should not be expected to
-- resolve this to CORE_A's core signature -- that would require proving
-- semantic equivalence between a JOIN and an EXISTS-correlated subquery,
-- which is a fundamentally different (and much harder) problem than
-- structural comparison. Kept here as a documented non-goal, not a bug to
-- fix: the future test suite should assert this does NOT match CORE_A,
-- not that it does.
SELECT
    A.ACCT_ID,
    B.CTRT_NO,
    D.TBSAMPLE001,
    CASE
        WHEN B.CTRT_TYPE_CD = '01' THEN B.BASE_AMT * 1.05
        WHEN B.CTRT_TYPE_CD = '02' THEN B.BASE_AMT * 1.10
        ELSE B.BASE_AMT
    END AS ADJ_AMT
FROM TBACCT A
INNER JOIN TBCTRT B
    ON A.ACCT_ID = B.ACCT_ID
JOIN TBSAMPLE001 D
    ON A.ACCT_ID = D.ACCT_ID
WHERE B.CTRT_TYPE_CD <> '99'
  AND A.OPEN_DT BETWEEN '20200101' AND '20261231'
  AND EXISTS (
        SELECT 1
        FROM TBSTAT C
        WHERE C.CTRT_NO = B.CTRT_NO
          AND C.STAT_CD IN ('01', '02')
      );
