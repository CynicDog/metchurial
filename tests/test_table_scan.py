# -*- coding: utf-8 -*-
"""Unit tests for table_scan.py -- the token-scan engine Features 1 and 3
sit on top of. These pin down behavior across the grammar gotchas that
motivated writing this as a separate token-scan pass in the first place:
schema-qualified names, JOIN...ON/USING (unreachable from any parse tree),
CTE-name exclusion, UNION-sibling scoping, and derived-table inner tables
(a real bug caught during development -- a naive single-pass design
silently dropped tables referenced only inside a derived table's own
parens; see table_scan.py's _discover_blocks/_populate_table_lists
docstrings for why this needs to be two coordinated passes).

Run:
    python -m unittest tests.test_table_scan
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src.detect.statement_driver import lex_file, chunk_ranges  # noqa: E402
from src.references import table_scan as ts  # noqa: E402


def _blocks_for(sql):
    """Returns the list of QueryBlock lists, one per chunk, for `sql`."""
    all_tokens, _ = lex_file(sql)
    return [ts.scan_query_blocks(all_tokens[start:end])
            for start, end in chunk_ranges(all_tokens)]


def _tables(blocks):
    return sorted((t.schema, t.table, t.alias) for qb in blocks for t in qb.tables)


def _edges(blocks):
    return sorted((e.left.alias, e.right.alias, e.join_type)
                  for e in ts.scan_join_edges(blocks))


class TestSchemaQualifiedNames(unittest.TestCase):
    def test_two_part_name_and_alias(self):
        blocks = _blocks_for("SELECT * FROM schema1.table1 a WHERE a.col1 = '1';")[0]
        self.assertEqual(_tables(blocks), [("SCHEMA1", "TABLE1", "A")])

    def test_bare_table_has_placeholder_schema(self):
        blocks = _blocks_for("SELECT * FROM t1;")[0]
        self.assertEqual(_tables(blocks), [(ts.PLACEHOLDER_SCHEMA, "T1", "T1")])

    def test_three_part_name_drops_catalog(self):
        blocks = _blocks_for("SELECT * FROM cat1.schema1.table1;")[0]
        self.assertEqual(_tables(blocks), [("SCHEMA1", "TABLE1", "TABLE1")])


class TestJoinExtraction(unittest.TestCase):
    def test_explicit_join_on(self):
        blocks = _blocks_for(
            "SELECT a.col1,b.col2 FROM t1 a JOIN t2 b ON a.col1=b.col2 WHERE a.x=1;")[0]
        self.assertEqual(_tables(blocks),
                         [(ts.PLACEHOLDER_SCHEMA, "T1", "A"), (ts.PLACEHOLDER_SCHEMA, "T2", "B")])
        self.assertEqual(_edges(blocks), [("A", "B", "JOIN")])
        edge = ts.scan_join_edges(blocks)[0]
        self.assertIn("col1", edge.predicate_text)
        self.assertIn("col2", edge.predicate_text)

    def test_left_outer_join(self):
        blocks = _blocks_for("SELECT * FROM t1 a LEFT OUTER JOIN t2 b ON a.x=b.y;")[0]
        self.assertEqual(_edges(blocks), [("A", "B", "LEFT")])

    def test_using_clause_captured(self):
        blocks = _blocks_for("SELECT * FROM t1 a JOIN t2 b USING (id);")[0]
        edge = ts.scan_join_edges(blocks)[0]
        self.assertIn("id", edge.predicate_text)

    def test_comma_join_has_no_predicate_here(self):
        blocks = _blocks_for("SELECT * FROM t1 a, t2 b WHERE a.x=b.y;")[0]
        self.assertEqual(_edges(blocks), [("A", "B", "COMMA")])
        self.assertEqual(ts.scan_join_edges(blocks)[0].predicate_text, "")

    def test_second_join_table_recovered_despite_broken_grammar(self):
        # Regression guard for the vendored grammar's dead `joined_table`
        # rule (see table_scan.py's module docstring) -- the second table
        # of an explicit JOIN forms no parse-tree node at all; this must
        # still come from the token-scan, not a tree walk.
        blocks = _blocks_for("SELECT * FROM t1 a JOIN t2 b ON a.x=b.y;")[0]
        tables = {t.table for qb in blocks for t in qb.tables}
        self.assertIn("T2", tables)


class TestCteExclusion(unittest.TestCase):
    def test_cte_name_not_a_real_table(self):
        blocks = _blocks_for("WITH cte AS (SELECT id FROM t1) SELECT * FROM cte;")[0]
        tables = {t.table for qb in blocks for t in qb.tables}
        self.assertIn("T1", tables)
        self.assertNotIn("CTE", tables)

    def test_multiple_ctes(self):
        blocks = _blocks_for(
            "WITH c1 AS (SELECT id FROM t1), c2 AS (SELECT id FROM t2) "
            "SELECT * FROM c1, c2;")[0]
        tables = {t.table for qb in blocks for t in qb.tables}
        self.assertEqual(tables, {"T1", "T2"})


class TestQueryBlockScoping(unittest.TestCase):
    def test_union_siblings_scoped_independently(self):
        blocks = _blocks_for("SELECT a FROM t1 x UNION SELECT b FROM t2 x;")[0]
        # both arms alias their own table to "X" -- must resolve independently
        by_table = {}
        for qb in blocks:
            for t in qb.tables:
                by_table[t.table] = qb
        self.assertIsNot(by_table["T1"], by_table["T2"])

    def test_subquery_in_predicate_does_not_leak_alias(self):
        sql = "SELECT * FROM t1 a WHERE a.x IN (SELECT y FROM t2 b WHERE b.z=1);"
        blocks = _blocks_for(sql)[0]
        idx_outer = sql.index("a.x")
        idx_inner = sql.index("b.z")
        self.assertEqual(ts.resolve_qualifier(blocks, idx_outer, "A"),
                         (ts.PLACEHOLDER_SCHEMA, "T1"))
        self.assertEqual(ts.resolve_qualifier(blocks, idx_inner, "B"),
                         (ts.PLACEHOLDER_SCHEMA, "T2"))
        # the outer alias "A" must not resolve inside the inner block's scope
        self.assertEqual(ts.resolve_qualifier(blocks, idx_inner, "A"),
                         (ts.PLACEHOLDER_SCHEMA, ts.PLACEHOLDER_TABLE))


class TestDerivedTable(unittest.TestCase):
    def test_inner_table_of_derived_table_is_found(self):
        # Regression guard for a real bug caught during development: the
        # first (buggy) single-pass design silently dropped this table.
        blocks = _blocks_for("SELECT t.col1 FROM (SELECT col1 FROM inner_t) t;")[0]
        tables = {t.table for qb in blocks for t in qb.tables}
        self.assertEqual(tables, {"INNER_T"})

    def test_sibling_after_derived_table_still_found(self):
        blocks = _blocks_for(
            "SELECT t.col1 FROM (SELECT col1 FROM inner_t) t, t2 b WHERE t2.x=1;")[0]
        tables = {t.table for qb in blocks for t in qb.tables}
        self.assertEqual(tables, {"INNER_T", "T2"})


class TestNonSelectStatements(unittest.TestCase):
    def test_update_target_table_and_alias(self):
        blocks = _blocks_for("UPDATE t1 a SET x=1 WHERE a.y=2;")[0]
        self.assertEqual(_tables(blocks), [(ts.PLACEHOLDER_SCHEMA, "T1", "A")])

    def test_insert_into_target_table(self):
        blocks = _blocks_for("INSERT INTO t1 (a,b) VALUES (1,2);")[0]
        self.assertEqual(_tables(blocks), [(ts.PLACEHOLDER_SCHEMA, "T1", "T1")])

    def test_delete_from_target_table(self):
        blocks = _blocks_for("DELETE FROM t1 a WHERE a.x=1;")[0]
        self.assertEqual(_tables(blocks), [(ts.PLACEHOLDER_SCHEMA, "T1", "A")])

    def test_insert_select_keeps_target_and_source_separate(self):
        blocks = _blocks_for("INSERT INTO t1 SELECT * FROM t2;")[0]
        by_table = {t.table: qb for qb in blocks for t in qb.tables}
        self.assertIn("T1", by_table)
        self.assertIn("T2", by_table)
        self.assertIsNot(by_table["T1"], by_table["T2"])


class TestResolveQualifier(unittest.TestCase):
    def test_none_qualifier_is_placeholder(self):
        blocks = _blocks_for("SELECT * FROM t1;")[0]
        self.assertEqual(ts.resolve_qualifier(blocks, 0, None),
                         (ts.PLACEHOLDER_SCHEMA, ts.PLACEHOLDER_TABLE))

    def test_unknown_qualifier_is_placeholder(self):
        blocks = _blocks_for("SELECT * FROM t1 a;")[0]
        self.assertEqual(ts.resolve_qualifier(blocks, 0, "Z"),
                         (ts.PLACEHOLDER_SCHEMA, ts.PLACEHOLDER_TABLE))

    def test_bare_table_name_also_usable_as_qualifier(self):
        # DB2 allows using the real table name as its own qualifier even
        # when no explicit alias is given.
        sql = "SELECT * FROM t1 WHERE t1.x=1;"
        blocks = _blocks_for(sql)[0]
        idx = sql.index("t1.x")
        self.assertEqual(ts.resolve_qualifier(blocks, idx, "T1"),
                         (ts.PLACEHOLDER_SCHEMA, "T1"))


class TestResolveQualifierCrashGuard(unittest.TestCase):
    def test_none_char_offset_does_not_crash(self):
        # Regression guard for a real crash: char_offset (a tree node's own
        # token position) wasn't guarded against None the way `qualifier`
        # and `qb.stop_char` already were, raising
        # "'<=' not supported between instances of 'int' and 'NoneType'"
        # on a heavily error-recovered tree (e.g. from a file with a lot
        # of non-SQL noise).
        qb = ts.QueryBlock(0)
        qb.stop_char = 100
        result = ts.resolve_qualifier([qb], None, "A")
        self.assertEqual(result, (ts.PLACEHOLDER_SCHEMA, ts.PLACEHOLDER_TABLE))


class TestScanTableListNeverLeaksNoneIndex(unittest.TestCase):
    """Regression guard for a second real crash, distinct from the
    resolve_qualifier one above: _scan_table_list's connector loop has
    three `break` statements that can all fire with its own local `i`
    already None (ran out of tokens via _skip_hidden mid-scan). That None
    used to leak straight through as the function's returned next_index,
    which _populate_table_lists assigns directly into its own loop index
    (`i = j2`) -- crashing the very next `while i < n` check with the
    exact same class of TypeError."""

    def test_from_list_running_to_end_of_derived_table(self):
        sql = "SELECT * FROM (SELECT * FROM t1 a JOIN t2 b ON a.x=b.y) sub;"
        blocks = _blocks_for(sql)[0]
        tables = {t.table for qb in blocks for t in qb.tables}
        self.assertEqual(tables, {"T1", "T2"})

    def test_from_list_running_to_end_of_chunk_no_trailing_semicolon(self):
        sql = "SELECT * FROM t1 a JOIN t2 b ON a.x=b.y"
        blocks = _blocks_for(sql)[0]
        tables = {t.table for qb in blocks for t in qb.tables}
        self.assertEqual(tables, {"T1", "T2"})

    def test_scan_table_list_never_returns_none_index_directly(self):
        # Direct unit check on the function itself: from_index deliberately
        # placed so every default-channel token is consumed by the single
        # entry, leaving nothing for _skip_hidden to find -- next_index
        # must be an int (len(tokens)), never None.
        sql = "SELECT * FROM t1"
        all_tokens, _ = lex_file(sql)
        from_idx = next(i for i, t in enumerate(all_tokens) if t.text.upper() == "T1")
        _entries, _connectors, next_index = ts._scan_table_list(all_tokens, from_idx, set())
        self.assertIsInstance(next_index, int)


class TestExtractTableRefsOnly(unittest.TestCase):
    def test_multi_statement_file(self):
        text = ("SELECT * FROM schema1.table1 a WHERE a.col1='1'; "
                "UPDATE t2 SET x=1; "
                "SELECT t.c FROM (SELECT c FROM inner_t) t;")
        refs = ts.extract_table_refs_only(text)
        tables = {(schema, table) for schema, table, _line in refs}
        self.assertEqual(tables, {("SCHEMA1", "TABLE1"), (ts.PLACEHOLDER_SCHEMA, "T2"),
                                  (ts.PLACEHOLDER_SCHEMA, "INNER_T")})


if __name__ == "__main__":
    unittest.main()
