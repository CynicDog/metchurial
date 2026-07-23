# -*- coding: utf-8 -*-
"""Tests for quarantine.bad_files.quarantine_bad_files: physically moving
a file the scan flagged bad into _quarantine/bad_files/, plus the CLI
wiring -- this runs automatically on every scan (not behind a flag),
and bad_files.tsv keeps the row (original path + reason) with a
quarantined_file column pointing at the new location.

Run:
    python -m unittest tests.test_quarantine_bad_files
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
from metchurial.io_utils import load_bad_files  # noqa: E402
from metchurial.models.bad_file import BadFileReason  # noqa: E402
from metchurial.quarantine import quarantine_bad_files  # noqa: E402


class TestQuarantineBadFiles(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def _write(self, rel_path, content="========================================\n"):
        full = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return full

    def test_moves_file_and_records_destination(self):
        path = self._write("bad.sql")
        bad_files_dir = os.path.join(self.root, "_quarantine", "bad_files")
        reason = BadFileReason(category="repeated-char-run", item="====", message="divider")

        updated = quarantine_bad_files({path: reason}, self.root, bad_files_dir)

        dest = os.path.join(bad_files_dir, "bad.sql")
        self.assertFalse(os.path.exists(path))
        self.assertTrue(os.path.isfile(dest))
        self.assertEqual(updated[path].quarantined_file, dest)
        # original reason fields carried through unchanged
        self.assertEqual(updated[path].category, "repeated-char-run")
        self.assertEqual(updated[path].message, "divider")

    def test_mirrors_relative_path_from_root(self):
        path = self._write(os.path.join("sub", "dir", "bad.sql"))
        bad_files_dir = os.path.join(self.root, "_quarantine", "bad_files")
        reason = BadFileReason(category="crash", item="", message="boom")

        updated = quarantine_bad_files({path: reason}, self.root, bad_files_dir)

        expected_dest = os.path.join(bad_files_dir, "sub", "dir", "bad.sql")
        self.assertTrue(os.path.isfile(expected_dest))
        self.assertEqual(updated[path].quarantined_file, expected_dest)

    def test_repeated_move_to_same_relative_path_does_not_clobber(self):
        bad_files_dir = os.path.join(self.root, "_quarantine", "bad_files")
        path1 = self._write("bad.sql", content="first")
        reason = BadFileReason(category="crash", item="", message="boom")
        quarantine_bad_files({path1: reason}, self.root, bad_files_dir)

        path2 = self._write("bad.sql", content="second")
        updated = quarantine_bad_files({path2: reason}, self.root, bad_files_dir)

        dest = updated[path2].quarantined_file
        self.assertNotEqual(dest, os.path.join(bad_files_dir, "bad.sql"))
        with open(dest, encoding="utf-8") as f:
            self.assertEqual(f.read(), "second")
        with open(os.path.join(bad_files_dir, "bad.sql"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "first")

    def test_missing_file_is_reported_and_left_unquarantined(self):
        bad_files_dir = os.path.join(self.root, "_quarantine", "bad_files")
        missing_path = os.path.join(self.root, "gone.sql")  # never actually written
        reason = BadFileReason(category="crash", item="", message="boom")
        warnings = []

        updated = quarantine_bad_files({missing_path: reason}, self.root, bad_files_dir,
                                       warn=warnings.append)

        self.assertEqual(updated[missing_path].quarantined_file, "")
        self.assertTrue(any("cannot move" in w for w in warnings))

    def test_empty_input_is_a_no_op(self):
        updated = quarantine_bad_files({}, self.root, os.path.join(self.root, "_quarantine", "bad_files"))
        self.assertEqual(updated, {})


class TestQuarantineBadFilesCLI(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.sql_root = os.path.join(self.workdir, "sqlroot")
        os.makedirs(self.sql_root)
        with open(os.path.join(self.sql_root, "good.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT * FROM t1 WHERE X = 1;\n")  # no sensitive-column finding
        with open(os.path.join(self.sql_root, "bad.sql"), "w", encoding="utf-8") as f:
            f.write("========================================\nSELECT * FROM t1;\n")
        self.prev_cwd = os.getcwd()
        os.chdir(self.workdir)

    def tearDown(self):
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.workdir)

    def _run(self, argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cli.main(argv)
        return ctx.exception.code

    def test_bad_file_is_quarantined_automatically_no_flag_needed(self):
        self._run([self.sql_root, "--extensions", "sql"])

        self.assertFalse(os.path.isfile(os.path.join(self.sql_root, "bad.sql")))
        self.assertTrue(os.path.isfile(os.path.join(self.sql_root, "good.sql")))
        self.assertTrue(os.path.isfile(
            os.path.join("_quarantine", "bad_files", "bad.sql")))

        entries = load_bad_files("bad_files.tsv")
        original_abspath = os.path.abspath(os.path.join(self.sql_root, "bad.sql"))
        self.assertIn(original_abspath, entries)
        self.assertTrue(entries[original_abspath].quarantined_file.endswith(
            os.path.join("_quarantine", "bad_files", "bad.sql")))

    def test_bad_file_not_rescanned_from_quarantine_on_next_run(self):
        self._run([self.sql_root, "--extensions", "sql"])
        # bad.sql is gone from sql_root now, sitting in _quarantine/bad_files/
        # instead -- a second run must not walk back into _quarantine/ and
        # treat it as fresh input.
        code = self._run([self.sql_root, "--extensions", "sql"])
        self.assertEqual(code, 0)  # only good.sql left to scan, no findings

        entries = load_bad_files("bad_files.tsv")
        self.assertEqual(len(entries), 1)  # still just the one historical entry


if __name__ == "__main__":
    unittest.main()
