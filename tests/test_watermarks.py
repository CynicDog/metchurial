# -*- coding: utf-8 -*-
"""Incremental-load watermark extraction (--extract-metadata /
refs_watermarks.tsv) -- see src/metchurial/references/watermarks.py.

Everything here runs through the real scan_file() pipeline rather than
poking the visitor directly: the shapes this detects
(`CURRENT DATE - 3 DAYS` and friends) only reach the visitor if the
statement actually parses as one clean tree, so a test that constructed
trees by hand could pass while the end-to-end path found nothing.

Run:
    python -m unittest tests.test_watermarks
"""

import os
import sys
import unittest

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import engine as scanner  # noqa: E402
from metchurial.models.options import ScanOptions  # noqa: E402
from metchurial.references import watermarks  # noqa: E402
from metchurial.tsv import _cell  # noqa: E402

FIXTURE = "41_incremental_load_watermarks.sql"


def _scan(filename=FIXTURE, **kwargs):
    kwargs.setdefault("extract_watermarks", True)
    path = os.path.join(FIXTURES_DIR, filename)
    return scanner.scan_file(path, ScanOptions(**kwargs))


def _by_line(result):
    return {row.line: row for row in result.watermark_uses}


class TestWatermarkPatterns(unittest.TestCase):
    """One case per shape the issue called out, all in fixture 41."""

    @classmethod
    def setUpClass(cls):
        cls.result = _scan()
        cls.rows = _by_line(cls.result)

    def test_fixture_parses_cleanly(self):
        self.assertIsNone(self.result.bad_reason)

    def test_direct_range_predicate(self):
        row = self.rows[14]
        self.assertEqual(row.watermark_column, "ORDER_DATE")
        self.assertEqual(row.table, "ORDERS")
        self.assertEqual(row.operator, ">=")
        self.assertEqual(row.base, "CURRENT DATE")
        self.assertEqual(row.window_expression, "CURRENT DATE - 365 DAYS")
        self.assertEqual(row.window_size, ("-365 DAY",))
        self.assertEqual(row.pattern, "DIRECT")

    def test_direct_equality_predicate(self):
        """Equality against a computed watermark, not just a range test."""
        row = self.rows[21]
        self.assertEqual(row.watermark_column, "OUR_MONTH_COLUMN")
        self.assertEqual(row.operator, "=")
        self.assertEqual(row.window_size, ("-1 MONTH",))
        self.assertEqual(row.pattern, "DIRECT")

    def test_format_then_subtract_single_wrapper(self):
        row = self.rows[28]
        self.assertEqual(row.watermark_column, "LOAD_MONTH")
        self.assertEqual(row.window_expression, "CHAR(CURRENT DATE - 1 MONTH, ISO)")
        self.assertEqual(row.window_size, ("-1 MONTH",))
        self.assertEqual(row.pattern, "WRAPPED:CHAR")

    def test_format_then_subtract_nested_wrappers(self):
        """The wrapper chain is reported outermost-first, so a reader can
        tell DECIMAL(CHAR(...)) from CHAR(DECIMAL(...))."""
        row = self.rows[34]
        self.assertEqual(row.watermark_column, "BATCH_KEY")
        self.assertEqual(row.window_expression,
                         "DECIMAL(CHAR(CURRENT DATE - 3 DAYS, USA), 8, 0)")
        self.assertEqual(row.window_size, ("-3 DAY",))
        self.assertEqual(row.pattern, "WRAPPED:DECIMAL>CHAR")

    def test_weekday_conditional_window_reports_every_branch(self):
        """DECODE(DAYOFWEEK(...), 2, 4, 6, 2, 1) -> match/result pairs plus
        the trailing default, so three candidate window sizes."""
        row = self.rows[41]
        self.assertEqual(row.watermark_column, "TXN_DATE")
        self.assertEqual(row.window_size, ("-4 DAY", "-2 DAY", "-1 DAY"))
        self.assertEqual(row.pattern, "DIRECT+CONDITIONAL")

    def test_hex_wrapped_window(self):
        row = self.rows[46]
        self.assertEqual(row.watermark_column, "PART_KEY")
        self.assertEqual(row.window_expression, "HEX(CURRENT DATE - 1 MONTH)")
        self.assertEqual(row.window_size, ("-1 MONTH",))
        self.assertEqual(row.pattern, "WRAPPED:HEX")


