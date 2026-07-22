# -*- coding: utf-8 -*-
"""End-to-end CLI tests for the --query-similarity flag: the O(n^2)
similarity pass is opt-in, so refs_query_similarity.tsv must only exist
(and only be mentioned in summary.md) when the flag is given, and the
flag without --extract-metadata is a usage error.

Run:
    python -m unittest tests.test_cli_similarity
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


class TestQuerySimilarityFlag(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.sql_root = os.path.join(self.workdir, "sqlroot")
        os.mkdir(self.sql_root)
        with open(os.path.join(self.sql_root, "a.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT c1 FROM s1.t1 a JOIN s1.t2 b ON a.k = b.k WHERE a.c2 = 1;\n"
                    "SELECT c1 FROM s1.t1 a JOIN s1.t3 b ON a.k = b.k WHERE a.c2 = 1;\n")
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

    def test_extract_metadata_alone_writes_no_similarity_file(self):
        code = self._run([self.sql_root, "--extract-metadata"])
        self.assertIn(code, (0, 1))
        self.assertTrue(os.path.isfile("refs_query_identity.tsv"))
        self.assertFalse(os.path.exists("refs_query_similarity.tsv"))
        with open("summary.md", encoding="utf-8-sig") as f:
            summary = f.read()
        self.assertNotIn("refs_query_similarity.tsv", summary)
        self.assertIn("| Query similarity | OFF |", summary)

    def test_flag_writes_similarity_file_and_summary_pointer(self):
        code = self._run([self.sql_root, "--extract-metadata", "--query-similarity"])
        self.assertIn(code, (0, 1))
        self.assertTrue(os.path.isfile("refs_query_similarity.tsv"))
        with open("refs_query_similarity.tsv", encoding="utf-8-sig") as f:
            header = f.readline().strip()
        self.assertEqual(header, "core_id_a\tcore_id_b\tsimilarity\tshared_facts\tonly_in_a\tonly_in_b")
        with open("summary.md", encoding="utf-8-sig") as f:
            summary = f.read()
        self.assertIn("refs_query_similarity.tsv", summary)
        self.assertIn("| Query similarity | ON |", summary)

    def test_flag_without_extract_metadata_is_a_usage_error(self):
        code = self._run([self.sql_root, "--query-similarity"])
        self.assertEqual(code, 2)  # argparse usage-error exit code


if __name__ == "__main__":
    unittest.main()
