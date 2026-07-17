# -*- coding: utf-8 -*-
"""Unit tests for statement_driver.py's own plumbing (chunk-level driver
loop), independent of any specific visitor's semantics. `parse_file`'s
`pre_chunk_hook`/`parse_chunk`'s `extra_visitors` are what table_scan.py
and reference_visitor.py hook into for Features 1 and 3 -- this pins down
that the plumbing itself (not any particular feature built on it) behaves
correctly: called once per chunk, default `None`/`()` changes nothing.

Run:
    python -m unittest tests.test_statement_driver
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src.detect.extractor_visitor import ExtractorVisitor  # noqa: E402
from src.parsing.statement_driver import parse_file  # noqa: E402
from src.detect.supplementary_checks import make_token_scan_fallback  # noqa: E402


class _RecordingVisitor(object):
    def __init__(self):
        self.visited = []

    def visit(self, tree):
        self.visited.append(tree.getText())


def _run(text, pre_chunk_hook=None):
    hits = []
    visitor = ExtractorVisitor(["ACCT_ID"], lambda col, op, val, line, so, eo: hits.append(val))
    fallback = make_token_scan_fallback(["ACCT_ID"], lambda col, op, val, line, so, eo: hits.append(val))
    parse_file(text, visitor, fallback, pre_chunk_hook=pre_chunk_hook)
    return hits


class TestPreChunkHook(unittest.TestCase):
    def test_default_none_changes_nothing(self):
        hits = _run("SELECT * FROM t1 WHERE ACCT_ID = '1'; SELECT * FROM t2 WHERE ACCT_ID = '2';")
        self.assertEqual(hits, ["'1'", "'2'"])

    def test_called_once_per_chunk(self):
        calls = []

        def hook(all_tokens, start, end):
            calls.append((start, end))
            return ()

        _run("SELECT * FROM t1 WHERE ACCT_ID = '1'; SELECT * FROM t2 WHERE ACCT_ID = '2';",
            pre_chunk_hook=hook)
        self.assertEqual(len(calls), 2)

    def test_extra_visitor_sees_every_committed_tree(self):
        extra = _RecordingVisitor()

        def hook(all_tokens, start, end):
            return (extra,)

        hits = _run("SELECT * FROM t1 WHERE ACCT_ID = '1';", pre_chunk_hook=hook)
        self.assertEqual(hits, ["'1'"])
        self.assertTrue(extra.visited)  # the extra visitor got at least one tree too

    def test_extra_visitor_does_not_affect_primary_visitor_output(self):
        extra = _RecordingVisitor()
        hits = _run("SELECT * FROM t1 WHERE ACCT_ID = '1';",
                    pre_chunk_hook=lambda all_tokens, start, end: (extra,))
        hits_without_extra = _run("SELECT * FROM t1 WHERE ACCT_ID = '1';")
        self.assertEqual(hits, hits_without_extra)


if __name__ == "__main__":
    unittest.main()
