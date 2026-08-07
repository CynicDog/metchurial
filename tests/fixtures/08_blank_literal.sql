-- ==========================================================================
-- 08_blank_literal.sql
-- What it does: Empty and whitespace-only literals, including a double-
--   quoted one that the grammar has no parse path for and only the token-
--   scan fallback can see.
-- Modules: detect/extractor_visitor.py, detect/supplementary_checks.py
-- ==========================================================================

SELECT * FROM CUSTOMER WHERE ACCT_ID = '';
SELECT * FROM CUSTOMER WHERE CTRT_NO = '   ';
SELECT * FROM CUSTOMER WHERE ACCT_ID = "" ;
SELECT * FROM CUSTOMER WHERE ACCT_ID IN ('', '0000080');
SELECT * FROM CUSTOMER WHERE ACCT_NM = '0000081';
