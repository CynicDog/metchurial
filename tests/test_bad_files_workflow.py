# -*- coding: utf-8 -*-
"""Tests for the bad_files.tsv skip-list workflow: io_utils.py's
load_bad_files/write_bad_files round-trip, and scan_file's own two
safety nets (the cheap bad_file_check pre-check, and the try/except
around the real work so one file's unexpected crash can't take down an
entire tree scan).

Run:
    python -m unittest tests.test_bad_files_workflow
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import engine as scanner  # noqa: E402
from metchurial.io_utils import load_bad_files, write_bad_files  # noqa: E402
from metchurial.models.bad_file import BadFileReason  # noqa: E402


class TestBadFilesIO(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "bad_files.tsv")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_round_trip(self):
        entries = {
            "/a/b.sql": BadFileReason(category="repeated-char-run", item="====",
                                      message="some reason"),
            "/c/d.sql": BadFileReason(category="", item="", message=""),
        }
        write_bad_files(self.path, entries)
        loaded = load_bad_files(self.path)
        self.assertEqual(loaded, {
            os.path.abspath("/a/b.sql"): BadFileReason(
                category="repeated-char-run", item="====", message="some reason"),
            os.path.abspath("/c/d.sql"): BadFileReason(category="", item="", message=""),
        })

    def test_missing_file_returns_empty(self):
        self.assertEqual(load_bad_files(os.path.join(self.d, "nope.tsv")), {})

    def test_header_only_file_has_no_entries(self):
        write_bad_files(self.path, {})
        self.assertEqual(load_bad_files(self.path), {})

    def test_deleting_a_row_removes_it_on_reload(self):
        write_bad_files(self.path, {
            "/a/b.sql": BadFileReason(category="crash", item="", message="reason1"),
            "/c/d.sql": BadFileReason(category="crash", item="", message="reason2"),
        })
        with open(self.path, encoding="utf-8-sig") as f:
            lines = f.readlines()
        # simulate the user deleting the data row for /a/b.sql, keeping
        # the header row
        kept = [ln for ln in lines if "/a/b.sql" not in ln]
        with open(self.path, "w", encoding="utf-8-sig") as f:
            f.writelines(kept)
        loaded = load_bad_files(self.path)
        self.assertNotIn(os.path.abspath("/a/b.sql"), loaded)
        self.assertIn(os.path.abspath("/c/d.sql"), loaded)


class TestScanFileSafetyNets(unittest.TestCase):
    def test_divider_heavy_file_is_flagged_bad_without_crashing(self):
        fd, path = tempfile.mkstemp(suffix=".sql")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("========================================\nSELECT * FROM t1;\n")
            result = scanner.scan_file(path)
            self.assertIsNotNone(result.bad_reason)
            self.assertEqual((result.findings, result.name_candidates, result.select_block_count),
                             ([], [], 0))
        finally:
            os.unlink(path)

    def test_unexpected_exception_is_caught_and_marks_bad_instead_of_propagating(self):
        fd, path = tempfile.mkstemp(suffix=".sql")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("SELECT * FROM t1 WHERE ACCT_ID = '1';\n")
            with mock.patch("metchurial.engine._scan_file_body", side_effect=RuntimeError("boom")):
                result = scanner.scan_file(path)
            self.assertIsNotNone(result.bad_reason)
            self.assertEqual(result.bad_reason.category, "crash")
            self.assertIn("RuntimeError", result.bad_reason.message)
            self.assertIn("boom", result.bad_reason.message)
            self.assertEqual((result.findings, result.name_candidates, result.select_block_count),
                             ([], [], 0))
        finally:
            os.unlink(path)

    def test_normal_file_has_no_bad_reason(self):
        fd, path = tempfile.mkstemp(suffix=".sql")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("SELECT * FROM t1 WHERE ACCT_ID = '1';\n")
            result = scanner.scan_file(path)
            self.assertIsNone(result.bad_reason)
            self.assertEqual(len(result.findings), 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
