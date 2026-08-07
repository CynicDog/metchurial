-- ==========================================================================
-- 11_digit_boundary.sql
-- What it does: An unquoted numeric literal and a bare column-to-column
--   comparison; neither is a quoted-literal finding.
-- Modules: parsing/predicates.py, detect/extractor_visitor.py
-- ==========================================================================

SELECT * FROM CUSTOMER WHERE TBSAMPLE001=CTRT_NO;
SELECT * FROM CUSTOMER WHERE ACCT_ID = 12345;
