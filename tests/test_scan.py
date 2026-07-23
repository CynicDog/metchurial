# -*- coding: utf-8 -*-
"""Ported from ../metchurial/tests/test_scan.py -- same assertions, same
fixtures, run against the new ANTLR-based engine.py instead of the original
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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import mask  # noqa: E402
from metchurial import engine as scanner  # noqa: E402
from metchurial.models.options import ScanOptions  # noqa: E402
from metchurial.split.select_blocks import select_block_ranges  # noqa: E402
from metchurial.parsing.statement_driver import chunk_ranges, lex_file  # noqa: E402


def scan(filename, stopwords=None, known_names=None):
    path = os.path.join(FIXTURES_DIR, filename)
    result = scanner.scan_file(
        path, ScanOptions(stopwords=stopwords or set(), known_names=known_names or set()))
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
            path, ScanOptions(stopwords=stopwords or set(), known_names=known_names or set()))
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


class TestAssignmentDetection(unittest.TestCase):
    """UPDATE ... SET col = 'literal' -- an assignment, a completely
    different grammar rule from the predicate/comparison shapes
    visitPredicate handles, so it needs its own visitor hook
    (ExtractorVisitor.visitAssignment_item) or it's silently invisible to
    sensitive-column detection regardless of how sensitive the column or
    how real the literal is."""

    def test_single_assignment_is_a_hit(self):
        hits, _ = scan_text("UPDATE t1 SET ACCT_ID = '1234567' WHERE X = 1;")
        acct_hits = [h for h in hits if h.column_name == "ACCT_ID"]
        self.assertEqual(len(acct_hits), 1)
        self.assertEqual(acct_hits[0].operator, "=")
        self.assertEqual(acct_hits[0].value, "'1234567'")

    def test_multiple_assignments_on_one_line_all_reported(self):
        hits, _ = scan_text(
            "UPDATE t1 SET ACCT_ID = '1234567', ACCT_NM = '9999', "
            "CTRT_NO = '1112223' WHERE X = 1;")
        by_col = {h.column_name: h.value for h in hits if h.column_name != "-"}
        self.assertEqual(by_col.get("ACCT_ID"), "'1234567'")
        self.assertEqual(by_col.get("ACCT_NM"), "'9999'")
        self.assertEqual(by_col.get("CTRT_NO"), "'1112223'")

    def test_non_sensitive_assignment_is_not_a_hit(self):
        hits, _ = scan_text("UPDATE t1 SET DESCRIPTION = 'not sensitive' WHERE X = 1;")
        self.assertEqual([h for h in hits if h.column_name == "DESCRIPTION"], [])

    def test_assignment_to_another_column_is_not_a_hit(self):
        # ACCT_ID assigned FROM another column (no literal on the right)
        # must never be reported -- there's no hardcoded value here at all.
        hits, _ = scan_text("UPDATE t1 SET ACCT_ID = OTHER_COL WHERE X = 1;")
        self.assertEqual([h for h in hits if h.column_name == "ACCT_ID"], [])


class TestSameLineFindingDoesNotSuppressUnrelatedNameCandidate(unittest.TestCase):
    """Regression test: known-name matching used to skip an entire *line*
    once any sensitive-column-comparison finding landed on it, so an
    unrelated name-shaped literal sharing that line silently never reached
    strings.txt/known_names.txt, let alone got masked. Fixed to dedup by
    exact literal span instead of by line."""

    def test_unrelated_name_literal_on_same_line_still_surfaces(self):
        hits, name_candidates = scan_text(
            "SELECT '홍길동', DESCRIPTION FROM T1 WHERE CTRT_NO = '9999999';")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].column_name, "CTRT_NO")
        self.assertEqual(name_candidates, ["홍길동"])

    def test_unrelated_name_literal_on_same_line_becomes_a_hit_when_known(self):
        hits, name_candidates = scan_text(
            "SELECT '홍길동', DESCRIPTION FROM T1 WHERE CTRT_NO = '9999999';",
            known_names={"홍길동"})
        self.assertEqual(len(hits), 2)
        self.assertEqual({h.value for h in hits}, {"'홍길동'", "'9999999'"})
        self.assertEqual(name_candidates, [])

    def test_same_literal_caught_by_both_paths_is_not_double_reported(self):
        # ACCT_NM is a sensitive column, so this literal is already a
        # finding via the assignment/comparison path -- the known-name
        # regex pass must not also emit a second, redundant finding for
        # the exact same span.
        hits, name_candidates = scan_text(
            "UPDATE t1 SET ACCT_NM = '홍길동' WHERE X = 1;", known_names={"홍길동"})
        matching = [h for h in hits if h.value == "'홍길동'"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].column_name, "ACCT_NM")
        self.assertEqual(name_candidates, [])


class TestInsertValuesDetection(unittest.TestCase):
    """INSERT INTO t (col, ...) VALUES ('lit', ...) binds each value to its
    column purely by position against the explicit column list --
    ExtractorVisitor.visitInsert_statement implements this the same way
    visitAssignment_item covers UPDATE...SET.

    IMPORTANT: the vendored grammar (vendor/grammars-v4/Db2Parser.g4,
    insert_statement rule) currently cannot parse this shape *at all* --
    `INSERT INTO t (col) VALUES (...)` fails with "no viable alternative"
    even though the EBNF (`column_name_list?` right after the table name)
    looks correct on paper; `INSERT INTO t VALUES (...)` with no column
    list parses fine. Reproduced with a bare `parser.sql_statement()`
    call, no metchurial code involved -- this is an upstream grammar
    limitation, not a bug in visitInsert_statement itself. The first test
    below documents today's actual (unfortunate) behavior; the others show
    the no-column-list case is deliberately never guessed at."""

    def test_explicit_column_list_form_currently_produces_no_hit_at_all(self):
        # This SHOULD be a hit once the grammar limitation above is
        # worked around (e.g. a token-scan fallback, same pattern as the
        # existing bare-paren/double-quoted-literal fallbacks) -- today it
        # silently isn't, which is exactly the gap this test documents.
        hits, _ = scan_text(
            "INSERT INTO CUSTOMERS (ACCT_ID, ACCT_NM) VALUES ('1234567', '9999');")
        self.assertEqual(hits, [])

    def test_no_column_list_form_is_never_guessed_at(self):
        # Parses fine, but with no column list there's no way to know
        # which value lands in which column without the table's real DDL
        # -- must not be reported at all rather than guessing positionally
        # against some assumed column order.
        hits, _ = scan_text("INSERT INTO CUSTOMERS VALUES ('1234567', '9999');")
        self.assertEqual(hits, [])


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
        result = scanner.scan_file(path, ScanOptions(extract_table_refs=True))
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
        tree = scanner.scan_tree(FIXTURES_DIR)
        self.assertEqual(tree.file_count, 38)  # 37 .sql + 1 .txt fixture
        self.assertTrue(any(h.value == "'0000070'" for h in tree.findings))

    def test_sql_only_when_requested(self):
        tree = scanner.scan_tree(FIXTURES_DIR, ScanOptions(extensions=("sql",)))
        self.assertEqual(tree.file_count, 37)
        self.assertFalse(any(h.value == "'0000070'" for h in tree.findings))

    def test_exclude_paths_skips_own_output_files(self):
        excluded = {os.path.abspath(os.path.join(FIXTURES_DIR, "07_from_txt_export.txt"))}
        tree = scanner.scan_tree(FIXTURES_DIR, exclude_paths=excluded)
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
            self.path, ScanOptions(known_names=self.KNOWN_NAMES))
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
            self.path, ScanOptions(known_names=self.KNOWN_NAMES)).findings
        mask.write_masked_files(hits)
        with open(self.path, encoding="utf-8") as f:
            once = f.read()

        hits2 = scanner.scan_file(
            self.path, ScanOptions(known_names=self.KNOWN_NAMES)).findings
        mask.write_masked_files(hits2)
        with open(self.path, encoding="utf-8") as f:
            twice = f.read()
        self.assertEqual(once, twice)


class TestSameNameDifferentExtensionDeduped(unittest.TestCase):
    """A backup copy of a source file, kept alongside it under a different
    extension (query1.sql / query1.sql.bak, or a lone query1.bak with no
    ".sql" counterpart), must count as the same file for scanning purposes
    -- not a second, independent one. This is purely name-based: a
    same-identity sibling is dropped regardless of whether its content
    actually still matches, since a diverged backup is still just a
    backup, not independent data worth double-scanning."""

    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def _write(self, name, text):
        with open(os.path.join(self.d, name), "w", encoding="utf-8") as f:
            f.write(text)

    def test_identical_bak_copy_of_sql_file_counts_once(self):
        text = "SELECT * FROM t1 WHERE ACCT_ID = '1';"
        self._write("query1.sql", text)
        self._write("query1.sql.bak", text)
        tree = scanner.scan_tree(self.d, ScanOptions(extensions=("sql", "bak")))
        self.assertEqual(tree.file_count, 1)
        self.assertEqual(len(tree.findings), 1)

    def test_bare_bak_file_with_no_sql_sibling_counts_once(self):
        text = "SELECT * FROM t1 WHERE ACCT_ID = '1';"
        self._write("query1.bak", text)
        tree = scanner.scan_tree(self.d, ScanOptions(extensions=("sql", "bak")))
        self.assertEqual(tree.file_count, 1)
        self.assertEqual(len(tree.findings), 1)

    def test_diverged_bak_copy_is_still_collapsed_by_name_alone(self):
        self._write("query1.sql", "SELECT * FROM t1 WHERE ACCT_ID = '1';")
        self._write("query1.sql.bak", "SELECT * FROM t1 WHERE ACCT_ID = '2';")
        tree = scanner.scan_tree(self.d, ScanOptions(extensions=("sql", "bak")))
        self.assertEqual(tree.file_count, 1)
        self.assertEqual(len(tree.findings), 1)

    def test_bare_bak_sibling_never_wins_over_real_sql_file(self):
        # "select_my_income.sql" and "select_my_income.bak" are the same
        # length -- a length-only tie-break falls through to alphabetical
        # order, where "bak" < "sql" would wrongly pick the backup copy
        # and leave the real .sql file completely unscanned. Content is
        # deliberately made to *differ* per-format below so the assertion
        # can tell which file was actually chosen, not just that some file
        # with matching findings was scanned.
        self._write("select_my_income.sql",
                    "SELECT * FROM t1 WHERE ACCT_ID = '1'; SELECT * FROM t2;")
        self._write("select_my_income.bak", "not sql at all, just a stray same-named backup")
        options = ScanOptions(extensions=("sql", "bak"), split_selects=True)
        tree = scanner.scan_tree(self.d, options)
        self.assertEqual(tree.file_count, 1)
        remaining = set(os.listdir(self.d))
        self.assertIn("select_my_income-01.sql", remaining)
        self.assertIn("select_my_income-02.sql", remaining)
        self.assertNotIn("select_my_income.bak", remaining)

    def test_bak_extension_not_scanned_unless_requested(self):
        text = "SELECT * FROM t1 WHERE ACCT_ID = '1';"
        self._write("query1.sql", text)
        self._write("query1.sql.bak", text)
        tree = scanner.scan_tree(self.d, ScanOptions(extensions=("sql",)))
        self.assertEqual(tree.file_count, 1)


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
        tree = scanner.scan_tree(self.d)
        self.assertEqual(tree.file_count, 1)
        self.assertEqual(len(tree.findings), 1)


class TestSplitOutputScannedOnceOriginalIsGone(unittest.TestCase):
    """Once --split-selects has actually run and deleted the original
    (the normal case -- see write_split_files), its split-output siblings
    are the only copy of that data left on disk and must be scanned like
    any other file on a later, separate run. Before this fix,
    _matching_files excluded any -NN-suffixed name unconditionally, so a
    plain --extract-metadata run after an earlier --split-selects run
    found nothing for that file at all, forever."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        # simulates the post-split state: only the split outputs remain,
        # the original ("report.sql") is already gone.
        with open(os.path.join(self.d, "report-01.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT * FROM t1 WHERE ACCT_ID = '1';")
        with open(os.path.join(self.d, "report-02.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT * FROM t2 WHERE ACCT_ID = '2';")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_both_split_files_scanned_when_original_absent(self):
        tree = scanner.scan_tree(self.d)
        self.assertEqual(tree.file_count, 2)
        self.assertEqual(len(tree.findings), 2)


class TestSplitDeletesMatchingBackupSiblings(unittest.TestCase):
    """A .bak sibling of a file that --split-selects just split (and
    deleted) must be deleted too, purely by name -- no content comparison
    -- otherwise it survives untouched into a later scan, where it's no
    longer deduped against anything (the original is gone) and gets split
    all over again under its own name, duplicating content the first run
    already captured."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.text = "SELECT a FROM t1; SELECT b FROM t2;"

    def tearDown(self):
        shutil.rmtree(self.d)

    def _write(self, name, text):
        with open(os.path.join(self.d, name), "w", encoding="utf-8") as f:
            f.write(text)

    def test_identical_bak_sibling_deleted_alongside_split_original(self):
        self._write("query1.sql", self.text)
        self._write("query1.sql.bak", self.text)
        options = ScanOptions(extensions=("sql", "bak"), split_selects=True)
        scanner.scan_tree(self.d, options)
        remaining = set(os.listdir(self.d))
        self.assertNotIn("query1.sql.bak", remaining)
        self.assertNotIn("query1.sql", remaining)
        self.assertIn("query1-01.sql", remaining)
        self.assertIn("query1-02.sql", remaining)

        # A later scan of the same tree finds the split files themselves
        # (their original is gone, so they're ordinary input now -- see
        # _is_stale_split_output), but nothing gets (re-)split: each is a
        # single SELECT block on its own, and looks_like_split_output
        # refuses to re-split an already-split file regardless.
        tree2 = scanner.scan_tree(self.d, options)
        self.assertEqual(tree2.file_count, 2)
        self.assertEqual(tree2.split_manifest, [])
        remaining2 = set(os.listdir(self.d))
        self.assertEqual(remaining2, {"query1-01.sql", "query1-02.sql"})

    def test_diverged_bak_sibling_deleted_too_by_name_alone(self):
        self._write("query1.sql", self.text)
        self._write("query1.sql.bak", "SELECT c FROM t3 WHERE x = 1; SELECT d FROM t4;")
        options = ScanOptions(extensions=("sql", "bak"), split_selects=True)
        tree = scanner.scan_tree(self.d, options)
        self.assertEqual(tree.file_count, 1)
        remaining = set(os.listdir(self.d))
        self.assertIn("query1-01.sql", remaining)
        self.assertIn("query1-02.sql", remaining)
        self.assertNotIn("query1.sql.bak", remaining)


if __name__ == "__main__":
    unittest.main()
