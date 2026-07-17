-- ============================================================================
-- DB2 DIALECT PARSER STRESS TEST AND METADATA EXTRACTOR VERIFICATION SUITE
-- Target File Length: > 600 Lines
-- Designed to test: Scope resolution, implicit/explicit joins, multi-CTE graphs,
-- DB2 dialect-specific window functions, lateral joins, and system catalog structures.
-- ============================================================================

-- MODULE 1: COMPLEX METADATA AND SYSTEM CATALOG LINEAGE
-- Tests: DB2-specific system tables (SYSCAT), spatial types, and string concat patterns.
-- Parser verification: Can the parser map dependencies to SYSCAT.TABLES and SYSCAT.COLUMNS?

SELECT
    t.tabschema AS schema_name,
    t.tabname AS table_name,
    t.card AS cardinality,
    c.colname AS column_name,
    c.typename AS data_type,
    c.length AS data_length,
    CASE
        WHEN c.nulls = 'Y' THEN 1
        ELSE 0
    END AS is_nullable,
    -- DB2 double-pipe string concatenation and scalar functions
    SUBSTR(t.tabschema || '.' || t.tabname, 1, 50) AS fully_qualified_name,
    COALESCE(t.remarks, 'No description available') AS table_comment,
    (SELECT COUNT(*)
     FROM syscat.indexes i
     WHERE i.tabschema = t.tabschema AND i.tabname = t.tabname) AS index_count
FROM syscat.tables t
INNER JOIN syscat.columns c
    ON t.tabschema = c.tabschema
    AND t.tabname = c.tabname
WHERE t.type = 'T'
  AND t.tabschema NOT LIKE 'SYS%'
  AND (c.typename IN ('VARCHAR', 'CHARACTER', 'TIMESTAMP', 'DECIMAL')
       OR c.typename LIKE 'DBCLOB%')
ORDER BY t.tabschema, t.tabname, c.colno
FETCH FIRST 150 ROWS ONLY;

---

-- MODULE 2: DEEPLY NESTED ANALYTICAL CTE MATRIX
-- Tests: Multiple Common Table Expressions, recursive/hierarchical relationships,
-- and window functions with custom frame specifications (ROWS/RANGE).
-- Parser verification: Tracks alias propagation from base tables through 4 layers of CTEs.

WITH RECURSIVE org_hierarchy(employee_id, manager_id, emp_level, path_string) AS (
    -- Anchor member
    SELECT
        e.emp_id,
        e.mgr_id,
        1,
        VARCHAR(e.last_name, 500)
    FROM hr_employees e
    WHERE e.mgr_id IS NULL

    UNION ALL

    -- Recursive member matching DB2 hierarchical specification
    SELECT
        child.emp_id,
        child.mgr_id,
        parent.emp_level + 1,
        parent.path_string || ' -> ' || child.last_name
    FROM hr_employees child
    INNER JOIN org_hierarchy parent ON child.mgr_id = parent.employee_id
),