class TestWatermarkNormalization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = _by_line(_scan())

    def test_timestamp_register_is_reported_as_its_own_base(self):
        """A TIMESTAMP-based window is a different thing from a DATE-based
        one and shouldn't be collapsed into it."""
        self.assertEqual(self.rows[52].base, "CURRENT TIMESTAMP")
        self.assertEqual(self.rows[14].base, "CURRENT DATE")

    def test_window_on_the_left_flips_the_operator(self):
        """`CURRENT TIMESTAMP - 7 DAYS <= evt.created_at` means the same
        thing as `evt.created_at >= CURRENT TIMESTAMP - 7 DAYS`; every row
        reads column-first, so the operator is mirrored rather than
        copied."""
        row = self.rows[52]
        self.assertEqual(row.watermark_column, "CREATED_AT")
        self.assertEqual(row.operator, ">=")
        self.assertEqual(row.window_expression, "CURRENT TIMESTAMP - 7 DAYS")

    def test_plural_and_singular_units_normalize_together(self):
        """`- 1 MONTH` and `- 3 DAYS` normalize to the same canonical
        singular unit their plural/singular twins would, so a corpus-wide
        count groups them instead of splitting on how each was written."""
        self.assertEqual(self.rows[21].window_size, ("-1 MONTH",))
        self.assertEqual(self.rows[34].window_size, ("-3 DAY",))

    def test_raw_source_text_is_preserved_alongside_the_normalized_size(self):
        """window_expression is sliced from the source by character offset,
        not reconstructed from tokens, so it keeps its original spacing."""
        self.assertEqual(self.rows[41].window_expression,
                         "CURRENT DATE - DECODE(DAYOFWEEK(CURRENT DATE), 2, 4, 6, 2, 1) DAYS")

    def test_qualified_column_resolves_to_its_owning_table(self):
        row = self.rows[59]
        self.assertEqual((row.table, row.watermark_column), ("INVOICE_HEADER", "INVOICE_DATE"))

    def test_unqualified_column_keeps_the_table_placeholder(self):
        """Same convention refs_columns.tsv uses: a bare column name can't
        be attributed to a table, so it keeps the placeholder rather than
        guessing."""
        from metchurial.references import table_scan
        row = self.rows[28]
        self.assertEqual(row.table, table_scan.PLACEHOLDER_TABLE)
        self.assertEqual(row.watermark_column, "LOAD_MONTH")


class TestWatermarkScope(unittest.TestCase):
    """WHERE at any nesting depth is in scope; ON and HAVING are not."""

    @classmethod
    def setUpClass(cls):
        cls.result = _scan()
        cls.rows = _by_line(cls.result)

    def test_cte_body_where_is_in_scope(self):
        row = self.rows[68]
        self.assertEqual((row.table, row.watermark_column), ("ORDERS", "ORDER_DATE"))
        self.assertEqual(row.window_size, ("-90 DAY",))

    def test_correlated_subquery_where_is_in_scope(self):
        row = self.rows[81]
        self.assertEqual((row.table, row.watermark_column), ("CONTACT_LOG", "CONTACTED_AT"))
        self.assertEqual(row.window_size, ("-14 DAY",))

    def test_join_on_and_having_conditions_are_excluded(self):
        """Fixture statement 10 carries the same date arithmetic in its ON,
        its WHERE and its HAVING -- only the WHERE is an incremental
        filter."""
        self.assertIn(93, self.rows)  # the WHERE
        self.assertEqual(self.rows[93].watermark_column, "SHIPPED_AT")
        self.assertNotIn(90, self.rows)  # the ON
        self.assertNotIn(94, self.rows)  # the HAVING

    def test_bare_special_register_has_no_window_and_is_excluded(self):
        """`WHERE snap.snapshot_date = CURRENT DATE` filters on a moving
        target but has no window to size, which is what this artifact
        reports."""
        self.assertNotIn(99, self.rows)

    def test_every_filter_in_one_statement_gets_its_own_row(self):
        """Two watermark filters ANDed together are two occurrences, not
        one deduped row -- same per-occurrence convention as
        refs_functions.tsv/refs_relations.tsv."""
        self.assertEqual(self.rows[59].table, "INVOICE_HEADER")
        self.assertEqual(self.rows[60].table, "INVOICE_DETAIL")

    def test_expected_row_count(self):
        """Pins the total, so a future change that starts reporting ON /
        HAVING / bare-register predicates fails loudly instead of quietly
        widening the artifact."""
        self.assertEqual(len(self.result.watermark_uses), 12)


