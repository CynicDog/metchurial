-- ==========================================================================
-- 06_false_positives.sql
-- What it does: Four shapes that must produce no finding at all -- a column
--   whose name merely starts with a sensitive one, a column-to-column
--   comparison, a host-variable bind, and an IS NOT NULL test.
-- Modules: parsing/predicates.py, detect/extractor_visitor.py
-- ==========================================================================

SELECT * FROM CUSTOMER WHERE ACCT_ID_TYPE = '01';
SELECT * FROM CUSTOMER WHERE ACCT_ID = OTHER_COL;
SELECT * FROM CUSTOMER WHERE ACCT_ID = :hostvar;
SELECT * FROM CUSTOMER WHERE ACCT_ID IS NOT NULL;
