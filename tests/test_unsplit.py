# -*- coding: utf-8 -*-
"""Tests for --un-split-selects: io_utils.load_split_manifest,
unsplit.revert_splits' own regrouping/safety-check logic, plus the CLI
wiring (flag, mutual exclusion with --split-selects, split_manifest.tsv
rewritten, summary.md's Un-split selects row).

Run:
    python -m unittest tests.test_unsplit
"""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import cli  # noqa: E402
from metchurial import unsplit  # noqa: E402
from metchurial.io_utils import load_split_manifest  # noqa: E402
from metchurial.models.split import SplitManifestRow  # noqa: E402
from metchurial.tsv import write_refs_tsv  # noqa: E402


class TestLoadSplitManifest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "split_manifest.tsv")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_round_trip_through_write_refs_tsv(self):
        rows = [
            SplitManifestRow(original_file="a.sql", split_file="a-01.sql",
                             block_number=1, total_blocks=2),
            SplitManifestRow(original_file="a.sql", split_file="a-02.sql",
                             block_number=2, total_blocks=2),
        ]
        write_refs_tsv(self.path,
                       ["original_file", "split_file", "block_number", "total_blocks"], rows)

        loaded = load_split_manifest(self.path)

        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].original_file, "a.sql")
        self.assertEqual(loaded[0].split_file, "a-01.sql")
        self.assertEqual(loaded[0].block_number, 1)
        self.assertEqual(loaded[0].total_blocks, 2)

    def test_missing_file_returns_empty(self):
        self.assertEqual(load_split_manifest(self.path), [])

    def test_header_only_file_has_no_entries(self):
        write_refs_tsv(self.path,
                       ["original_file", "split_file", "block_number", "total_blocks"], [])
        self.assertEqual(load_split_manifest(self.path), [])


