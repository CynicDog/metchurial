-- A CTE whose own body is a JOIN, then referenced from an outer ANSI
-- JOIN -- exercises both grammar fixes (CTE body -> fullselect, and
-- table_reference's now-direct-left-recursive JOIN chain) together in
-- one statement. Previously the CTE body would be independently
-- re-surfaced by the tiered driver as if it were its own standalone
-- top-level SELECT, and the ANSI JOIN had no parse path at all.
WITH ACTIVE_ACCT AS (
    SELECT A.ACCT_ID, A.ACCT_NM
    FROM TBACCT A
    JOIN TBSTAT S ON A.ACCT_ID = S.ACCT_ID
    WHERE S.STAT_CD = '01'
)
SELECT
    AA.ACCT_ID,
    AA.ACCT_NM,
    C.CTRT_NO
FROM ACTIVE_ACCT AA
LEFT JOIN TBCTRT C
    ON AA.ACCT_ID = C.ACCT_ID
WHERE AA.ACCT_ID = '7654321';
