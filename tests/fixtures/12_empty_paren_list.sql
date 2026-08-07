-- ==========================================================================
-- 12_empty_paren_list.sql
-- What it does: IN-lists with nothing inside them, in live code and in
--   comments, spanning several lines -- must neither crash nor invent
--   findings.
-- Modules: parsing/predicates.py, detect/supplementary_checks.py,
--   detect/comment_rescan.py
-- ==========================================================================

SELECT * FROM CUSTOMER A WHERE A.CTRT_NO IN ();

-- ctrt_no not in (
--)

SELECT * FROM CUSTOMER WHERE ACCT_ID IN (

)

SELECT * FROM CUSTOMER WHERE ACCT_ID = '0000123';
