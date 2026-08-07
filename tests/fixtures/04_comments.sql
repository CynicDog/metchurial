-- ==========================================================================
-- 04_comments.sql
-- What it does: Findings inside a line comment and inside a block comment
--   (tagged in_comment=Y), alongside string literals that merely contain
--   comment markers and must not be treated as comments.
-- Modules: detect/comment_rescan.py, detect/extractor_visitor.py
-- ==========================================================================

-- ACCT_ID = '0000040'  (old test query, kept for reference)
SELECT * FROM CUSTOMER WHERE DESC LIKE '%--not a comment%';
SELECT * FROM CUSTOMER WHERE NOTE = 'test /* not a comment */ end';
/*
  Example query for QA:
  ACCT_ID = '0000041'
*/
SELECT * FROM CUSTOMER WHERE CTRT_NO = '0000042';
