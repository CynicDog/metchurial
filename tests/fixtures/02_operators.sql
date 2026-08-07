-- ==========================================================================
-- 02_operators.sql
-- What it does: Every predicate operator the extractor recognises -- equals
--   with no surrounding spaces, an IN-list, BETWEEN, a reversed literal-on-
--   the-left comparison, and not-equals.
-- Modules: parsing/predicates.py, detect/extractor_visitor.py
-- ==========================================================================

SELECT * FROM CUSTOMER WHERE ACCT_ID='0000002';
SELECT * FROM CUSTOMER WHERE CTRT_NO IN ('1000001', '1000002', '1000003');
SELECT * FROM CUSTOMER WHERE ACCT_ID BETWEEN '0000010' AND '0000099';
SELECT * FROM CUSTOMER WHERE '0000123' = ACCT_ID;
SELECT * FROM CUSTOMER WHERE ACCT_ID <> '0000005';