class TestUnparseableStatementFallback(unittest.TestCase):
    """Fixture 38's XMLTABLE/XMLELEMENT-heavy modules don't parse as whole
    statements, so their WHERE clauses reach the visitor as bare
    `search_condition` fragments with no where_clause node to walk up to.
    The token-scan fallback (nearest preceding clause keyword) is what
    keeps their incremental filters from being dropped -- these are the
    exact lines GitHub issue #2 cited."""

    @classmethod
    def setUpClass(cls):
        cls.result = _scan("38_db2_dialect_stress_suite.sql")
        cls.rows = _by_line(cls.result)

    def test_window_inside_a_derived_table_subquery(self):
        row = self.rows[172]
        self.assertEqual((row.table, row.watermark_column), ("ORDERS", "ORDER_DATE"))
        self.assertEqual(row.window_size, ("-365 DAY",))

    def test_window_recovered_from_a_where_anchored_fragment(self):
        row = self.rows[325]
        self.assertEqual(row.watermark_column, "INVOICE_DATE")
        self.assertEqual(row.window_size, ("-180 DAY",))

    def test_window_recovered_mid_clause_past_the_resync_anchor(self):
        """This fragment starts at the `AND`, not at the token right after
        WHERE, so an anchor-position-only test would miss it -- the
        governing-clause scan is what catches it."""
        row = self.rows[356]
        self.assertEqual(row.watermark_column, "CREATED_AT")
        self.assertEqual(row.base, "CURRENT TIMESTAMP")
        self.assertEqual(row.window_size, ("-7 DAY",))

    def test_from_clause_temporal_spec_is_not_a_watermark(self):
        """`FROM products FOR SYSTEM_TIME AS OF CURRENT TIMESTAMP - 30 DAYS`
        (line 201) is a temporal table qualifier, not a WHERE filter."""
        self.assertNotIn(201, self.rows)


class TestWatermarkExtractionIsOptIn(unittest.TestCase):

    def test_off_by_default(self):
        self.assertEqual(_scan(extract_watermarks=False).watermark_uses, [])

    def test_on_under_the_metadata_preset(self):
        path = os.path.join(FIXTURES_DIR, FIXTURE)
        result = scanner.scan_file(path, ScanOptions.metadata())
        self.assertEqual(len(result.watermark_uses), 12)

    def test_no_watermarks_in_a_fixture_without_any(self):
        self.assertEqual(_scan("01_basic_hit.sql").watermark_uses, [])


class TestWatermarksTsv(unittest.TestCase):

    def test_conditional_window_renders_as_one_joined_cell(self):
        """The several candidate sizes of a DECODE window share one row --
        one row per predicate occurrence stays true across every
        refs_*.tsv, so counting rows still counts predicates."""
        row = _by_line(_scan())[41]
        self.assertEqual(_cell(row.window_size), "-4 DAY; -2 DAY; -1 DAY")

    def test_header_written_for_an_empty_scan(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "refs_watermarks.tsv")
            watermarks.write_watermarks_tsv(out, [])
            with open(out, encoding="utf-8-sig") as fh:
                header = fh.read().splitlines()
        self.assertEqual(header, ["schema\ttable\twatermark_column\toperator\tbase\t"
                                  "window_expression\twindow_size\tpattern\tfile\tline"])

    def test_rows_render_in_header_order(self):
        import tempfile
        rows = sorted(_scan().watermark_uses, key=lambda r: r.line)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "refs_watermarks.tsv")
            watermarks.write_watermarks_tsv(out, rows)
            with open(out, encoding="utf-8-sig") as fh:
                lines = fh.read().splitlines()
        first = lines[1].split("\t")
        self.assertEqual(first[2], "ORDER_DATE")
        self.assertEqual(first[3], ">=")
        self.assertEqual(first[4], "CURRENT DATE")
        self.assertEqual(first[6], "-365 DAY")
        self.assertEqual(first[7], "DIRECT")
        self.assertEqual(first[9], "14")


if __name__ == "__main__":
    unittest.main()