class TestRevertSplits(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def _write(self, name, content):
        path = os.path.join(self.d, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _row(self, original, split_name, block, total):
        return SplitManifestRow(
            original_file=os.path.join(self.d, original),
            split_file=os.path.join(self.d, split_name),
            block_number=block, total_blocks=total)

    def test_complete_group_is_reverted_and_split_files_removed(self):
        self._write("a-01.sql", "SELECT A FROM T1;")
        self._write("a-02.sql", "SELECT B FROM T2;")
        rows = [self._row("a.sql", "a-01.sql", 1, 2), self._row("a.sql", "a-02.sql", 2, 2)]

        reverted, remaining = unsplit.revert_splits(rows)

        original = os.path.join(self.d, "a.sql")
        self.assertEqual(reverted, [original])
        self.assertEqual(remaining, [])
        self.assertTrue(os.path.isfile(original))
        self.assertFalse(os.path.isfile(os.path.join(self.d, "a-01.sql")))
        self.assertFalse(os.path.isfile(os.path.join(self.d, "a-02.sql")))
        with open(original, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("SELECT A FROM T1;", content)
        self.assertIn("SELECT B FROM T2;", content)

    def test_uses_each_split_files_current_content_not_a_cached_copy(self):
        self._write("a-01.sql", "SELECT A FROM T1;")
        self._write("a-02.sql", "-- edited during review\nSELECT B FROM T2 WHERE X = 1;")
        rows = [self._row("a.sql", "a-01.sql", 1, 2), self._row("a.sql", "a-02.sql", 2, 2)]

        reverted, _remaining = unsplit.revert_splits(rows)

        self.assertEqual(len(reverted), 1)
        with open(reverted[0], encoding="utf-8") as f:
            content = f.read()
        self.assertIn("edited during review", content)

    def test_incomplete_group_is_left_alone(self):
        self._write("a-01.sql", "SELECT A FROM T1;")
        # a-02.sql missing entirely from disk AND from rows -- total_blocks
        # says 2 but only one row was ever passed in.
        rows = [self._row("a.sql", "a-01.sql", 1, 2)]
        warnings = []

        reverted, remaining = unsplit.revert_splits(rows, warn=warnings.append)

        self.assertEqual(reverted, [])
        self.assertEqual(remaining, rows)
        self.assertTrue(os.path.isfile(os.path.join(self.d, "a-01.sql")))
        self.assertTrue(any("skipped" in w for w in warnings))

    def test_missing_split_file_on_disk_is_left_alone(self):
        self._write("a-01.sql", "SELECT A FROM T1;")
        # a-02.sql recorded in the manifest but never actually written/
        # already deleted since.
        rows = [self._row("a.sql", "a-01.sql", 1, 2), self._row("a.sql", "a-02.sql", 2, 2)]
        warnings = []

        reverted, remaining = unsplit.revert_splits(rows, warn=warnings.append)

        self.assertEqual(reverted, [])
        self.assertEqual(remaining, rows)
        self.assertTrue(os.path.isfile(os.path.join(self.d, "a-01.sql")))
        self.assertTrue(any("missing" in w for w in warnings))

    def test_original_already_recreated_is_never_overwritten(self):
        self._write("a-01.sql", "SELECT A FROM T1;")
        self._write("a-02.sql", "SELECT B FROM T2;")
        self._write("a.sql", "-- someone recreated this since the split\n")
        rows = [self._row("a.sql", "a-01.sql", 1, 2), self._row("a.sql", "a-02.sql", 2, 2)]
        warnings = []

        reverted, remaining = unsplit.revert_splits(rows, warn=warnings.append)

        self.assertEqual(reverted, [])
        self.assertEqual(remaining, rows)
        self.assertTrue(os.path.isfile(os.path.join(self.d, "a-01.sql")))
        self.assertTrue(os.path.isfile(os.path.join(self.d, "a-02.sql")))
        with open(os.path.join(self.d, "a.sql"), encoding="utf-8") as f:
            self.assertIn("someone recreated", f.read())
        self.assertTrue(any("already exists" in w for w in warnings))

    def test_mixed_groups_only_the_reissuable_one_reverts(self):
        self._write("good-01.sql", "SELECT A FROM T1;")
        self._write("good-02.sql", "SELECT B FROM T2;")
        self._write("bad-01.sql", "SELECT C FROM T3;")
        good_rows = [self._row("good.sql", "good-01.sql", 1, 2),
                    self._row("good.sql", "good-02.sql", 2, 2)]
        bad_rows = [self._row("bad.sql", "bad-01.sql", 1, 2)]  # incomplete: 1 of 2

        reverted, remaining = unsplit.revert_splits(good_rows + bad_rows)

        self.assertEqual(reverted, [os.path.join(self.d, "good.sql")])
        self.assertEqual(remaining, bad_rows)

    def test_no_rows_is_a_no_op(self):
        reverted, remaining = unsplit.revert_splits([])
        self.assertEqual(reverted, [])
        self.assertEqual(remaining, [])


class TestUnsplitCLI(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.sql_root = os.path.join(self.workdir, "sqlroot")
        os.makedirs(self.sql_root)
        with open(os.path.join(self.sql_root, "report.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT A FROM T1;\nSELECT B FROM T2;\nSELECT C FROM T3;\n")
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

    def test_split_then_unsplit_round_trip(self):
        self._run([self.sql_root, "--extensions", "sql", "--split-selects"])
        self.assertFalse(os.path.isfile(os.path.join(self.sql_root, "report.sql")))
        self.assertTrue(os.path.isfile(os.path.join(self.sql_root, "report-01.sql")))

        self._run([self.sql_root, "--extensions", "sql", "--un-split-selects"])

        self.assertTrue(os.path.isfile(os.path.join(self.sql_root, "report.sql")))
        self.assertFalse(os.path.isfile(os.path.join(self.sql_root, "report-01.sql")))
        self.assertFalse(os.path.isfile(os.path.join(self.sql_root, "report-02.sql")))
        self.assertFalse(os.path.isfile(os.path.join(self.sql_root, "report-03.sql")))
        with open("split_manifest.tsv", encoding="utf-8-sig") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)  # header row only, all rows reverted

        with open("summary.md", encoding="utf-8-sig") as f:
            self.assertIn("| Un-split selects | ON |", f.read())

    def test_flag_off_leaves_split_manifest_absent(self):
        self._run([self.sql_root, "--extensions", "sql"])
        self.assertFalse(os.path.exists("split_manifest.tsv"))
        with open("summary.md", encoding="utf-8-sig") as f:
            self.assertIn("| Un-split selects | OFF |", f.read())

    def test_no_prior_manifest_is_a_no_op_not_a_crash(self):
        code = self._run([self.sql_root, "--extensions", "sql", "--un-split-selects"])
        self.assertIn(code, (0, 1))
        self.assertTrue(os.path.isfile(os.path.join(self.sql_root, "report.sql")))

    def test_both_split_and_unsplit_together_is_an_error(self):
        code = self._run([self.sql_root, "--extensions", "sql",
                          "--split-selects", "--un-split-selects"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
