-- ==========================================================================
-- 10_subquery_in_list.sql
-- What it does: IN followed by a subquery rather than a literal list -- it
--   must yield table references, not a list of literal findings.
-- Modules: parsing/predicates.py, references/table_scan.py,
--   detect/extractor_visitor.py
-- ==========================================================================

SELECT * FROM CUSTOMER
WHERE CTRT_NO IN (SELECT CTRT_NO FROM TBSAMPLE001 WHERE STAT_CD = '02');
SELECT * FROM CUSTOMER WHERE ACCT_ID = '0000123';
