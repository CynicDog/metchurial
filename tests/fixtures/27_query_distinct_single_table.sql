-- [query-identity stress corpus: DISTINCT, negative control]
-- A trivial single-table query, no joins at all -- an edge case for the
-- join-graph half of the signature (an empty/singleton join graph must
-- still hash and score consistently, not crash or degenerate). Shares
-- TBACCT with the CORE_A cluster but nothing else, and has no join graph
-- to compare against CORE_A's -- must not land on CORE_A's core signature.
SELECT
    A.ACCT_ID,
    A.ACCT_NM
FROM TBACCT A
WHERE A.CHANNEL_CD = 'WEB';
