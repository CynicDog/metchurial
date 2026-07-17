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
