# -*- coding: utf-8 -*-
"""Tests for --quarantine: quarantine.quarantine_non_matching's own
file-moving logic, plus the CLI wiring (flag, quarantine_manifest.tsv,
summary.md's Quarantine row).

Run:
    python -m unittest tests.test_quarantine
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
from metchurial import quarantine  # noqa: E402


class TestQuarantineNonMatching(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def _write(self, rel_path, content="x"):
        full = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return full

    def test_moves_non_matching_recursively_preserving_relative_path(self):
        self._write("a.sql")
        self._write("notes.docx")
        self._write("sub/dir/readme.md")
        self._write("sub/dir/b.sql")
        quarantine_dir = os.path.join(self.root, "quarantine")

        rows = quarantine.quarantine_non_matching(self.root, ("sql",), quarantine_dir)

        moved = {os.path.relpath(r.quarantined_file, quarantine_dir) for r in rows}
        self.assertEqual(moved, {"notes.docx", os.path.join("sub", "dir", "readme.md")})
        self.assertTrue(os.path.isfile(os.path.join(self.root, "a.sql")))
        self.assertTrue(os.path.isfile(os.path.join(self.root, "sub", "dir", "b.sql")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "notes.docx")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "sub", "dir", "readme.md")))

    def test_does_not_descend_into_quarantine_dir_itself(self):
        self._write("notes.docx")
        quarantine_dir = os.path.join(self.root, "quarantine")

        first = quarantine.quarantine_non_matching(self.root, ("sql",), quarantine_dir)
        self.assertEqual(len(first), 1)
        # Re-running must not re-discover the file it just moved into
        # quarantine_dir (which sits inside root) and move it again.
        second = quarantine.quarantine_non_matching(self.root, ("sql",), quarantine_dir)
        self.assertEqual(second, [])

    def test_repeated_move_to_same_relative_path_does_not_clobber(self):
        quarantine_dir = os.path.join(self.root, "quarantine")
        self._write("notes.docx", content="first")
        quarantine.quarantine_non_matching(self.root, ("sql",), quarantine_dir)
        self._write("notes.docx", content="second")
        rows = quarantine.quarantine_non_matching(self.root, ("sql",), quarantine_dir)

        self.assertEqual(len(rows), 1)
        with open(rows[0].quarantined_file, encoding="utf-8") as f:
            self.assertEqual(f.read(), "second")
        original_dest = os.path.join(quarantine_dir, "notes.docx")
        with open(original_dest, encoding="utf-8") as f:
            self.assertEqual(f.read(), "first")

    def test_exclude_paths_are_never_moved(self):
        excluded = self._write("summary.md")
        quarantine_dir = os.path.join(self.root, "quarantine")

        rows = quarantine.quarantine_non_matching(
            self.root, ("sql",), quarantine_dir, exclude_paths={os.path.abspath(excluded)})

        self.assertEqual(rows, [])
        self.assertTrue(os.path.isfile(excluded))

    def test_no_non_matching_files_returns_empty_and_no_dir_created(self):
        self._write("a.sql")
        quarantine_dir = os.path.join(self.root, "quarantine")

        rows = quarantine.quarantine_non_matching(self.root, ("sql",), quarantine_dir)

        self.assertEqual(rows, [])
        self.assertFalse(os.path.exists(quarantine_dir))


class TestQuarantineCLI(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.sql_root = os.path.join(self.workdir, "sqlroot")
        os.makedirs(os.path.join(self.sql_root, "sub"))
        with open(os.path.join(self.sql_root, "a.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT 1 FROM t1;\n")
        with open(os.path.join(self.sql_root, "notes.docx"), "w", encoding="utf-8") as f:
            f.write("not sql\n")
        with open(os.path.join(self.sql_root, "sub", "readme.md"), "w", encoding="utf-8") as f:
            f.write("# not sql either\n")
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

    def test_flag_off_leaves_tree_untouched(self):
        self._run([self.sql_root, "--extensions", "sql"])
        self.assertFalse(os.path.exists("quarantine"))
        self.assertFalse(os.path.exists("quarantine_manifest.tsv"))
        self.assertTrue(os.path.isfile(os.path.join(self.sql_root, "notes.docx")))
        with open("summary.md", encoding="utf-8-sig") as f:
            self.assertIn("| Quarantine | OFF |", f.read())

    def test_flag_on_moves_non_matching_and_writes_manifest(self):
        self._run([self.sql_root, "--extensions", "sql", "--quarantine"])

        self.assertFalse(os.path.isfile(os.path.join(self.sql_root, "notes.docx")))
        self.assertFalse(os.path.isfile(os.path.join(self.sql_root, "sub", "readme.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.sql_root, "a.sql")))
        self.assertTrue(os.path.isfile(os.path.join("quarantine", "notes.docx")))
        self.assertTrue(os.path.isfile(os.path.join("quarantine", "sub", "readme.md")))

        with open("quarantine_manifest.tsv", encoding="utf-8-sig") as f:
            manifest = f.read()
        self.assertIn("original_file\tquarantined_file", manifest)
        self.assertIn("notes.docx", manifest)

        with open("summary.md", encoding="utf-8-sig") as f:
            self.assertIn("| Quarantine | ON |", f.read())

    def test_scan_root_as_cwd_does_not_quarantine_own_output_artifacts(self):
        os.chdir(self.sql_root)
        self._run([".", "--extensions", "sql", "--quarantine"])

        # summary.md/findings.tsv/etc. are non-.sql but reserved -- must
        # survive right where the scan wrote them, not end up quarantined.
        self.assertTrue(os.path.isfile("summary.md"))
        self.assertTrue(os.path.isfile("findings.tsv"))
        self.assertTrue(os.path.isfile("quarantine_manifest.tsv"))
        self.assertTrue(os.path.isfile(os.path.join("quarantine", "notes.docx")))


if __name__ == "__main__":
    unittest.main()
