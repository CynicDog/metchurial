-- ==========================================================================
-- 13_comment_escape_recovery.sql
-- What it does: A truncated IN-list in a comment followed by a stray close
--   paren, with no semicolon anywhere before it: both live predicates must
--   still be found, each on its own line.
-- Modules: detect/comment_rescan.py, parsing/statement_driver.py,
--   parsing/statement_starts.py
-- ==========================================================================

--                   -- and ctrt_no in ('0000099'
SELECT ACCT_ID
FROM CUSTOMER
WHERE ACCT_ID = '0000050'
)
SELECT * FROM CUSTOMER WHERE ACCT_ID = '0000100';
