-- ACCT_ID = '0000040'  (old test query, kept for reference)
SELECT * FROM CUSTOMER WHERE DESC LIKE '%--not a comment%';
SELECT * FROM CUSTOMER WHERE NOTE = 'test /* not a comment */ end';
/*
  Example query for QA:
  ACCT_ID = '0000041'
*/
SELECT * FROM CUSTOMER WHERE CTRT_NO = '0000042';
