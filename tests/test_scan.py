# -*- coding: utf-8 -*-
"""Ported from ../metchurial/tests/test_scan.py -- same assertions, same
fixtures, run against the new ANTLR-based scan.py instead of the original
regex engine. This file is the acceptance bar for the migration: parity
with the original tool's tested behavior.

Run:
    python -m unittest tests.test_scan
"""

import os
import shutil
import sys
import tempfile
import unittest

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src import mask  # noqa: E402
from src import scan as scanner  # noqa: E402
from src.split.select_blocks import select_block_ranges  # noqa: E402
from src.parsing.statement_driver import chunk_ranges, lex_file  # noqa: E402


def scan(filename, stopwords=None, known_names=None):
    path = os.path.join(FIXTURES_DIR, filename)
    result = scanner.scan_file(
        path, scanner.DEFAULT_COLUMNS, stopwords or set(), known_names or set())
    return result.findings, result.name_candidates


def scan_text(text, stopwords=None, known_names=None):
    """For a one-off assertion that doesn't warrant its own fixture file
    (and, unlike scan(), doesn't perturb tests/fixtures/'s directory-wide
    file count, see TestTxtExtension below)."""
    fd, path = tempfile.mkstemp(suffix=".sql")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        result = scanner.scan_file(
            path, scanner.DEFAULT_COLUMNS, stopwords or set(), known_names or set())
        return result.findings, result.name_candidates
    finally:
        os.unlink(path)


class TestBasicHit(unittest.TestCase):
    def test_simple_equals(self):
        hits, name_candidates = scan("01_basic_hit.sql")
        self.assertEqual(len(name_candidates), 0)
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual(h.severity, "FINDING")
        self.assertEqual(h.column_name, "ACCT_ID")
        self.assertEqual(h.operator, "=")
        self.assertEqual(h.value, "'0000001'")
        self.assertEqual(h.in_comment, "N")
        self.assertEqual(h.line, 3)


class TestOperators(unittest.TestCase):
    def test_operator_coverage(self):
        hits, name_candidates = scan("02_operators.sql")
        self.assertEqual(len(name_candidates), 0)
        self.assertEqual(len(hits), 8)
        self.assertTrue(all(h.severity == "FINDING" for h in hits))

        ops = [h.operator for h in hits]
        values = set(h.value for h in hits)

        # no-space equals
        self.assertIn("=", ops)
        self.assertIn("'0000002'", values)

        # IN(...) exploded into one row per literal
        in_hits = [h for h in hits if h.operator == "IN"]
        self.assertEqual(len(in_hits), 3)
        self.assertEqual({h.value for h in in_hits},
                         {"'1000001'", "'1000002'", "'1000003'"})

        # BETWEEN ... AND ... exploded into two rows
        between_hits = [h for h in hits if h.operator == "BETWEEN"]
        self.assertEqual(len(between_hits), 2)
        self.assertEqual({h.value for h in between_hits},
                         {"'0000010'", "'0000099'"})

        # reversed literal-first comparison
        reversed_hits = [h for h in hits if h.value == "'0000123'"]
        self.assertEqual(len(reversed_hits), 1)
        self.assertEqual(reversed_hits[0].column_name, "ACCT_ID")
        self.assertEqual(reversed_hits[0].operator, "=")

        # <>
        self.assertIn("<>", ops)
        self.assertIn("'0000005'", values)


class TestMultiline(unittest.TestCase):
    def test_split_across_lines(self):
        hits, name_candidates = scan("03_multiline.sql")
        self.assertEqual(len(name_candidates), 0)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].value, "'0000030'")
        self.assertEqual(hits[0].line, 3)
        self.assertEqual(hits[0].in_comment, "N")
        # offset-based, so the operator and literal sitting on different
        # source lines doesn't matter -- the span still slices back to
        # exactly the literal text (needed for --mask-literals).
        path = os.path.join(FIXTURES_DIR, "03_multiline.sql")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        start, end = hits[0].start_offset, hits[0].end_offset
        self.assertEqual(text[start:end + 1], "'0000030'")


