-- ==========================================================================
-- 03_multiline.sql
-- What it does: A predicate whose operator and literal sit on different
--   source lines, so the finding's line number and character offsets must
--   come from the literal token itself rather than from the statement
--   start.
-- Modules: parsing/predicates.py, detect/extractor_visitor.py, mask.py
-- ==========================================================================

SELECT *
FROM CUSTOMER
WHERE ACCT_ID =
    '0000030';
