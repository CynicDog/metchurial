# -*- coding: utf-8 -*-
"""Unit tests for select_blocks.py (Feature 2: SELECT-block counting/split).

Pins down the regression this feature exists to guard against: a CTE's own
body SELECT gets independently re-surfaced by the tiered parsing driver as
if it were its own standalone top-level statement (see table_scan.py's
module docstring) -- classify_chunk works at the chunk level specifically
so this never inflates the count, without needing to patch that bug.

Run:
    python -m unittest tests.test_select_blocks
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial.parsing.statement_driver import lex_file, chunk_ranges  # noqa: E402
from metchurial.split import select_blocks as sb  # noqa: E402


def _classify_all(sql):
    all_tokens, _ = lex_file(sql)
    ranges = chunk_ranges(all_tokens)
    return [sb.classify_chunk(all_tokens, s, e) for s, e in ranges]


class TestClassifyChunk(unittest.TestCase):
    def test_plain_select_is_a_block(self):
        self.assertEqual(_classify_all("SELECT * FROM t1;"), [True])

    def test_non_select_statements_are_not_blocks(self):
        self.assertEqual(_classify_all("UPDATE t1 SET x=1;"), [False])
        self.assertEqual(_classify_all("INSERT INTO t1 VALUES (1);"), [False])
        self.assertEqual(_classify_all("DELETE FROM t1;"), [False])

    def test_cte_prologue_counts_as_one_block_not_two(self):
        # The regression guard: without chunk-level classification, the
        # tiered driver independently re-surfaces the CTE body as if it
        # were its own standalone top-level SELECT.
        self.assertEqual(
            _classify_all("WITH cte AS (SELECT id FROM t1) SELECT * FROM cte;"),
            [True])

    def test_multiple_ctes_still_one_block(self):
        self.assertEqual(
            _classify_all(
                "WITH c1 AS (SELECT id FROM t1), c2 AS (SELECT id FROM t2) "
                "SELECT * FROM c1, c2;"),
            [True])

    def test_mixed_statements_classified_independently(self):
        self.assertEqual(
            _classify_all("SELECT * FROM t1; UPDATE t2 SET x=1; SELECT * FROM t3;"),
            [True, False, True])

    def test_malformed_with_never_reaching_select_is_not_a_block(self):
        self.assertEqual(_classify_all("WITH cte AS (1);"), [False])


class TestChunkSourceText(unittest.TestCase):
    def test_split_files_have_no_leading_blank_line(self):
        text = "SELECT * FROM t1;\nUPDATE t2 SET x=1;\nSELECT * FROM t3;\n"
        all_tokens, _ = lex_file(text)
        ranges = chunk_ranges(all_tokens)
        blocks = sb.select_block_ranges(all_tokens, ranges)
        self.assertEqual(len(blocks), 2)
        texts = [sb.chunk_source_text(text, all_tokens, s, e) for s, e in blocks]
        self.assertEqual(texts, ["SELECT * FROM t1;", "SELECT * FROM t3;"])


class TestWriteSplitFiles(unittest.TestCase):
    def test_writes_one_file_per_block_leaves_original_untouched(self):
        d = tempfile.mkdtemp()
        try:
            text = "SELECT * FROM t1;\nUPDATE t2 SET x=1;\nSELECT * FROM t3;\n"
            path = os.path.join(d, "sample.sql")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            all_tokens, _ = lex_file(text)
            blocks = sb.select_block_ranges(all_tokens, chunk_ranges(all_tokens))

            written = sb.write_split_files(path, text, all_tokens, blocks)
            self.assertEqual(len(written), 2)
            self.assertTrue(os.path.basename(written[0]).startswith("sample-01"))
            self.assertTrue(os.path.basename(written[1]).startswith("sample-02"))
            with open(written[0], encoding="utf-8") as f:
                self.assertEqual(f.read(), "SELECT * FROM t1;")
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), text)  # original untouched
        finally:
            import shutil
            shutil.rmtree(d)

    def test_no_op_on_a_single_block(self):
        # A lone SELECT block has nowhere to be split apart from -- a
        # "-01.sql" copy would just duplicate the original under a new
        # name, so write_split_files leaves it alone.
        d = tempfile.mkdtemp()
        try:
            text = "SELECT * FROM t1;\n"
            path = os.path.join(d, "sample.sql")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            all_tokens, _ = lex_file(text)
            blocks = sb.select_block_ranges(all_tokens, chunk_ranges(all_tokens))
            self.assertEqual(len(blocks), 1)

            written = sb.write_split_files(path, text, all_tokens, blocks)
            self.assertEqual(written, [])
            self.assertFalse(os.path.exists(os.path.join(d, "sample-01.sql")))
        finally:
            import shutil
            shutil.rmtree(d)

    def test_no_op_on_zero_blocks(self):
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, "sample.sql")
            with open(path, "w", encoding="utf-8") as f:
                f.write("UPDATE t1 SET x=1;")
            self.assertEqual(sb.write_split_files(path, "UPDATE t1 SET x=1;", [], []), [])
        finally:
            import shutil
            shutil.rmtree(d)

    def test_refuses_to_resplit_already_split_output(self):
        self.assertTrue(sb.looks_like_split_output("sample-01.sql"))
        self.assertTrue(sb.looks_like_split_output("sample-12.sql"))
        self.assertFalse(sb.looks_like_split_output("sample.sql"))
        self.assertFalse(sb.looks_like_split_output("sample-1.sql"))  # single digit -- not our pattern

        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, "sample-01.sql")
            text = "SELECT * FROM t1; SELECT * FROM t2;"
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            all_tokens, _ = lex_file(text)
            blocks = sb.select_block_ranges(all_tokens, chunk_ranges(all_tokens))
            self.assertEqual(sb.write_split_files(path, text, all_tokens, blocks), [])
        finally:
            import shutil
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