class TestComments(unittest.TestCase):
    def test_comment_tagging(self):
        hits, name_candidates = scan("04_comments.sql")
        self.assertEqual(len(name_candidates), 0)
        self.assertEqual(len(hits), 3)

        by_value = {h.value: h for h in hits}
        self.assertEqual(set(by_value), {"'0000040'", "'0000041'", "'0000042'"})

        self.assertEqual(by_value["'0000040'"].severity, "FINDING")
        self.assertEqual(by_value["'0000040'"].in_comment, "Y")

        self.assertEqual(by_value["'0000041'"].severity, "FINDING")
        self.assertEqual(by_value["'0000041'"].in_comment, "Y")
        self.assertEqual(by_value["'0000041'"].line, 6)

        self.assertEqual(by_value["'0000042'"].severity, "FINDING")
        self.assertEqual(by_value["'0000042'"].in_comment, "N")


class TestKoreanNames(unittest.TestCase):
    def test_without_known_names_or_stopwords(self):
        # Neither curated file has an opinion yet -- both name-shaped
        # literals are just unclassified candidates, not findings.
        hits, name_candidates = scan("05_korean_names.sql")
        self.assertEqual(len(hits), 0)
        self.assertEqual(set(name_candidates), {"홍길동", "강남구"})

    def test_known_name_becomes_hit(self):
        hits, name_candidates = scan("05_korean_names.sql", known_names={"홍길동"})
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual(h.severity, "FINDING")
        self.assertEqual(h.column_name, "-")
        self.assertEqual(h.operator, "-")
        self.assertEqual(h.value, "'홍길동'")
        self.assertEqual(name_candidates, ["강남구"])

    def test_stopword_excluded(self):
        # A stopworded candidate is dropped entirely -- not a finding, and
        # not left sitting in name_candidates for strings.txt either.
        hits, name_candidates = scan("05_korean_names.sql", stopwords={"강남구"})
        self.assertEqual(len(hits), 0)
        self.assertEqual(name_candidates, ["홍길동"])

    def test_known_name_offsets_slice_back_to_original_quoting(self):
        # A known-name finding's "value" is always single-quote-normalized even
        # when the source used double quotes -- masking must never rely on
        # it for the quote character, only on start_offset/end_offset
        # sliced from the original text (see src/mask.py).
        hits, name_candidates = scan_text(
            'SELECT * FROM t1 WHERE HLDR_NM = "홍길동";', known_names={"홍길동"})
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual(h.value, "'홍길동'")  # normalized in the dict
        # but the actual source text at the recorded span is double-quoted
        source = 'SELECT * FROM t1 WHERE HLDR_NM = "홍길동";'
        self.assertEqual(source[h.start_offset:h.end_offset + 1], '"홍길동"')


