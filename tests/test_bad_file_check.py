# -*- coding: utf-8 -*-
"""Unit tests for bad_file_check.py's cheap, lex-only "is this real SQL"
heuristic -- the first line of defense in cli.py's bad_files.txt
workflow (scan_file's own try/except around the real work is the second,
for whatever this cheap check doesn't catch).

Run:
    python -m unittest tests.test_bad_file_check
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src.detect.bad_file_check import check_file_quality  # noqa: E402
from src.parsing.statement_driver import lex_file  # noqa: E402


def _check(sql):
    all_tokens, lexer_errors = lex_file(sql)
    return check_file_quality(all_tokens, lexer_errors)


class TestDividerDetection(unittest.TestCase):
    def test_long_equals_divider_is_flagged(self):
        sql = "========================================\nSELECT * FROM t1;\n"
        self.assertIsNotNone(_check(sql))

    def test_short_run_is_not_flagged(self):
        # A handful of repeated characters (e.g. "=="  from some odd
        # spacing) shouldn't trip this -- only long, clearly decorative
        # runs should.
        sql = "SELECT * FROM t1 WHERE x == 1;\n"
        self.assertIsNone(_check(sql))


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
