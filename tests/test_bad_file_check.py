# -*- coding: utf-8 -*-
"""Unit tests for bad_file_check.py's cheap, lex-only "is this real SQL"
heuristic -- the first line of defense in cli.py's bad_files.tsv
workflow (scan_file's own try/except around the real work is the second,
for whatever this cheap check doesn't catch).

Run:
    python -m unittest tests.test_bad_file_check
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial.detect.bad_file_check import check_file_quality  # noqa: E402
from metchurial.parsing.statement_driver import lex_file  # noqa: E402


def _check_reason(sql):
    """The full BadFileReason (or None) -- for tests asserting on the
    structured category/item fields, not just the prose message."""
    all_tokens, lexer_errors = lex_file(sql)
    return check_file_quality(all_tokens, lexer_errors)


def _check(sql):
    """Just the human-readable message, or None -- BadFileReason.__str__
    returns it too, but spelling it out keeps assertIn/assertIsNone calls
    below working against a plain str/None like before."""
    reason = _check_reason(sql)
    return reason.message if reason is not None else None


class TestDividerDetection(unittest.TestCase):
    def test_long_equals_divider_is_flagged(self):
        sql = "========================================\nSELECT * FROM t1;\n"
        reason = _check(sql)
        self.assertIsNotNone(reason)
        # The reason should echo back what was actually matched, not just
        # a bare count, so it's obvious at a glance what tripped it.
        self.assertIn("====", reason)

    def test_short_run_is_not_flagged(self):
        # A handful of repeated characters (e.g. "=="  from some odd
        # spacing) shouldn't trip this -- only long, clearly decorative
        # runs should.
        sql = "SELECT * FROM t1 WHERE x == 1;\n"
        self.assertIsNone(_check(sql))


class TestPunctuationRunIgnoresSwallowedText(unittest.TestCase):
    """A lexer error consumes source text without emitting a token for
    it, so punctuation that is actually far apart in the source -- e.g.
    sentence-ending periods separated by bare, untokenizable Korean prose
    -- must not look like a contiguous divider just because nothing sits
    between the periods in the filtered token list."""

    def test_korean_prose_periods_are_not_a_divider(self):
        sql = (
            "SELECT A1, A2, A3, A4, A5, A6, A7, A8, A9, A10\n"
            "FROM TABLE1\n"
            "WHERE COND1 = 1 AND COND2 = 2 AND COND3 = 3\n"
            "검토 완료. 배포 대기. 참고 요망. 문의 채널. 확인 필요. 승인 대기.\n"
            "SELECT A1, A2, A3, A4, A5, A6, A7, A8, A9, A10\n"
            "FROM TABLE1\n"
            "WHERE COND1 = 1 AND COND2 = 2 AND COND3 = 3\n"
        )
        self.assertIsNone(_check(sql))

    def test_korean_quoted_string_list_is_not_a_divider(self):
        sql = "SELECT * FROM T WHERE COL IN ('가','나','다','라','마','바','사')"
        self.assertIsNone(_check(sql))

    def test_spaced_out_divider_is_still_flagged(self):
        # A real divider can be spaced out ('- - - - - - -') without any
        # swallowed content between the dashes -- that's genuinely
        # contiguous source, so it must still be caught.
        sql = "- - - - - - -\nSELECT 1 FROM T1;\n"
        reason = _check(sql)
        self.assertIsNotNone(reason)
        self.assertIn("divider", reason)


class TestSingleTokenValuesAreNotFlagged(unittest.TestCase):
    """A single token that happens to be one long repeated character (a
    bare 3333333333333333, or the same thing quoted) must never be
    treated as a divider: it's exactly one resync point for the tiered
    driver regardless of its content (unlike '========', which is many
    separate single-char tokens -- the actual performance problem this
    precheck exists to defend against), and a masked/dummy/round-number
    numeric literal is completely ordinary, legitimate SQL data, quoted
    or bare."""

    def test_bare_repeated_digit_literal_in_a_real_predicate_is_not_flagged(self):
        sql = "SELECT * FROM T WHERE ACCT_NO = 3333333333333333"
        self.assertIsNone(_check(sql))

    def test_bare_repeated_digit_literal_in_values_list_is_not_flagged(self):
        sql = "INSERT INTO T (ACCT_NO) VALUES (3333333333333333)"
        self.assertIsNone(_check(sql))

    def test_quoted_repeated_digit_literal_is_not_flagged(self):
        sql = "SELECT * FROM T WHERE COL = '3333333333333333'"
        self.assertIsNone(_check(sql))

    def test_round_number_amount_is_not_flagged(self):
        sql = "SELECT * FROM T WHERE AMOUNT > 1000000000"
        self.assertIsNone(_check(sql))


class TestBadFileReasonStructuredFields(unittest.TestCase):
    """bad_files.tsv (io_utils.py) needs category/item, not just prose --
    lock in that check_file_quality actually populates them."""

    def test_repeated_char_run_reports_category_and_matched_item(self):
        sql = "========================================\nSELECT * FROM t1;\n"
        reason = _check_reason(sql)
        self.assertIsNotNone(reason)
        self.assertEqual(reason.category, "repeated-char-run")
        self.assertTrue(reason.item.startswith("===="))

    def test_lexer_error_ratio_reports_category_and_offending_text(self):
        sql = "이것은실제SQL이아닌설명입니다전혀다른내용입니다\nSELECT 1 FROM T1;"
        reason = _check_reason(sql)
        self.assertIsNotNone(reason)
        self.assertEqual(reason.category, "lexer-error-ratio")
        # item should be built from the actual characters the lexer
        # choked on, not left empty.
        self.assertTrue(reason.item)


class TestLexerErrorRatio(unittest.TestCase):
    def test_prose_heavy_file_is_flagged(self):
        sql = "이것은실제SQL이아닌설명입니다전혀다른내용입니다\nSELECT 1 FROM T1;"
        self.assertIsNotNone(_check(sql))

    def test_legitimate_korean_aliases_are_not_flagged(self):
        # A real, structurally valid, fairly large query (multi-CTE,
        # 3-way UNION ALL, nested CASE, JOINs) using bare Korean column
        # aliases extensively throughout (a genuine, common pattern --
        # see README's Known Limitations) must NOT be flagged just
        # because it lands in a moderate lexer-error ratio on its own.
        # A short, alias-dense one-liner isn't representative here (it
        # can look like ~35-100% error tokens purely from having too few
        # real SQL tokens to dilute the ratio against) -- this reuses the
        # actual fixture verified during development to land at ~7%.
        fixtures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
        path = os.path.join(fixtures_dir, "14_complex_multi_cte_query.sql")
        with open(path, encoding="utf-8") as f:
            sql = f.read()
        self.assertIsNone(_check(sql))


class TestNormalSqlPasses(unittest.TestCase):
    def test_ordinary_multi_statement_file(self):
        sql = ("SELECT * FROM t1 a JOIN t2 b ON a.id=b.id WHERE a.acct_id = '1';\n"
              "UPDATE t3 SET x = 1 WHERE y = 2;\n")
        self.assertIsNone(_check(sql))

    def test_empty_file(self):
        self.assertIsNone(_check(""))


class TestBadSqlFixture(unittest.TestCase):
    """15_bad_sql.sql: a realistic bad file (bracketed section markers,
    missing semicolons, numbered prose headers, a decorative divider,
    a truncated CTE) -- exercises the same heuristic as the rest of this
    file, but against real fixture content rather than a synthetic
    example, and locks in that this specific file stays flagged."""

    def test_is_flagged_bad(self):
        fixtures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
        path = os.path.join(fixtures_dir, "15_bad_sql.sql")
        with open(path, encoding="utf-8") as f:
            sql = f.read()
        reason = _check(sql)
        self.assertIsNotNone(reason)
        self.assertIn("divider", reason)


if __name__ == "__main__":
    unittest.main()
