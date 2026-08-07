# -*- coding: utf-8 -*-
"""Tests for --identity-granularity (models/options.IDENTITY_GRANULARITIES):
core_id's discriminating fact-set tier is a per-run choice, not the single
fixed subset it used to be -- see references/query_identity.py's module
docstring, "Condensed grouping", and docs/query-identity.md. Reuses the
CORE_A stress-corpus fixtures tests/test_query_identity.py already exercises
at the `structure` default, checking how the same fixture pairs regroup at
the other three tiers -- plus a couple of ad hoc GROUP BY-only variants that
corpus has no need for at the default tier (GROUPBY never discriminates
there) but does here.

Run:
    python -m unittest tests.test_identity_granularity
"""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import cli  # noqa: E402
from metchurial import engine as scanner  # noqa: E402
from metchurial.models.options import ScanOptions  # noqa: E402

BASE = "20_query_identity_base.sql"
PREDICATE_VARIANT = "25_query_identity_predicate_variant.sql"
JOIN_TYPE_VARIANT = "32_query_near_miss_join_type_change.sql"

GROUPBY_BASE_SQL = (
    "SELECT A.ACCT_ID, B.CTRT_NO FROM TBACCT A "
    "INNER JOIN TBCTRT B ON A.ACCT_ID = B.ACCT_ID "
    "GROUP BY A.ACCT_ID, B.CTRT_NO;\n"
)
GROUPBY_VARIANT_SQL = (
    "SELECT A.ACCT_ID, B.CTRT_NO FROM TBACCT A "
    "INNER JOIN TBCTRT B ON A.ACCT_ID = B.ACCT_ID "
    "GROUP BY A.ACCT_ID;\n"
)


def _identity_rows(filename, granularity):
    path = os.path.join(FIXTURES_DIR, filename)
    result = scanner.scan_file(
        path, ScanOptions(extract_query_identity=True, identity_granularity=granularity))
    assert result.bad_reason is None, (filename, result.bad_reason)
    return result.identity_rows


def _core_id(filename, granularity):
    rows = _identity_rows(filename, granularity)
    assert len(rows) == 1, (filename, rows)
    return rows[0].core_id


def _scan_sql(sql_text, granularity):
    """Scans a small ad hoc SQL string (not one of the fixture files) --
    used for the GROUP BY-only variant pair, which the existing fixture
    corpus has no need for at the `structure` default."""
    workdir = tempfile.mkdtemp()
    try:
        path = os.path.join(workdir, "query.sql")
        with open(path, "w", encoding="utf-8") as f:
            f.write(sql_text)
        result = scanner.scan_file(
            path, ScanOptions(extract_query_identity=True, identity_granularity=granularity))
        assert result.bad_reason is None, result.bad_reason
        rows = result.identity_rows
        assert len(rows) == 1, rows
        return rows[0]
    finally:
        shutil.rmtree(workdir)


class TestTableTierCollapsesJoinTypeDifferences(unittest.TestCase):
    """At `table`, only the table set discriminates core_id -- a join-type
    change (structure tier's NEAR_MISS case, see test_query_identity.py)
    must stop mattering."""

    def test_join_type_change_collapses_onto_base_at_table_tier(self):
        self.assertEqual(_core_id(BASE, "table"), _core_id(JOIN_TYPE_VARIANT, "table"))

    def test_join_type_change_still_distinct_at_structure_tier(self):
        # Sanity check the fixture pair still behaves as
        # test_query_identity.py documents at the unaffected default tier.
        self.assertNotEqual(_core_id(BASE, "structure"), _core_id(JOIN_TYPE_VARIANT, "structure"))


