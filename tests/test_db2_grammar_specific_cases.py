# -*- coding: utf-8 -*-
"""End-to-end regression tests for constructs specific to the Db2-grammar
migration -- as opposed to tests/test_scan.py, which is a direct port of
the original tool's own fixtures/assertions.

These exist because an earlier pass at documenting "what's resolved vs.
the original tool" asserted several of these were fixed based only on
isolated grammar-rule-level checks (tests/test_grammar_smoke.py), without
ever running them through the actual scan_file() pipeline -- and every
single one of them was silently broken end-to-end (see git history).
Fixing them surfaced two more real bugs (a hidden-token position landing
in statement_driver.py's tier race, and a missing paren-balance check in
supplementary_checks.py that a later fix -- recursive comment re-scanning
-- would otherwise have regressed). This file exists so none of that can
silently regress again without a test noticing.

Run:
    python -m unittest tests.test_db2_grammar_specific_cases
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src.scan import DEFAULT_COLUMNS, scan_file  # noqa: E402


def scan_text(content, columns=None):
    columns = columns or DEFAULT_COLUMNS
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False,
                                      encoding="utf-8") as f:
        f.write(content)
        path = f.name
    try:
        hits, suspects, _refs, _rel, _sbc, _fc, _bad = scan_file(path, columns, set())
        return hits, suspects
    finally:
        os.unlink(path)


class TestBareParenQuirkEndToEnd(unittest.TestCase):
    def test_bare_paren_literal_is_found(self):
        # No grammar path at all for this (see extractor_visitor.py's
        # docstring) -- must be caught by supplementary_checks.py's Tier 3.
        # Originally missed entirely: sql_statement()'s bare-identifier
        # over-acceptance consumed just "ACCT_ID" before Tier 3 ever got a
        # look, because the tier race only checked stream.tokens[pos]
        # directly without skipping a hidden-channel starting position.
        content = "SELECT * FROM CUSTOMER WHERE ACCT_ID ('0000001');\n"
        hits, suspects = scan_text(content)
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["column_name"], "ACCT_ID")
        self.assertEqual(hits[0]["operator"], "(")
        self.assertEqual(hits[0]["value"], "'0000001'")
        # the span excludes the wrapping '(' -- only the quoted payload
        start, end = hits[0]["start_offset"], hits[0]["end_offset"]
        self.assertEqual(content[start:end + 1], "'0000001'")


class TestDoubleQuotedLiteralEndToEnd(unittest.TestCase):
    def test_dq_literal_is_found(self):
        # DOUBLE_QUOTE_ID has no parser-level path either -- same Tier 3
        # dependency and same original bug as the bare-paren case.
        content = 'SELECT * FROM CUSTOMER WHERE ACCT_ID = "0000079";\n'
        hits, suspects = scan_text(content)
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["column_name"], "ACCT_ID")
        self.assertEqual(hits[0]["value"], '"0000079"')
        start, end = hits[0]["start_offset"], hits[0]["end_offset"]
        self.assertEqual(content[start:end + 1], '"0000079"')


class TestNestedParensInList(unittest.TestCase):
    def test_redundant_parens_around_in_list_items_are_unwrapped(self):
        # Each item in ACCT_ID IN (('0000001'), ('0000002')) parses as its
        # own ExpressionContext wrapping a single inner expression, not as
        # a plain Constant_Context directly -- as_literal() must unwrap it.
        content = "SELECT * FROM CUSTOMER WHERE ACCT_ID IN (('0000001'), ('0000002'));\n"
        hits, suspects = scan_text(content)
        self.assertEqual(suspects, [])
        self.assertEqual({h["value"] for h in hits}, {"'0000001'", "'0000002'"})
        self.assertTrue(all(h["column_name"] == "ACCT_ID" for h in hits))
        # each finding's span is the innermost literal only -- the
        # wrapping parens around each IN-list item are excluded
        for h in hits:
            start, end = h["start_offset"], h["end_offset"]
            self.assertEqual(content[start:end + 1], h["value"])


class TestSubqueryRedundantParens(unittest.TestCase):
    def test_subquery_wrapped_in_extra_parens_still_scopes_correctly(self):
        # CTRT_NO IN ((SELECT ...)) -- an extra, redundant paren layer
        # around the subquery. The inner comparison's own column must
        # still be found (if configured) and never attributed to the
        # outer CTRT_NO.
        hits, suspects = scan_text(
            "SELECT * FROM CUSTOMER WHERE CTRT_NO IN "
            "((SELECT CTRT_NO FROM T WHERE ACCT_ID = '02'));\n")
        self.assertEqual(suspects, [])
        self.assertNotIn("CTRT_NO", {h["column_name"] for h in hits})
        self.assertEqual({(h["column_name"], h["value"]) for h in hits},
                         {("ACCT_ID", "'02'")})


class TestNestedBlockComments(unittest.TestCase):
    def test_hit_inside_a_nested_comment_is_found(self):
        content = "/* outer /* ACCT_ID = '0000099' */ still outer */\nSELECT 1;\n"
        hits, suspects = scan_text(content)
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["value"], "'0000099'")
        self.assertEqual(hits[0]["in_comment"], "Y")
        self.assertEqual(hits[0]["line"], 1)
        # the offset-rebasing math (base_offset = tok.start + 2, composed
        # through one level of nesting) must land on the literal's exact
        # span in the *original* file's coordinate system, not the
        # re-lexed comment-inner-text one.
        start, end = hits[0]["start_offset"], hits[0]["end_offset"]
        self.assertEqual(content[start:end + 1], "'0000099'")

    def test_hit_inside_a_triple_nested_comment_is_found(self):
        content = "/* L1 /* L2 /* ACCT_ID = '0000042' */ L2 */ L1 */\nSELECT 1;\n"
        hits, suspects = scan_text(content)
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["value"], "'0000042'")
        self.assertEqual(hits[0]["in_comment"], "Y")
        # three levels of nested-offset composition (base_offset shifted
        # once per recursion level) must still resolve correctly
        start, end = hits[0]["start_offset"], hits[0]["end_offset"]
        self.assertEqual(content[start:end + 1], "'0000042'")

    def test_nested_comment_line_number_is_remapped_correctly(self):
        content = "/* outer1\n/* ACCT_ID = '0000055' */\nstill outer2 */\nSELECT 1;\n"
        hits, suspects = scan_text(content)
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["value"], "'0000055'")
        self.assertEqual(hits[0]["line"], 2)
        start, end = hits[0]["start_offset"], hits[0]["end_offset"]
        self.assertEqual(content[start:end + 1], "'0000055'")

    def test_malformed_paren_fragment_inside_nested_comment_is_not_a_false_hit(self):
        # This is the regression this whole file exists to prevent: making
        # comment re-scanning recursive (to catch the case above) initially
        # broke the original tool's core safety guarantee -- a truncated,
        # never-closed '(' inside a comment must never produce a finding,
        # even when nested. Requires the same paren-balance check that
        # protects the original malformed-fragment fixtures
        # (09_paren_list_boundary.sql, 13_comment_escape_recovery.sql).
        content = "/* outer /* ctrt_no in ('0000099' */ still outer */\nSELECT 1;\n"
        hits, suspects = scan_text(content)
        self.assertEqual(suspects, [])
        self.assertNotIn("CTRT_NO", {h["column_name"] for h in hits})


class TestFetchFirst(unittest.TestCase):
    def test_fetch_first_rows_only_does_not_lose_the_where_clause_hit(self):
        hits, suspects = scan_text(
            "SELECT * FROM CUSTOMER WHERE ACCT_ID = '0000001' FETCH FIRST 10 ROWS ONLY;\n")
        self.assertEqual(suspects, [])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["value"], "'0000001'")


class TestFunctionCallArgumentNotMisattributedEndToEnd(unittest.TestCase):
    """Real production false positive: CONCAT is a reserved
    operator-keyword token in this grammar (the infix `CONCAT`/`||`
    operator), not a plain ID, so `CONCAT(...)` has no function_invocation
    grammar path -- `RRNO LIKE CONCAT('%', '02291')` falls through to the
    Tier 3 token-scan fallback, whose paren-balance check used to grab the
    first literal found inside any nesting that eventually closed,
    misattributing the function's own argument ('%') to the outer LIKE.
    See tests/test_supplementary_checks.py::TestFunctionCallArgumentNotMisattributed
    for the unit-level regression; this is the full scan_file() pipeline
    version, including the originally-reported in-comment case."""

    def test_concat_argument_in_live_code_is_not_a_hit(self):
        hits, suspects = scan_text(
            "SELECT * FROM CUSTOMER WHERE rrno like concat('%', '02291');\n",
            columns=["RRNO"])
        self.assertEqual(suspects, [])
        self.assertEqual(hits, [])

    def test_concat_argument_in_a_comment_is_not_a_hit(self):
        # The exact real-world shape originally reported: a commented-out
        # condition using CONCAT, inside a parenthesized group.
        hits, suspects = scan_text(
            "SELECT * FROM CUSTOMER\n"
            "--and (rrno like concat('%', '02291')) ..\n"
            "WHERE 1=1;\n",
            columns=["RRNO"])
        self.assertEqual(suspects, [])
        self.assertNotIn("RRNO", {h["column_name"] for h in hits})
        self.assertFalse(any(h["value"] == "'%'" for h in hits))


if __name__ == "__main__":
    unittest.main()
