-- ==========================================================================
-- 09_paren_list_boundary.sql
-- What it does: A truncated IN-list left inside a comment, plus a stray
--   unmatched close paren in live code: the paren-depth clamp must stop
--   either one from swallowing the live predicates that follow.
-- Modules: parsing/statement_driver.py, parsing/statement_starts.py,
--   detect/comment_rescan.py
-- ==========================================================================

-- broken/truncated fragment left behind in a comment, no closing paren on this line:
--                   -- and ctrt_no in ('0000099'
SELECT * FROM CUSTOMER WHERE ACCT_ID = '0000050';
    )
SELECT * FROM CUSTOMER WHERE ACCT_ID = '0000100';

SELECT * FROM CUSTOMER WHERE ACCT_ID IN (
    '0000201', -- flagged for review
    '0000202',
    '0000203'
);
