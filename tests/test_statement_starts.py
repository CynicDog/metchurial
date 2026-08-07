# -*- coding: utf-8 -*-
"""Unit tests for parsing/statement_starts.py -- statement boundaries
inferred where no top-level ';' is present.

A top-level ';' is DB2 syntax for ending a statement but is not reliably
present: real .sql files routinely hold several standalone queries with no
terminator at all, because the author highlights the one they want and runs
the selection. Without inference such a file arrives as one chunk and every
consumer fuses N unrelated queries into a single statement.

These are also the suite's first direct assertions on chunk boundaries --
chunk_ranges was previously only exercised indirectly. Cases are ordered by
how common they are: the plain no-CTE/no-isolation-clause/no-';' file first,
then one case per guard.

Run:
    python -m unittest tests.test_statement_starts
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial.parsing.statement_driver import chunk_ranges, lex_file  # noqa: E402
from metchurial.split.select_blocks import chunk_source_text  # noqa: E402


def _chunks(sql):
    """The source text of each statement chunk chunk_ranges finds.

    Whitespace-only chunks are dropped: a file-final ';' leaves a trailing
    range holding just the newline after it, which chunk_ranges has always
    emitted and which has nothing to do with boundary inference. Inferred
    boundaries never produce one -- a chunk always opens on the statement
    keyword that started it."""
    all_tokens, _ = lex_file(sql)
    texts = [chunk_source_text(sql, all_tokens, s, e)
             for s, e in chunk_ranges(all_tokens)]
    return [t for t in texts if t.strip()]


class TestPlainUnpunctuatedFile(unittest.TestCase):
    """The common case: bare SELECTs, no ';', no CTE, no isolation clause."""

    def test_two_bare_selects_split(self):
        chunks = _chunks("SELECT a FROM t1\nWHERE x = 1\n\nSELECT b FROM t2\n")
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith("SELECT a"))
        self.assertTrue(chunks[1].startswith("SELECT b"))
        # The first chunk must not swallow any of the second.
        self.assertNotIn("t2", chunks[0])

    def test_three_bare_selects_split(self):
        self.assertEqual(
            len(_chunks("SELECT a FROM t1\n\nSELECT b FROM t2\n\nSELECT c FROM t3\n")), 3)

    def test_single_query_is_one_chunk(self):
        self.assertEqual(len(_chunks("SELECT a FROM t1\nWHERE x = 1\n")), 1)

    def test_multiline_clauses_never_cut_a_statement(self):
        """FROM/WHERE/GROUP BY/HAVING/ORDER BY/FETCH FIRST each open a line
        in normal DB2 formatting; none of them is a statement keyword."""
        self.assertEqual(len(_chunks(
            "SELECT a, b\n"
            "FROM   t\n"
            "WHERE  x = 1\n"
            "GROUP BY a\n"
            "HAVING COUNT(*) > 1\n"
            "ORDER BY 1\n"
            "FETCH FIRST 10 ROWS ONLY\n")), 1)

    def test_comment_header_travels_with_its_own_query(self):
        """A `-- n. description` header above a query must land in that
        query's chunk, not trail the previous one -- same as where a ';'
        leaves it."""
        chunks = _chunks("-- 1. first\nSELECT a FROM t1\n\n-- 2. second\nSELECT b FROM t2\n")
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith("-- 1. first"))
        self.assertTrue(chunks[1].startswith("-- 2. second"))
        self.assertNotIn("-- 2.", chunks[0])

    def test_derived_table_then_next_query(self):
        chunks = _chunks("SELECT a FROM (\n  SELECT b FROM t\n) x\n\nSELECT c FROM u\n")
        self.assertEqual(len(chunks), 2)


class TestSemicolonsStillWin(unittest.TestCase):
    def test_punctuated_file_is_unaffected(self):
        self.assertEqual(_chunks("SELECT * FROM t1;\nSELECT * FROM t2;\n"),
                         ["SELECT * FROM t1;", "SELECT * FROM t2;"])

    def test_half_punctuated_file(self):
        self.assertEqual(len(_chunks(
            "SELECT a FROM t1;\nSELECT b FROM t2\n\nSELECT c FROM t3\n")), 3)


class TestLexerResolvesQuoting(unittest.TestCase):
    """A keyword or ';' inside a literal/comment/quoted identifier is part
    of a single token and can never be seen as a boundary."""

    def test_semicolon_inside_string_literal(self):
        chunks = _chunks("SELECT ';' FROM t1\n\nSELECT b FROM t2\n")
        self.assertEqual(len(chunks), 2)
        self.assertIn("';'", chunks[0])

    def test_select_inside_line_comment(self):
        self.assertEqual(len(_chunks("-- SELECT nope FROM x\nSELECT a FROM t1\n")), 1)

    def test_select_inside_block_comment(self):
        self.assertEqual(len(_chunks(
            "SELECT a FROM t1\n/*\nSELECT nope FROM x\n*/\nWHERE y = 1\n")), 1)

    def test_keyword_inside_quoted_identifier(self):
        self.assertEqual(len(_chunks('SELECT a FROM t1\nWHERE "SELECT" = 1\n')), 1)


class TestGuards(unittest.TestCase):
    def test_g1_union_is_not_a_boundary(self):
        self.assertEqual(len(_chunks("SELECT a FROM t1\nUNION\nSELECT b FROM t2\n")), 1)

    def test_g1_union_all_is_not_a_boundary(self):
        self.assertEqual(len(_chunks("SELECT a FROM t1\nUNION ALL\nSELECT b FROM t2\n")), 1)

    def test_g1_except_and_intersect(self):
        self.assertEqual(len(_chunks("SELECT a FROM t1\nEXCEPT\nSELECT b FROM t2\n")), 1)
        self.assertEqual(len(_chunks("SELECT a FROM t1\nINTERSECT\nSELECT b FROM t2\n")), 1)

    def test_depth_guards_subquery(self):
        self.assertEqual(len(_chunks(
            "SELECT a FROM t1\nWHERE x IN (\n  SELECT y FROM t2\n)\n")), 1)
        self.assertEqual(len(_chunks(
            "SELECT a FROM t1\nWHERE EXISTS (\n  SELECT 1 FROM t2\n)\n")), 1)

    def test_g2_create_view_as(self):
        self.assertEqual(len(_chunks("CREATE VIEW v AS\nSELECT a FROM t\n")), 1)

    def test_g2_declare_cursor_for(self):
        self.assertEqual(len(_chunks("DECLARE c CURSOR FOR\nSELECT a FROM t\n")), 1)

    def test_g2_merge_when_matched_then_update(self):
        self.assertEqual(len(_chunks(
            "MERGE INTO t USING s ON t.id = s.id\n"
            "WHEN MATCHED THEN\n"
            "UPDATE SET c = 1\n")), 1)

    def test_g3_insert_select_stays_whole(self):
        self.assertEqual(len(_chunks("INSERT INTO t\nSELECT * FROM u\n")), 1)

    def test_g3_second_select_after_insert_select_is_a_boundary(self):
        chunks = _chunks("INSERT INTO t\nSELECT * FROM u\n\nSELECT b FROM t2\n")
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith("INSERT"))
        self.assertTrue(chunks[1].startswith("SELECT b"))

    def test_g4_cte_prologue_select_is_not_a_boundary(self):
        self.assertEqual(len(_chunks(
            "WITH a AS (SELECT 1 FROM x)\nSELECT * FROM a\n")), 1)

    def test_g4_two_cte_queries_split(self):
        chunks = _chunks("WITH a AS (SELECT 1 FROM x)\nSELECT * FROM a\n\n"
                         "WITH b AS (SELECT 2 FROM y)\nSELECT * FROM b\n")
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[1].startswith("WITH b"))

    def test_g4_multi_cte_list_is_one_chunk(self):
        self.assertEqual(len(_chunks(
            "WITH a AS (SELECT 1 FROM x),\n"
            "     b AS (SELECT 2 FROM y)\n"
            "SELECT * FROM a JOIN b ON a.c = b.c\n")), 1)

    def test_g5_isolation_clause_with_ur_is_not_a_statement_start(self):
        """The load-bearing false-positive guard: DB2's isolation clause
        puts a bare depth-0 WITH *inside* a SELECT. Two queries here, not
        three."""
        chunks = _chunks("SELECT a FROM t1\nWITH UR\n\nSELECT b FROM t2\n")
        self.assertEqual(len(chunks), 2)
        self.assertIn("WITH UR", chunks[0])

    def test_g5_other_isolation_levels(self):
        for level in ("RS", "RR", "CS"):
            with self.subTest(level=level):
                self.assertEqual(len(_chunks(
                    "SELECT a FROM t1\nWITH {}\n\nSELECT b FROM t2\n".format(level))), 2)

    def test_g6_update_set_stays_whole(self):
        self.assertEqual(len(_chunks("UPDATE t\nSET c = 1\nWHERE x = 2\n")), 1)

    def test_g6_set_after_a_select_is_a_boundary(self):
        self.assertEqual(len(_chunks(
            "SELECT a FROM t1\n\nSET CURRENT SCHEMA = 'X'\n")), 2)


class TestDocumentedLimitations(unittest.TestCase):
    def test_two_statements_on_one_line_are_not_split(self):
        """Deliberate: the line-start requirement buys precision at the
        cost of this case. Highlight-and-run workflows are line-oriented."""
        self.assertEqual(len(_chunks("SELECT a FROM t SELECT b FROM u\n")), 1)

    def test_unbalanced_open_paren_suppresses_later_boundaries(self):
        """Pre-existing in chunk_ranges' ';' handling too; such files
        already trip bad_file_check's lexer-error-ratio gate."""
        self.assertEqual(len(_chunks("SELECT a FROM t1 WHERE x IN (1, 2\n\nSELECT b FROM t2\n")), 1)

    def test_unmatched_close_paren_does_not_mask_later_boundaries(self):
        """Depth is clamped at 0, so a stray ')' left in live code can't
        drive tracking negative (fixture 09_paren_list_boundary.sql)."""
        self.assertEqual(len(_chunks("SELECT a FROM t1)\n\nSELECT b FROM t2\n")), 2)


