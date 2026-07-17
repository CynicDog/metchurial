-- Zero-argument function calls (function_invocation's arg_list is now
-- optional) -- previously had no parse path, so NOW()/CURRENT_TIMESTAMP-
-- style calls silently disappeared from --extract-functions output and
-- from the parse tree entirely.
SELECT
    A.ACCT_ID,
    A.ACCT_NM,
    NOW() AS SCAN_TS
FROM TBACCT A
WHERE A.ACCT_ID = '1112223'
  AND A.LAST_UPD_TS < NOW();
