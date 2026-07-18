# -*- coding: utf-8 -*-
"""Integration tests for Feature 1 (schema/table/column reference
extraction) through scan_file's actual pre_chunk_hook/ReferenceVisitor
wiring -- table_scan.py's own unit tests (tests/test_table_scan.py) cover
the token-scan engine in isolation; this covers the wiring that connects
it to scan_file's `extract_table_refs`/`extract_column_refs` flags,
matching what a real --extract-refs run produces.

Run:
    python -m unittest tests.test_reference_extraction
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import engine as scanner  # noqa: E402
from metchurial.models.options import ScanOptions  # noqa: E402


def refs_for(text, extract_table_refs=True, extract_column_refs=True):
    fd, path = tempfile.mkstemp(suffix=".sql")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        result = scanner.scan_file(path, ScanOptions(
            extract_table_refs=extract_table_refs, extract_column_refs=extract_column_refs))
        return result
    finally:
        os.unlink(path)


class TestTableRefs(unittest.TestCase):
    def test_schema_qualified_table_with_alias(self):
        table_refs = refs_for("SELECT * FROM schema1.table1 a WHERE a.x = 1;").table_uses
        self.assertEqual(len(table_refs), 1)
        self.assertEqual(table_refs[0].schema, "SCHEMA1")
        self.assertEqual(table_refs[0].table, "TABLE1")

    def test_join_second_table_included_despite_broken_grammar(self):
        tables = {r.table for r in refs_for("SELECT * FROM t1 a JOIN t2 b ON a.x=b.y;").table_uses}
        self.assertEqual(tables, {"T1", "T2"})

    def test_disabled_by_default(self):
        result = refs_for("SELECT * FROM t1;", extract_table_refs=False, extract_column_refs=False)
        self.assertEqual(result.table_uses, [])
        self.assertEqual(result.column_uses, [])


class TestColumnRefs(unittest.TestCase):
    def test_qualified_column_resolves_to_its_table(self):
        refs = refs_for("SELECT a.ACCT_ID FROM schema1.table1 a;")
        col_refs = [r for r in refs.column_uses if r.column == "ACCT_ID"]
        self.assertEqual(len(col_refs), 1)
        self.assertEqual(col_refs[0].schema, "SCHEMA1")
        self.assertEqual(col_refs[0].table, "TABLE1")

    def test_bare_column_gets_placeholder(self):
        refs = refs_for("SELECT x FROM t1;")
        col_refs = [r for r in refs.column_uses if r.column == "X"]
        self.assertEqual(len(col_refs), 1)
        self.assertEqual(col_refs[0].table, "(no-table)")

    def test_existing_hit_detection_still_fires_alongside_ref_extraction(self):
        # Feature 1 shouldn't change sensitive-column comparison detection's
        # own behavior when both are requested in the same scan_file call.
        fd, path = tempfile.mkstemp(suffix=".sql")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("SELECT * FROM t1 a WHERE a.ACCT_ID = '0000001';")
            result = scanner.scan_file(path, ScanOptions(
                extract_table_refs=True, extract_column_refs=True))
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].value, "'0000001'")
            self.assertTrue(any(r.table == "T1" for r in result.table_uses))
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