class TestFalsePositives(unittest.TestCase):
    def test_no_matches(self):
        hits, name_candidates = scan("06_false_positives.sql")
        self.assertEqual(hits, [])
        self.assertEqual(name_candidates, [])

    def test_blank_literals_ignored(self):
        hits, name_candidates = scan("08_blank_literal.sql")
        self.assertEqual(len(name_candidates), 0)
        # only the two real values should be reported: '0000080' (from the
        # IN-list, alongside a blank that must be dropped) and '0000081'
        self.assertEqual({h.value for h in hits}, {"'0000080'", "'0000081'"})

    def test_paren_list_does_not_cross_statement_boundary(self):
        hits, name_candidates = scan("09_paren_list_boundary.sql")
        self.assertEqual(len(name_candidates), 0)
        by_value = {h.value: h for h in hits}
        # the malformed/truncated "ctrt_no in ('0000099'" left in a comment
        # must NOT match at all (no closing paren on its own line) -- in
        # particular it must not swallow the live ACCT_ID on the next line
        # and mis-report it as a CTRT_NO value from the comment's line
        self.assertNotIn("CTRT_NO", {h.column_name for h in hits})
        self.assertEqual(by_value["'0000050'"].column_name, "ACCT_ID")
        self.assertEqual(by_value["'0000050'"].line, 3)
        self.assertEqual(by_value["'0000050'"].in_comment, "N")
        self.assertEqual(by_value["'0000100'"].column_name, "ACCT_ID")
        self.assertEqual(by_value["'0000100'"].line, 5)
        # a legitimate multi-line IN(...) with an inline comment between
        # values must still be fully detected
        self.assertEqual(
            {v for v in by_value if v in ("'0000201'", "'0000202'", "'0000203'")},
            {"'0000201'", "'0000202'", "'0000203'"})
        self.assertEqual(len(hits), 5)

    def test_subquery_in_list_not_treated_as_literal_list(self):
        hits, name_candidates = scan("10_subquery_in_list.sql")
        self.assertEqual(len(name_candidates), 0)
        # CTRT_NO IN (SELECT ... WHERE STAT_CD = '02') is a subquery, not a
        # hardcoded literal list -- neither the inner literal '02' (bound
        # to STAT_CD, an unconfigured column here) nor '2001' (digits out
        # of the inner table name TBSAMPLE001) may be attributed to CTRT_NO
        self.assertNotIn("CTRT_NO", {h.column_name for h in hits})
        self.assertEqual({h.value for h in hits}, {"'0000123'"})

    def test_digit_suffix_of_identifier_is_not_a_literal(self):
        hits, name_candidates = scan("11_digit_boundary.sql")
        self.assertEqual(len(name_candidates), 0)
        # "2001" out of table name TBSAMPLE001 must never be extracted as a
        # bare numeric literal just because "=CTRT_NO" happens to follow
        self.assertEqual({h.value for h in hits}, {"12345"})
        self.assertEqual(hits[0].column_name, "ACCT_ID")
        # An unquoted numeric literal's offsets must slice back to just the
        # digits, no surrounding quotes to worry about (relevant for
        # --mask-literals' numeric-vs-quoted classification).
        path = os.path.join(FIXTURES_DIR, "11_digit_boundary.sql")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        start, end = hits[0].start_offset, hits[0].end_offset
        self.assertEqual(text[start:end + 1], "12345")

    def test_empty_paren_list_is_not_a_value(self):
        hits, name_candidates = scan("12_empty_paren_list.sql")
        self.assertEqual(len(name_candidates), 0)
        # A.CTRT_NO IN () -- genuinely empty, no closing-line issue at all
        # -- and both a malformed two-line "-- ctrt_no not in (" / "--)"
        # comment fragment and a legitimate-looking but empty multi-line
        # ACCT_ID IN ( <blank> ) must produce zero findings: there's no
        # literal inside any of them, so nothing sensitive was found --
        # not "the empty parens themselves are the finding".
        self.assertEqual({h.value for h in hits}, {"'0000123'"})
        self.assertNotIn("CTRT_NO", {h.column_name for h in hits})

    def test_comment_escape_discards_match_but_recovers_hidden_live_hit(self):
        hits, name_candidates = scan("13_comment_escape_recovery.sql")
        self.assertEqual(len(name_candidates), 0)
        # a malformed "-- ... ctrt_no in ('0000099'" comment, with no
        # semicolon anywhere before a stray ')' a few lines down, would
        # previously either (a) mis-attribute the live ACCT_ID='0000050'
        # in between to CTRT_NO, or (b) once that mis-attribution was
        # blocked, silently swallow and lose that live match entirely.
        # Neither must happen: no CTRT_NO finding at all, and both real,
        # live ACCT_ID values are independently detected on their own line.
        self.assertNotIn("CTRT_NO", {h.column_name for h in hits})
        by_value = {h.value: h for h in hits}
        self.assertEqual(by_value["'0000050'"].line, 4)
        self.assertEqual(by_value["'0000050'"].in_comment, "N")
        self.assertEqual(by_value["'0000100'"].line, 6)
        self.assertEqual(len(hits), 2)


