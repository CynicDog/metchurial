# -*- coding: utf-8 -*-
"""End-to-end regression tests for the three grammar-level parse-path
fixes tracked in GitHub issue #4 (ANSI JOIN...ON/USING, CTE bodies, and
zero-argument function calls) -- see vendor/grammars-v4/Db2Parser.g4's
table_reference/common_table_expression/function_invocation rules and
docs/PROVENANCE.md.

Unlike tests/test_grammar_smoke.py (isolated parser-rule checks) and
tests/test_db2_grammar_specific_cases.py (still-open grammar gaps), this
file runs full, realistic multi-table fixtures through the actual
scan_file() pipeline to prove the fix holds up end-to-end, not just at
the grammar-rule level -- detection, table/function extraction, and JOIN
relationship extraction all have to agree the statement parsed as one
clean tree.

Run:
    python -m unittest tests.test_grammar_fix_regression
"""

import os
import sys
import unittest

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src import scan as scanner  # noqa: E402
from src.detect.statement_driver import chunk_ranges, lex_file  # noqa: E402
from src.split.select_blocks import select_block_ranges  # noqa: E402


def _scan(filename, **kwargs):
    path = os.path.join(FIXTURES_DIR, filename)
    return scanner.scan_file(path, scanner.DEFAULT_COLUMNS, set(), **kwargs)


class TestAnsiJoinChain(unittest.TestCase):
    """17_ansi_join_chain.sql: INNER/LEFT OUTER/plain JOIN...USING/CROSS
    JOIN in one FROM clause -- previously table_reference had no parse
    path for any of these beyond the first table."""

    def test_hit_still_found_inside_a_join_heavy_statement(self):
        hits, suspects, _refs, _rel, _sbc, _fc, bad = _scan("17_ansi_join_chain.sql")
        self.assertIsNone(bad)
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["column_name"], "ACCT_ID")
        self.assertEqual(hits[0]["value"], "'1234567'")

    def test_every_joined_table_is_discovered(self):
        _hits, _suspects, refs, _rel, _sbc, _fc, _bad = _scan(
            "17_ansi_join_chain.sql", extract_table_refs=True)
        tables = {r["table"] for r in refs if r["kind"] == "table"}
        self.assertEqual(tables, {"TBACCT", "TBCTRT", "TBSTAT", "TBSAMPLE001", "TBCODE"})

    def test_join_edges_for_inner_outer_and_cross_all_recorded(self):
        _hits, _suspects, _refs, rel, _sbc, _fc, _bad = _scan(
            "17_ansi_join_chain.sql", extract_relations=True)
        join_types = sorted(edge["join_type"] for edge in rel)
        self.assertEqual(join_types, ["CROSS", "INNER", "JOIN", "LEFT"])


class TestCteWithAnsiJoin(unittest.TestCase):
    """18_cte_with_ansi_join.sql: a CTE whose own body is a JOIN,
    consumed by an outer ANSI JOIN -- previously the CTE body would be
    independently re-surfaced as its own standalone top-level SELECT by
    the tiered driver's fallback, and the outer JOIN had no parse path
    either."""

    def test_hit_found_and_cte_name_excluded_from_real_tables(self):
        hits, suspects, refs, _rel, _sbc, _fc, bad = _scan(
            "18_cte_with_ansi_join.sql", extract_table_refs=True)
        self.assertIsNone(bad)
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["value"], "'7654321'")
        tables = {r["table"] for r in refs if r["kind"] == "table"}
        self.assertEqual(tables, {"TBACCT", "TBSTAT", "TBCTRT"})
        self.assertNotIn("ACTIVE_ACCT", tables)

    def test_parses_as_one_statement_not_two(self):
        path = os.path.join(FIXTURES_DIR, "18_cte_with_ansi_join.sql")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        all_tokens, _lexer_errors = lex_file(text)
        ranges = chunk_ranges(all_tokens)
        self.assertEqual(len(select_block_ranges(all_tokens, ranges)), 1)


class TestZeroArgumentFunctionFixture(unittest.TestCase):
    """19_zero_argument_functions.sql: NOW() in both the SELECT list and
    the WHERE clause -- previously function_invocation's mandatory
    arg_list gave zero-arg calls no parse path at all."""

    def test_hit_found_alongside_zero_arg_calls(self):
        hits, suspects, _refs, _rel, _sbc, _fc, bad = _scan("19_zero_argument_functions.sql")
        self.assertIsNone(bad)
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["value"], "'1112223'")

    def test_both_now_calls_captured(self):
        _hits, _suspects, _refs, _rel, _sbc, fc, _bad = _scan(
            "19_zero_argument_functions.sql", extract_functions=True)
        now_calls = [f for f in fc if f["function"] == "NOW"]
        self.assertEqual(len(now_calls), 2)
        self.assertTrue(all(f["parameters"] == "" for f in now_calls))


if __name__ == "__main__":
    unittest.main()
