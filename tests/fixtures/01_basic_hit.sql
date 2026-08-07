-- ==========================================================================
-- 01_basic_hit.sql
-- What it does: The simplest sensitive-value finding: one equality
--   predicate comparing a sensitive column to a quoted literal. The
--   baseline every other detection fixture varies from.
-- Modules: parsing/statement_driver.py, parsing/predicates.py,
--   detect/extractor_visitor.py
-- ==========================================================================

SELECT *
FROM CUSTOMER
WHERE ACCT_ID = '0000001';