class TestAliasQualifiedColumn(unittest.TestCase):
    def test_alias_qualified_comparison_is_a_hit(self):
        # Regression guard: as_column() used to only check column_name(),
        # never field_reference() (the grammar's separate rule for a
        # table/alias-qualified reference) -- so an alias-qualified
        # comparison was previously silently missed entirely.
        hits, name_candidates = scan_text("SELECT * FROM t1 a WHERE a.ACCT_ID = '0000001';")
        self.assertEqual(len(name_candidates), 0)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].column_name, "ACCT_ID")
        self.assertEqual(hits[0].operator, "=")
        self.assertEqual(hits[0].value, "'0000001'")


class TestComplexRealWorldQuery(unittest.TestCase):
    """A large, genuinely complex real-world-derived query, generalized
    to fully domain-free table/column names (multi-CTE, 3-way UNION ALL,
    nested CASE, LEFT JOINs mixed with comma-joins, derived-table
    subqueries, a correlated IN-subquery, bare unquoted Korean column
    aliases throughout) -- a stress test for the whole pipeline at once,
    not a single-construct regression guard. Runs in ~3s (vs. milliseconds
    for the other fixtures here), a real cost of the tiered driver's
    per-token tier-racing on one very large, JOIN-heavy chunk -- see
    README's Known Limitations. (An earlier draft of this fixture used a
    reserved-keyword-colliding CTE name, `REF`, referenced ~10 times --
    that alone took the same query from ~3s to 66s, a concrete
    confirmation of exactly the performance cliff documented there.)"""

    def test_does_not_crash_and_produces_no_findings(self):
        hits, name_candidates = scan("14_complex_multi_cte_query.sql")
        self.assertEqual(hits, [])
        self.assertEqual(name_candidates, [])

    def test_real_tables_found_cte_names_excluded(self):
        # extract_table_refs=True only (no split_select here -- it's
        # exercised, with its own dedicated fixtures, in
        # tests/test_select_blocks.py; this test reads the classification
        # read-only instead so it stays independent of that).
        path = os.path.join(FIXTURES_DIR, "14_complex_multi_cte_query.sql")
        result = scanner.scan_file(
            path, scanner.DEFAULT_COLUMNS, set(), extract_table_refs=True)
        tables = {r.table for r in result.table_uses}
        self.assertEqual(tables, {"T1", "T2", "T_REF", "T_MAP", "T_CODE",
                                 "T_HIST", "SYSDUMMY1"})
        self.assertNotIn("CONFIG", tables)
        self.assertNotIn("AUX", tables)

        with open(path, encoding="utf-8") as f:
            text = f.read()
        all_tokens, _ = lex_file(text)
        ranges = chunk_ranges(all_tokens)
        # exactly one standalone SELECT block -- the whole WITH...GROUP BY
        # is one top-level chunk, not miscounted per-CTE/per-UNION-arm
        self.assertEqual(len(select_block_ranges(all_tokens, ranges)), 1)


class TestTxtExtension(unittest.TestCase):
    def test_txt_included_by_default(self):
        tree = scanner.scan_tree(
            FIXTURES_DIR, scanner.DEFAULT_COLUMNS, set())
        self.assertEqual(tree.file_count, 38)  # 37 .sql + 1 .txt fixture
        self.assertTrue(any(h.value == "'0000070'" for h in tree.findings))

    def test_sql_only_when_requested(self):
        tree = scanner.scan_tree(
            FIXTURES_DIR, scanner.DEFAULT_COLUMNS, set(), extensions=["sql"])
        self.assertEqual(tree.file_count, 37)
        self.assertFalse(any(h.value == "'0000070'" for h in tree.findings))

    def test_exclude_paths_skips_own_output_files(self):
        excluded = {os.path.abspath(os.path.join(FIXTURES_DIR, "07_from_txt_export.txt"))}
        tree = scanner.scan_tree(
            FIXTURES_DIR, scanner.DEFAULT_COLUMNS, set(), exclude_paths=excluded)
        self.assertEqual(tree.file_count, 37)
        self.assertFalse(any(h.value == "'0000070'" for h in tree.findings))