class TestFilteredTierSplitsPredicateDifferences(unittest.TestCase):
    """At `filtered`, a WHERE-only difference (structure tier's CORE_A
    predicate variant) must now produce a distinct core_id."""

    def test_predicate_variant_distinct_at_filtered_tier(self):
        self.assertNotEqual(_core_id(BASE, "filtered"), _core_id(PREDICATE_VARIANT, "filtered"))

    def test_predicate_variant_still_collapses_at_structure_tier(self):
        self.assertEqual(_core_id(BASE, "structure"), _core_id(PREDICATE_VARIANT, "structure"))


class TestStrictTierSplitsGroupByDifferences(unittest.TestCase):
    """At `strict`, a GROUP BY-only difference must produce a distinct
    core_id; `filtered` (which still excludes GROUPBY) must not."""

    def test_groupby_variant_distinct_at_strict_tier(self):
        base_id = _scan_sql(GROUPBY_BASE_SQL, "strict").core_id
        variant_id = _scan_sql(GROUPBY_VARIANT_SQL, "strict").core_id
        self.assertNotEqual(base_id, variant_id)

    def test_groupby_variant_collapses_at_filtered_tier(self):
        base_id = _scan_sql(GROUPBY_BASE_SQL, "filtered").core_id
        variant_id = _scan_sql(GROUPBY_VARIANT_SQL, "filtered").core_id
        self.assertEqual(base_id, variant_id)


class TestSupplementaryFieldsStayPopulatedAtEveryTier(unittest.TestCase):
    """table_count/join_count/tables/join_types/relations are read from the
    statement's full fact set, not the granularity-narrowed one -- so even
    at the loosest `table` tier (which excludes JOINTYPE/REL from what
    discriminates core_id), these must still report the real joins, not
    silently read as empty/zero."""

    def test_join_count_and_relations_survive_table_tier(self):
        row = _identity_rows(BASE, "table")[0]
        self.assertGreater(row.join_count, 0)
        self.assertTrue(row.join_types)
        self.assertTrue(row.relations)
        self.assertEqual(row.table_count, 4)

    def test_supplementary_fields_identical_across_tiers(self):
        # Granularity must only ever move core_id -- these fields must not
        # move at all.
        rows = {g: _identity_rows(BASE, g)[0] for g in
                ("table", "structure", "filtered", "strict")}
        reference = rows["structure"]
        for granularity, row in rows.items():
            self.assertEqual(row.table_count, reference.table_count, granularity)
            self.assertEqual(row.join_count, reference.join_count, granularity)
            self.assertEqual(row.tables, reference.tables, granularity)
            self.assertEqual(row.join_types, reference.join_types, granularity)
            self.assertEqual(row.relations, reference.relations, granularity)


class TestCliValidation(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.sql_root = os.path.join(self.workdir, "sqlroot")
        os.mkdir(self.sql_root)
        with open(os.path.join(self.sql_root, "a.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT c1 FROM s1.t1;\n")
        self.prev_cwd = os.getcwd()
        os.chdir(self.workdir)

    def tearDown(self):
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.workdir)

    def _run(self, argv):
        """cli.main always sys.exit()s; returns the exit code."""
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cli.main(argv)
        return ctx.exception.code

    def test_invalid_granularity_value_rejected(self):
        code = self._run([self.sql_root, "--extract-metadata", "--identity-granularity", "bogus"])
        self.assertEqual(code, 2)  # argparse usage-error exit code

    def test_non_default_granularity_without_extract_metadata_is_usage_error(self):
        code = self._run([self.sql_root, "--identity-granularity", "filtered"])
        self.assertEqual(code, 2)

    def test_default_granularity_without_extract_metadata_is_fine(self):
        code = self._run([self.sql_root])
        self.assertIn(code, (0, 1))

    def test_granularity_reported_in_summary(self):
        code = self._run([self.sql_root, "--extract-metadata", "--identity-granularity", "table"])
        self.assertIn(code, (0, 1))
        with open("summary.md", encoding="utf-8-sig") as f:
            summary = f.read()
        self.assertIn("| Identity granularity | table |", summary)


if __name__ == "__main__":
    unittest.main()
