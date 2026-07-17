-- [query-identity stress corpus: DISTINCT, negative control]
-- Shares zero tables with CORE_A (20-25/30-32) *and* CORE_B (34-37) --
-- a third, genuinely unrelated domain (inventory/warehouse, not account/
-- contract or employee/department). An earlier draft of this fixture
-- reused CORE_B's own TBEMP/TBDEPT/TBPOS tables, which made it a poor
-- negative control against CORE_B specifically (high accidental overlap)
-- even though it was correctly unrelated to CORE_A -- fixed by using
-- fresh tables here instead. Must score low similarity against every
-- CORE_A- and CORE_B-family fixture and must not land on either core
-- signature.
SELECT
    W.WH_ID,
    W.WH_NM,
    ST.STOCK_QTY,
    IT.ITEM_NM
FROM TBWAREHOUSE W
INNER JOIN TBSTOCK ST
    ON W.WH_ID = ST.WH_ID
LEFT OUTER JOIN TBITEM IT
    ON ST.ITEM_CD = IT.ITEM_CD
WHERE W.WH_STAT_CD = 'A'
  AND ST.STOCK_QTY < 100;