class TestMaskingEndToEnd(unittest.TestCase):
    """Stress test for --mask-literals against a fixture combining several
    finding shapes at once (plain/double-quoted finding, IN-list, BETWEEN,
    reversed comparison, bare-paren quirk, nested-paren IN item, single-
    and double-quoted known-name findings, a finding inside a comment) -- see
    tests/fixtures/16_masking_end_to_end.sql. Individual constructs already
    have their own dedicated tests elsewhere; this one exercises the full
    scan -> mask pipeline together, the way --mask-literals is actually
    used from cli.py. Runs against a scratch copy of the fixture (never
    the checked-in file itself), since masking now rewrites its target in
    place rather than writing a separate sibling."""

    FIXTURE = "16_masking_end_to_end.sql"
    KNOWN_NAMES = {"홍길동", "강남구"}

    def setUp(self):
        with open(os.path.join(FIXTURES_DIR, self.FIXTURE), encoding="utf-8") as f:
            self.original_text = f.read()
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, self.FIXTURE)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.original_text)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_masking_pipeline(self):
        result = scanner.scan_file(
            self.path, scanner.DEFAULT_COLUMNS, set(), self.KNOWN_NAMES)
        hits = result.findings
        self.assertEqual(len(hits), 15)
        self.assertEqual(result.name_candidates, [])

        written = mask.write_masked_files(hits)
        self.assertEqual(written, [self.path])

        with open(self.path, encoding="utf-8") as f:
            masked_text = f.read()

        # No original literal value survives in the masked output ...
        for f in hits:
            self.assertNotIn(f.value.strip("'\""), masked_text)
        # ... but every quote/paren/keyword/structural character is
        # unchanged: stripping the placeholder runs from both texts must
        # leave them identical.
        self.assertEqual(
            self.original_text.replace("0000001", "").replace("0000002", "")
                .replace("0000003", "").replace("0000004", "").replace("0000005", "")
                .replace("0000010", "").replace("0000020", "").replace("0000123", "")
                .replace("0000030", "").replace("0000040", "").replace("0000041", "")
                .replace("0000099", "").replace("0000050", "")
                .replace("홍길동", "").replace("강남구", ""),
            masked_text.replace("****", ""))

    def test_masking_is_idempotent_on_a_second_pass(self):
        # Re-scanning an already-masked file still finds the same finding
        # shapes (column/operator against a literal -- the placeholder is
        # still a literal), and re-masking must be a no-op: '****'/'0000'
        # simply mask to themselves.
        hits = scanner.scan_file(
            self.path, scanner.DEFAULT_COLUMNS, set(), self.KNOWN_NAMES).findings
        mask.write_masked_files(hits)
        with open(self.path, encoding="utf-8") as f:
            once = f.read()

        hits2 = scanner.scan_file(
            self.path, scanner.DEFAULT_COLUMNS, set(), self.KNOWN_NAMES).findings
        mask.write_masked_files(hits2)
        with open(self.path, encoding="utf-8") as f:
            twice = f.read()
        self.assertEqual(once, twice)


class TestSplitOutputNeverRescannedAsInput(unittest.TestCase):
    """A --split-select run leaves e.g. `report-01.sql` sitting alongside
    the original in the scanned tree -- a later scan of the same tree
    must never treat that as a distinct SQL file, or every finding/table/
    relation in the original gets double-counted under its split-output
    filename too."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        with open(os.path.join(self.d, "report.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT * FROM t1 WHERE ACCT_ID = '1';")
        # simulates a file --split-select already wrote on an earlier run
        with open(os.path.join(self.d, "report-01.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT * FROM t1 WHERE ACCT_ID = '1';")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_split_output_excluded_from_file_count_and_hits(self):
        tree = scanner.scan_tree(
            self.d, scanner.DEFAULT_COLUMNS, set())
        self.assertEqual(tree.file_count, 1)
        self.assertEqual(len(tree.findings), 1)


if __name__ == "__main__":
    unittest.main()
