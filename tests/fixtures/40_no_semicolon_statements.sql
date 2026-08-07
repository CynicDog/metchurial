-- ==========================================================================
-- 40_no_semicolon_statements.sql
-- What it does: Six standalone queries with no semicolon anywhere in the
--   file: boundaries must be inferred, and neither the CTE prologue nor the
--   WITH UR isolation clause may be mistaken for a statement start.
-- Modules: parsing/statement_starts.py, parsing/statement_driver.py,
--   split/select_blocks.py
-- ==========================================================================

-- 1. 세미콜론이 하나도 없는 파일 -- 첫 번째 문장
SELECT A.ACCT_ID
     , A.ACCT_NM
FROM   TBACCT A
WHERE  A.STAT_CD = 'A'
ORDER BY A.ACCT_ID

-- 2. 여러 줄 절, 문장 구분자 없음
SELECT A.ACCT_ID
     , SUM(A.AMT1) AS AMT_SUM
FROM   TBACCT A
WHERE  A.OPEN_DT >= '201907'
GROUP BY A.ACCT_ID
HAVING SUM(A.AMT1) > 0
ORDER BY AMT_SUM DESC
FETCH FIRST 100 ROWS ONLY

-- 3. UNION 은 한 문장이다
SELECT ACCT_ID FROM TBACCT
UNION ALL
SELECT ACCT_ID FROM TBSTAT

-- 4. 서브쿼리는 괄호 안이라 나눠지지 않는다
SELECT R.COL_A
FROM   T_REF R
WHERE  R.ID1 IN (
           SELECT S.ACCT_ID
           FROM   TBSTAT S
           WHERE  S.TYPE_CD = '01'
       )

-- 5. CTE 프롤로그와 그 SELECT 는 같은 문장이다
WITH AUX AS (
    SELECT ACCT_ID, MAX(SEQ1) AS SEQ_MAX
    FROM   TBSTAT
    GROUP BY ACCT_ID
)
SELECT X.ACCT_ID
     , X.SEQ_MAX
FROM   AUX X
JOIN   TBACCT A ON A.ACCT_ID = X.ACCT_ID

-- 6. 격리 수준 WITH UR 은 문장 시작이 아니다
SELECT A.ACCT_ID
     , A.ACCT_NM
FROM   TBACCT A
WITH UR
