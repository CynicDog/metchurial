# -*- coding: utf-8 -*-
"""Unit tests for supplementary_checks.py's Tier 3 token-scan fallback.

Pins down a real false-positive bug caught from production SQL: when the
structural parser fails somewhere nearby (forcing Tier 3 to grind token by
token) and this fallback gets raced at a bare, unqualified sensitive-column
token that's actually one side of a column-to-column comparison
(`a.item_no = b.item_no`), its old unbounded lookahead would walk straight
through the `AND` into a completely unrelated *second* comparison
(`item_flag = 'X'`) and misattribute that literal to the original
column, with a garbled "operator" string that's really a concatenation of
every token in between (e.g. `= B . ITEM_NO AND ITEM_FLAG =`).

Run:
    python -m unittest tests.test_supplementary_checks
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from antlr4 import InputStream, CommonTokenStream  # noqa: E402
from Db2Lexer import Db2Lexer  # noqa: E402
from src.detect.supplementary_checks import make_token_scan_fallback  # noqa: E402


def _stream(sql):
    lexer = Db2Lexer(InputStream(sql))
    stream = CommonTokenStream(lexer)
    stream.fill()
    return stream


def _find(stream, text):
    for i, t in enumerate(stream.tokens):
        if t.text.upper() == text.upper():
            return i
    raise ValueError("token not found: " + text)


def _run_fallback(sql, columns, anchor_text):
    results = []
    stream = _stream(sql)
    fallback = make_token_scan_fallback(columns, lambda *a: results.append(a))
    pos = _find(stream, anchor_text)
    consumed, commit = fallback(stream, pos)
    if commit is not None:
        commit()
    return consumed, results


class TestNoCrossComparisonFalsePositive(unittest.TestCase):
    def test_column_to_column_comparison_is_not_a_hit(self):
        # a.item_no = b.item_no is a column-to-column comparison (neither
        # side is a literal) -- must never match at all, regardless of
        # what follows later in the same predicate.
        consumed, results = _run_fallback(
            "a.item_no = b.item_no and item_flag = '01';",
            ["ITEM_NO", "ITEM_FLAG"], "item_no")
        self.assertEqual(consumed, 0)
        self.assertEqual(results, [])

    def test_unrelated_later_literal_not_misattributed(self):
        consumed, results = _run_fallback(
            "g.col1 = k.col1 and col_flag = '01';",
            ["COL1", "COL_FLAG"], "col1")
        self.assertEqual(consumed, 0)
        self.assertEqual(results, [])

    def test_or_also_stops_the_scan(self):
        consumed, results = _run_fallback(
            "a.item_no = b.item_no or item_flag = '01';",
            ["ITEM_NO", "ITEM_FLAG"], "item_no")
        self.assertEqual(consumed, 0)
        self.assertEqual(results, [])


class TestFunctionCallArgumentNotMisattributed(unittest.TestCase):
    """Real false-positive bug: CONCAT lexes as its own reserved
    operator-keyword token in this grammar (used for the infix `CONCAT`/
    `||` concatenation operator), not a plain ID -- so `CONCAT(...)` has
    no function_invocation grammar path at all, and a predicate like
    `RRNO LIKE CONCAT('%', '02291')` falls all the way through to this
    Tier 3 fallback. Before the fix, the fallback's paren-balance check
    couldn't tell "a paren belonging to a function call's own argument
    list" apart from the two shapes it's actually meant to handle (bare
    '(' before a literal, or a literal re-grouped in redundant parens) --
    it just grabbed the first literal token found inside any nesting that
    eventually closed, misattributing the function's first *argument*
    ('%') to the outer LIKE as if it were the real comparison value. A
    function's return value being compared is never a hardcoded literal
    (the structural path already agrees: when a function call *does*
    parse cleanly, as_literal() correctly returns None for it -- see
    extractor_visitor.py -- producing no finding at all)."""

    def test_literal_inside_an_unparsed_function_calls_arguments_is_not_a_hit(self):
        consumed, results = _run_fallback(
            "rrno like concat('%', '02291');", ["RRNO"], "rrno")
        self.assertEqual(consumed, 0)
        self.assertEqual(results, [])

    def test_literal_inside_an_unparsed_function_calls_arguments_inside_parens_is_not_a_hit(self):
        consumed, results = _run_fallback(
            "(rrno like concat('%', '02291'))", ["RRNO"], "rrno")
        self.assertEqual(consumed, 0)
        self.assertEqual(results, [])

    def test_bare_paren_quirk_still_works_alongside_the_new_guard(self):
        # Regression guard for the fix itself: a '(' immediately after the
        # anchor column's own token (no intervening identifier) is still
        # the legitimate bare-paren quirk, not a function call.
        sql = "ACCT_ID ('0000001');"
        consumed, results = _run_fallback(sql, ["ACCT_ID"], "ACCT_ID")
        self.assertGreater(consumed, 0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][:3], ("ACCT_ID", "(", "'0000001'"))


class TestIntendedCasesStillWork(unittest.TestCase):
    def test_bare_paren_before_literal(self):
        sql = "ACCT_ID ('0000001');"
        consumed, results = _run_fallback(sql, ["ACCT_ID"], "ACCT_ID")
        self.assertGreater(consumed, 0)
        self.assertEqual(len(results), 1)
        name, operator, value, line, start, end = results[0]
        self.assertEqual((name, operator, value, line), ("ACCT_ID", "(", "'0000001'", 1))
        # start/end are the literal's own 0-based inclusive-inclusive
        # character span in the original source -- required for masking
        # to locate/replace exactly this span.
        self.assertEqual(sql[start:end + 1], "'0000001'")

    def test_double_quoted_literal(self):
        sql = 'ACCT_ID = "0000079";'
        consumed, results = _run_fallback(sql, ["ACCT_ID"], "ACCT_ID")
        self.assertGreater(consumed, 0)
        self.assertEqual(len(results), 1)
        name, operator, value, line, start, end = results[0]
        self.assertEqual((name, operator, value, line), ("ACCT_ID", "=", '"0000079"', 1))
        self.assertEqual(sql[start:end + 1], '"0000079"')


if __name__ == "__main__":
    unittest.main()