class TestInferredBoundaryCount(unittest.TestCase):
    def test_counts_only_non_semicolon_boundaries(self):
        from metchurial.detect.supplementary_checks import make_token_scan_fallback
        from metchurial.detect.extractor_visitor import ExtractorVisitor
        from metchurial.models.parse_stats import ParseStats
        from metchurial.parsing.statement_driver import parse_file

        def noop(col, op, val, line, so, eo):
            pass

        for sql, expected in (
                ("SELECT a FROM t1;\nSELECT b FROM t2;\n", 0),
                ("SELECT a FROM t1\n\nSELECT b FROM t2\n", 1),
                ("SELECT a FROM t1\n\nSELECT b FROM t2\n\nSELECT c FROM t3\n", 2),
                # One real ';' plus one inferred boundary.
                ("SELECT a FROM t1;\nSELECT b FROM t2\n\nSELECT c FROM t3\n", 1),
        ):
            with self.subTest(sql=sql):
                stats = ParseStats()
                parse_file(sql, ExtractorVisitor(["ACCT_ID"], noop),
                           make_token_scan_fallback(["ACCT_ID"], noop), stats=stats)
                self.assertEqual(stats.inferred_boundaries, expected)


class TestGuardModel(unittest.TestCase):
    """models/statement_boundary.py enumerates the guards as data. These
    tests keep that model from drifting into stale documentation: every
    guard's own `example` is run through the real splitter and must both
    stay one statement and actually trip the guard that documents it."""

    def test_ids_and_names_are_unique(self):
        from metchurial.models.statement_boundary import GUARDS

        ids = [g.guard_id for g in GUARDS]
        names = [g.name for g in GUARDS]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(len(set(names)), len(names))

    def test_every_prev_token_name_resolves_against_the_lexer(self):
        """models/ is stdlib-only, so prev_tokens are token *names*. A
        name the lexer doesn't define would silently never match."""
        from metchurial._generated.Db2Lexer import Db2Lexer
        from metchurial.models.statement_boundary import GUARDS

        for guard in GUARDS:
            for name in guard.prev_tokens:
                with self.subTest(guard=guard.guard_id, token=name):
                    self.assertTrue(hasattr(Db2Lexer, name))

    def test_each_guard_example_stays_one_statement(self):
        from metchurial.models.statement_boundary import GUARDS

        for guard in GUARDS:
            with self.subTest(guard=guard.guard_id):
                self.assertEqual(
                    len(_chunks(guard.example)), 1,
                    "{} ({}) example was split apart".format(guard.guard_id, guard.name))

    def test_each_guard_example_actually_trips_that_guard(self):
        """The anti-drift check: without this, an example could stay one
        statement for some unrelated reason and the guard could be dead
        code."""
        from metchurial.models.statement_boundary import GUARDS
        from metchurial.parsing.statement_driver import chunk_ranges, lex_file

        for guard in GUARDS:
            with self.subTest(guard=guard.guard_id):
                hits = {}
                all_tokens, _ = lex_file(guard.example)
                chunk_ranges(all_tokens, guard_hits=hits)
                self.assertIn(guard.guard_id, hits,
                              "{} never fired on its own example; fired: {}".format(
                                  guard.guard_id, sorted(hits)))

    def test_guard_hits_are_recorded_on_parse_stats(self):
        from metchurial import scan_file
        from metchurial.models.options import ScanOptions

        result = scan_file(TestUnpunctuatedFixture.FIXTURE, ScanOptions())
        # The fixture carries a UNION ALL (G1) and a WITH UR (G5).
        self.assertGreaterEqual(result.parse_stats.guard_hits.get("G1", 0), 1)
        self.assertGreaterEqual(result.parse_stats.guard_hits.get("G5", 0), 1)

    def test_a_punctuated_file_trips_no_guard(self):
        from metchurial.parsing.statement_driver import chunk_ranges, lex_file

        hits = {}
        all_tokens, _ = lex_file("SELECT * FROM TBACCT;\nSELECT * FROM TBSTAT;\n")
        chunk_ranges(all_tokens, guard_hits=hits)
        self.assertEqual(hits, {})