financial_raw AS (
    SELECT
        f.emp_id,
        f.fiscal_year,
        f.quarter,
        f.revenue,
        f.operating_cost,
        f.revenue - f.operating_cost AS net_margin,
        -- Window function with complex frame specification
        SUM(f.revenue) OVER (
            PARTITION BY f.emp_id, f.fiscal_year
            ORDER BY f.quarter
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS ytd_revenue,
        AVG(f.operating_cost) OVER (
            PARTITION BY f.emp_id
            ORDER BY f.fiscal_year, f.quarter
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_avg_cost
    FROM employee_financials f
    WHERE f.fiscal_year BETWEEN 2020 AND 2026
),

aggregated_performance AS (
    SELECT
        fr.emp_id,
        fr.fiscal_year,
        SUM(fr.revenue) AS total_annual_revenue,
        SUM(fr.net_margin) AS total_annual_margin,
        AVG(fr.rolling_avg_cost) AS generalized_cost_index,
        COUNT(DISTINCT fr.quarter) AS active_quarters_count
    FROM financial_raw fr
    GROUP BY fr.emp_id, fr.fiscal_year
    HAVING SUM(fr.revenue) > 50000.00
),

final_scoping_layer AS (
    SELECT
        ap.emp_id,
        oh.path_string,
        oh.emp_level,
        ap.fiscal_year,
        ap.total_annual_revenue,
        ap.total_annual_margin,
        -- DB2-compatible ranking functions
        DENSE_RANK() OVER (PARTITION BY ap.fiscal_year ORDER BY ap.total_annual_revenue DESC) AS rev_rank,
        NTILE(4) OVER (PARTITION BY ap.fiscal_year ORDER BY ap.total_annual_margin DESC) AS margin_quartile
    FROM aggregated_performance ap
    INNER JOIN org_hierarchy oh ON ap.emp_id = oh.employee_id
)

SELECT
    fsl.emp_id,
    fsl.path_string,
    fsl.emp_level,
    fsl.fiscal_year,
    fsl.total_annual_revenue,
    fsl.total_annual_margin,
    fsl.rev_rank,
    fsl.margin_quartile,
    CASE
        WHEN fsl.rev_rank <= 3 THEN 'Top Tier'
        WHEN fsl.margin_quartile = 1 THEN 'High Efficiency'
        ELSE 'Standard Performance'
    END AS execution_class
FROM final_scoping_layer fsl
WHERE fsl.emp_level <= 5
ORDER BY fsl.fiscal_year DESC, fsl.total_annual_revenue DESC;

---

-- MODULE 3: LATERAL TABLE EXPRESSION AND OUTER JOIN COMPLEXITY
-- Tests: DB2 `LATERAL` keyword, correlated subqueries inside FROM clause,
-- and mixed left/right/full outer joins.
-- Parser verification: Does the parser understand that columns inside the LATERAL block
-- reference tables declared *outside* of it in the FROM clause?

SELECT
    dept.dept_id,
    dept.dept_name,
    emp.emp_id,
    emp.first_name,
    emp.last_name,
    lat_sales.total_deals,
    lat_sales.max_deal_value,
    lat_sales.avg_deal_value,
    proj.project_name,
    proj.budget
FROM departments dept
LEFT OUTER JOIN employees emp ON dept.dept_id = emp.dept_id
-- Complex DB2 LATERAL reference
LEFT OUTER JOIN LATERAL (
    SELECT
        COUNT(o.order_id) AS total_deals,
        MAX(o.total_amount) AS max_deal_value,
        AVG(o.total_amount) AS avg_deal_value
    FROM orders o
    WHERE o.sales_rep_id = emp.emp_id
      AND o.order_status = 'COMPLETED'
      AND o.order_date >= CURRENT DATE - 365 DAYS
) AS lat_sales ON 1=1
FULL OUTER JOIN projects proj ON proj.department_id = dept.dept_id
WHERE dept.location_code IN ('US-EAST', 'EU-WEST', 'APAC-HQ')
  AND (lat_sales.total_deals > 5 OR proj.budget > 100000.00);

---

-- MODULE 4: TEMPORAL HISTORY AND SYSTEM-PERIOD DATA EXTRACTION
-- Tests: DB2 temporal tables syntax (`FOR SYSTEM_TIME AS OF`),
-- epoch transitions, and historical state recreation.
-- Parser verification: Extracts temporal qualifiers from target tables.

WITH historical_snapshot AS (
    SELECT
        prod.product_id,
        prod.product_name,
        prod.unit_price AS historical_price,
        -- Querying DB2 system temporal table state as of a fixed past timestamp
        (SELECT p_hist.unit_price
         FROM products FOR SYSTEM_TIME AS OF TIMESTAMP('2024-01-01-00.00.00.000000') p_hist
         WHERE p_hist.product_id = prod.product_id
        ) AS price_jan_2024,
        (SELECT p_hist.unit_price
         FROM products FOR SYSTEM_TIME AS OF TIMESTAMP('2025-01-01-00.00.00.000000') p_hist
         WHERE p_hist.product_id = prod.product_id
        ) AS price_jan_2025,
        prod.sys_start AS record_effective_date,
        prod.sys_end AS record_expiration_date
    FROM products FOR SYSTEM_TIME AS OF CURRENT TIMESTAMP - 30 DAYS prod
)

SELECT
    hs.product_id,
    hs.product_name,
    hs.historical_price AS price_30_days_ago,
    hs.price_jan_2024,
    hs.price_jan_2025,
    COALESCE(hs.historical_price - hs.price_jan_2024, 0.00) AS price_delta_2024,
    CASE
        WHEN hs.historical_price > hs.price_jan_2025 THEN 'Inflationary Trend'
        WHEN hs.historical_price < hs.price_jan_2025 THEN 'Deflationary Trend'
        ELSE 'Stable Pricing'
    END AS pricing_trajectory,
    hs.record_effective_date,
    hs.record_expiration_date
FROM historical_snapshot hs
WHERE hs.historical_price > 0.00;

---

-- MODULE 5: COALESCED SET OPERATIONS MATRIX (UNION, INTERSECT, EXCEPT ALL)
-- Tests: Combining distinct set operations, verifying schema alignment,
-- and nested set intersections.
-- Parser verification: Validates branch-column mapping and set-precedence.

(
    SELECT
        'RETAIL_CUSTOMER' AS source_segment,
        rc.cust_id AS entity_id,
        rc.first_name || ' ' || rc.last_name AS display_name,
        rc.email_address AS communication_channel,
        rc.registration_date AS activity_start_date,
        DECIMAL(SUM(tx.amount), 12, 2) AS lifetime_value
    FROM retail_customers rc
    INNER JOIN retail_transactions tx ON rc.cust_id = tx.cust_id
    WHERE tx.status = 'SETTLED'
    GROUP BY rc.cust_id, rc.first_name, rc.last_name, rc.email_address, rc.registration_date
)
UNION ALL
(
    SELECT
        'ENTERPRISE_CLIENT' AS source_segment,
        ec.client_id AS entity_id,
        ec.company_name AS display_name,
        ec.primary_contact_email AS communication_channel,
        ec.contract_sign_date AS activity_start_date,
        DECIMAL(ec.annual_contract_value, 12, 2) AS lifetime_value
    FROM enterprise_clients ec
    WHERE ec.contract_status = 'ACTIVE'
)
INTERSECT
(
    SELECT
        m.segment_type AS source_segment,
        m.member_id AS entity_id,
        m.full_name AS display_name,
        m.email_address AS communication_channel,
        m.created_at AS activity_start_date,
        DECIMAL(m.total_spend, 12, 2) AS lifetime_value
    FROM marketing_master_list m
    WHERE m.opt_in_status = 'Y'
)
EXCEPT ALL
(
    SELECT
        'RETAIL_CUSTOMER' AS source_segment,
        dc.cust_id AS entity_id,
        dc.display_name,
        dc.email_address AS communication_channel,
        dc.deactivated_at AS activity_start_date,
        0.00 AS lifetime_value
    FROM deactivated_customers dc
);

---

-- MODULE 6: MULTI-LEVEL CORRELATED SUBQUERIES AND COMPLEX EXPRESSIONS
-- Tests: De-correlated subquery evaluation, nested scalar expressions,
-- and inline CAST / NULLIF transformations.
-- Parser verification: AST scoping of variables across subquery boundaries.

SELECT
    out_inv.invoice_id,
    out_inv.invoice_date,
    out_inv.customer_id,
    out_inv.total_amount,
    -- Level 1 Correlation
    (SELECT COUNT(*)
     FROM invoice_items item
     WHERE item.invoice_id = out_inv.invoice_id
       AND item.unit_price > (
           -- Level 2 Correlation
           SELECT AVG(sub_item.unit_price)
           FROM invoice_items sub_item
           INNER JOIN products p ON sub_item.product_id = p.product_id
           WHERE p.category_id = (
               -- Level 3 Correlation
               SELECT p2.category_id
               FROM products p2
               WHERE p2.product_id = item.product_id
           )
       )
    ) AS items_above_category_average,
    -- Complex expression testing mathematical operators, CAST, and NULLIF
    CAST(out_inv.total_amount AS DOUBLE) / NULLIF(
        CAST((SELECT SUM(item2.quantity)
              FROM invoice_items item2
              WHERE item2.invoice_id = out_inv.invoice_id) AS DOUBLE),
        0.00
    ) AS average_price_per_unit_sold,
    -- DB2 specific XML capabilities parser test
    XMLSERIALIZE(
        XMLDOCUMENT(
            XMLELEMENT(NAME "InvoiceSummary",
                XMLATTRIBUTES(out_inv.invoice_id AS "id"),
                XMLELEMENT(NAME "Total", out_inv.total_amount),
                XMLELEMENT(NAME "Date", out_inv.invoice_date)
            )
        ) AS VARCHAR(1000)
    ) AS xml_metadata_payload
FROM invoices out_inv
WHERE out_inv.invoice_status = 'POSTED'
  AND out_inv.invoice_date >= CURRENT DATE - 180 DAYS;

---

-- MODULE 7: AD-HOC SIMULATED TRANSACTIONS GENERATION & XML PARSING
-- Tests: DB2-specific sysibm.sysdummy1, complex string tokenization,
-- and parsing XML values into tabular structures (XMLTABLE).
-- Parser verification: Verifies table functions syntax and XML-namespaces parsing.

SELECT
    xtab.order_id,
    xtab.customer_id,
    xtab.order_date,
    xtab.item_id,
    xtab.quantity,
    xtab.unit_price,
    DECIMAL(xtab.quantity * xtab.unit_price, 10, 2) AS line_item_total
FROM
    xml_data_store xds,
    -- XMLTABLE parses unstructured data fields into relational columns
    XMLTABLE(
        '$d/PurchaseOrder/Items/Item' PASSING xds.xml_payload AS "d"
        COLUMNS
            order_id    VARCHAR(50)  PATH './../../OrderId',
            customer_id VARCHAR(50)  PATH './../../CustomerId',
            order_date  TIMESTAMP    PATH './../../OrderDate',
            item_id     VARCHAR(30)  PATH './ItemId',
            quantity    INTEGER      PATH './Quantity',
            unit_price  DECIMAL(8,2) PATH './UnitPrice'
    ) AS xtab
WHERE xds.status = 'PROCESSED'
  AND xds.created_at >= CURRENT TIMESTAMP - 7 DAYS;

---

-- MODULE 8: ULTIMATE COMBINATORIAL STRESS-TEST
-- Fuses massive dimensional joins, inline grouping sets, CUBE, ROLLUP,
-- and complex CASE statements with DB2 physical execution clause hints.
-- Parser verification: Checks that the parser handles optimization hints and aggregation groupings.

SELECT
    COALESCE(loc.region_name, 'TOTAL WORLDWIDE') AS region_name,
    COALESCE(cat.category_name, 'ALL CATEGORIES') AS category_name,
    COALESCE(CAST(d.d_year AS VARCHAR(4)), 'ALL YEARS') AS sales_year,
    SUM(sls.sales_amount) AS raw_sales,
    SUM(sls.tax_amount) AS raw_taxes,
    -- Percentage calculations using complex conditional aggregations
    DECIMAL(
        (SUM(sls.sales_amount) / NULLIF(
            SUM(SUM(sls.sales_amount)) OVER (PARTITION BY loc.region_name),
            0.00
        )) * 100.0,
        5, 2
    ) AS regional_contribution_percentage,
    -- Multiple metrics showcasing DB2 mathematical functions
    ROUND(STDDEV(sls.sales_amount), 4) AS sales_volatility,
    CORRELATION(sls.sales_amount, sls.profit_amount) AS profit_correlation,
    -- Complex searched CASE expression testing syntax limits
    CASE
        WHEN SUM(sls.sales_amount) >= 1000000.00 AND CORRELATION(sls.sales_amount, sls.profit_amount) >= 0.85
            THEN 'Tier A - Ultra Stable High Volume'
        WHEN SUM(sls.sales_amount) >= 1000000.00 AND CORRELATION(sls.sales_amount, sls.profit_amount) < 0.85
            THEN 'Tier B - Volatile High Volume'
        WHEN SUM(sls.sales_amount) < 1000000.00 AND SUM(sls.sales_amount) >= 100000.00
            THEN 'Tier C - Mid Market Standard'
        ELSE 'Tier D - Low Volatility / Tail End'
    END AS segment_classification
FROM sales_fact sls
INNER JOIN store_dimensions str ON sls.store_id = str.store_id
INNER JOIN location_dimensions loc ON str.location_id = loc.location_id
INNER JOIN product_catalog prod ON sls.product_id = prod.product_id
INNER JOIN category_dimensions cat ON prod.category_id = cat.category_id
INNER JOIN date_dimension d ON sls.date_key = d.d_date_sk
WHERE d.d_year IN (2023, 2024, 2025, 2026)
  AND loc.country_code IN ('US', 'CA', 'GB', 'DE', 'FR', 'JP', 'AU')
-- Multi-dimensional grouping patterns: CUBE and ROLLUP
GROUP BY ROLLUP(loc.region_name, cat.category_name, d.d_year)
HAVING SUM(sls.sales_amount) IS NOT NULL
-- DB2 optimization parameters at physical layer
FOR READ ONLY
WITH UR;
