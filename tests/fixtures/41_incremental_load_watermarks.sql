-- Incremental-load watermark fixture (--extract-metadata /
-- refs_watermarks.tsv). Every statement here is a rolling "today minus a
-- window" filter of the kind Informatica-generated DB2 ETL produces: the
-- WHERE clause picks up a moving slice on every run instead of a
-- hardcoded date range. Anonymized shapes, not real production SQL.

-- 1. Direct special-register arithmetic, range predicate.
SELECT
    ord.order_id,
    ord.customer_id,
    ord.total_amount
FROM orders ord
WHERE ord.order_status = 'COMPLETED'
  AND ord.order_date >= CURRENT DATE - 365 DAYS;

-- 2. Direct special-register arithmetic, equality against a computed
-- watermark rather than a range -- a whole-month reload keyed off a
-- month column.
SELECT agg.month_key, agg.revenue
FROM monthly_revenue_agg agg
WHERE agg.our_month_column = CURRENT DATE - 1 MONTH;

-- 3. Format-then-subtract: the arithmetic is wrapped in a formatting call
-- before comparison, because the compared column stores a YYYY-MM-DD-ish
-- character key rather than a real DATE.
SELECT load_id, load_month
FROM load_control
WHERE load_month = CHAR(CURRENT DATE - 1 MONTH, ISO);

-- 4. Format-then-subtract through two nested wrappers, landing on a
-- numeric YYYYMMDD batch key.
SELECT bat.batch_id, bat.batch_key
FROM batch_control bat
WHERE bat.batch_key = DECIMAL(CHAR(CURRENT DATE - 3 DAYS, USA), 8, 0);

-- 5. Weekday-conditional window: go back 4 days on Monday (DAYOFWEEK 2)
-- and 2 days on Friday (DAYOFWEEK 6) so a Monday run still picks up the
-- weekend, 1 day otherwise.
SELECT txn.txn_id, txn.txn_date, txn.amount
FROM transactions txn
WHERE txn.txn_date >= CURRENT DATE - DECODE(DAYOFWEEK(CURRENT DATE), 2, 4, 6, 2, 1) DAYS;

-- 6. HEX()-wrapped date arithmetic on a partition/bucket key.
SELECT prt.part_key, prt.partition_rows
FROM partition_stats prt
WHERE prt.part_key = HEX(CURRENT DATE - 1 MONTH);

-- 7. Timestamp-based window, with the arithmetic written on the *left*
-- of the operator -- the row still reads column-first.
SELECT evt.event_id, evt.created_at
FROM event_stream evt
WHERE CURRENT TIMESTAMP - 7 DAYS <= evt.created_at;

-- 8. Two independent watermark filters ANDed together in one statement
-- (a header table and its detail table), each its own occurrence.
SELECT hdr.invoice_id, det.line_no
FROM invoice_header hdr, invoice_detail det
WHERE hdr.invoice_id = det.invoice_id
  AND hdr.invoice_date >= CURRENT DATE - 30 DAYS
  AND det.posted_at >= CURRENT TIMESTAMP - 30 DAYS;

-- 9. Windows inside a CTE body and inside a correlated subquery -- both
-- are WHERE clauses defining a windowed record set, just not the
-- outermost one.
WITH recent_orders AS (
    SELECT rec.customer_id, rec.total_amount
    FROM orders rec
    WHERE rec.order_date >= CURRENT DATE - 90 DAYS
)
SELECT cus.customer_id
FROM customers cus
WHERE cus.customer_id IN (
        SELECT sub.customer_id
        FROM recent_orders sub
        WHERE sub.total_amount > 1000.00
      )
  AND EXISTS (
        SELECT 1
        FROM contact_log clog
        WHERE clog.customer_id = cus.customer_id
          AND clog.contacted_at >= CURRENT TIMESTAMP - 14 DAYS
      );

-- 10. Out of scope on purpose: an ON condition and a HAVING condition are
-- join/post-aggregation logic, not incremental filters, so neither is
-- reported even though both carry the same date arithmetic. The WHERE on
-- the same statement is reported.
SELECT shp.ship_id, COUNT(itm.item_id) AS item_count
FROM shipments shp
INNER JOIN shipment_items itm
        ON itm.ship_id = shp.ship_id
       AND itm.picked_at >= CURRENT DATE - 5 DAYS
WHERE shp.shipped_at >= CURRENT DATE - 5 DAYS
GROUP BY shp.ship_id
HAVING MAX(itm.picked_at) >= CURRENT DATE - 2 DAYS;

-- 11. Also out of scope on purpose: a bare special register with no
-- arithmetic has no window to size, so it produces no row.
SELECT snap.snapshot_id
FROM daily_snapshot snap
WHERE snap.snapshot_date = CURRENT DATE;