class TestUnpunctuatedFixture(unittest.TestCase):
    """End-to-end over tests/fixtures/40_no_semicolon_statements.sql: six
    standalone queries, not one ';' in the file."""

    FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "fixtures", "40_no_semicolon_statements.sql")

    def _text(self):
        with open(self.FIXTURE, encoding="utf-8") as f:
            return f.read()

    def test_six_statements_and_six_select_blocks(self):
        from metchurial.split.select_blocks import select_block_ranges

        text = self._text()
        self.assertNotIn(";", text)
        all_tokens, lexer_errors = lex_file(text)
        ranges = chunk_ranges(all_tokens)
        self.assertEqual(len(ranges), 6)
        self.assertEqual(len(select_block_ranges(all_tokens, ranges)), 6)
        self.assertEqual(lexer_errors, [])

    def test_each_numbered_header_stays_with_its_own_query(self):
        """Each `-- n.` header must land in its own query's chunk, not
        trail the previous one. Chunk 1 also carries the file's banner,
        which sits above it, so this checks containment rather than a
        prefix."""
        chunks = _chunks(self._text())
        self.assertEqual(len(chunks), 6)
        for i, chunk in enumerate(chunks, 1):
            self.assertIn("-- {}.".format(i), chunk)
            self.assertNotIn("-- {}.".format(i + 1), chunk)

    def test_metadata_sees_six_distinct_queries_not_one(self):
        """The conflation this fixes: without boundary inference the whole
        file is one chunk and collapses to a single identity row with one
        merged table set."""
        from metchurial import scan_file
        from metchurial.models.options import ScanOptions

        result = scan_file(self.FIXTURE, ScanOptions(extract_query_identity=True))
        self.assertEqual(len(result.identity_rows), 6)

    def test_split_selects_writes_one_file_per_query(self):
        """ScanOptions(split_selects=True) rewrites the tree -- it writes
        the per-block files and deletes the original -- so this runs
        against a temp copy, never the fixture in the repo."""
        import shutil
        import tempfile

        from metchurial import scan_file
        from metchurial.models.options import ScanOptions

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, os.path.basename(self.FIXTURE))
            shutil.copy(self.FIXTURE, path)

            result = scan_file(path, ScanOptions(split_selects=True))
            self.assertEqual(result.select_block_count, 6)
            self.assertEqual(result.parse_stats.inferred_boundaries, 5)

            self.assertFalse(os.path.exists(path), "original should be deleted")
            written = sorted(os.listdir(tmp))
            self.assertEqual(len(written), 6)
            for i, name in enumerate(written, 1):
                with open(os.path.join(tmp, name), encoding="utf-8") as f:
                    body = f.read()
                # Each split file holds exactly its own numbered query --
                # file 1 additionally carries the fixture's banner, which
                # sits above the first statement.
                self.assertIn("-- {}.".format(i), body)
                self.assertNotIn("-- {}.".format(i + 1), body)
                self.assertIn("SELECT", body)


if __name__ == "__main__":
    unittest.main()
