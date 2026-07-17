# -*- coding: utf-8 -*-
"""Unit tests for src/mask.py -- the --mask-literals splice/classification
logic. mask_text() is tested directly as a pure function (no filesystem
involved), and write_masked_files() is tested for its file-level
orchestration: in-place rewriting, encoding/BOM round-trip fidelity, and
the no-op cases (nothing maskable, missing offsets).

Run:
    python -m unittest tests.test_mask
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src.mask import mask_text, write_masked_files  # noqa: E402
from src.models.findings import Finding  # noqa: E402


def _finding(path, start, end):
    """Minimal Finding carrying just what masking consumes."""
    return Finding(severity="FINDING", file=path, line=1, column_name="C",
                   operator="=", value="", snippet="", encoding="utf-8",
                   in_comment="N", start_offset=start, end_offset=end)


class TestMaskText(unittest.TestCase):
    def test_single_quoted_literal(self):
        text = "ACCT_ID = '0000001'"
        span = (text.index("'"), len(text) - 1)
        masked, stats = mask_text(text, [span])
        self.assertEqual(masked, "ACCT_ID = '****'")
        self.assertEqual(stats, {"masked": 1, "skipped_overlap": 0, "skipped_unmaskable": 0})

    def test_double_quoted_literal_preserves_its_own_quote_char(self):
        text = 'ACCT_ID = "0000079"'
        span = (text.index('"'), len(text) - 1)
        masked, stats = mask_text(text, [span])
        self.assertEqual(masked, 'ACCT_ID = "****"')
        self.assertEqual(stats["masked"], 1)

    def test_unquoted_numeric_literal(self):
        text = "ACCT_ID = 12345"
        span = (text.index("12345"), len(text) - 1)
        masked, stats = mask_text(text, [span])
        self.assertEqual(masked, "ACCT_ID = 0000")
        self.assertEqual(stats["masked"], 1)

    def test_float_and_exponent_numeric_literal_shapes(self):
        # All three are legal `constant_` alternatives in the grammar
        # (DECIMAL_LITERAL, FLOAT_LITERAL/DEC_DOT_DEC, REAL_LITERAL) -- all
        # must mask to the same always-valid numeric placeholder.
        for literal in ("123.45", ".5", "1.5E10", "1.5e-3"):
            text = "ACCT_ID = " + literal
            span = (text.index(literal), len(text) - 1)
            masked, stats = mask_text(text, [span])
            self.assertEqual(masked, "ACCT_ID = 0000", msg=literal)
            self.assertEqual(stats["masked"], 1, msg=literal)

    def test_escaped_quote_inside_literal_masked_as_one_token(self):
        # 'it''s' is a single STRING_LITERAL token per the lexer grammar
        # (an embedded '' is an escaped quote, not two adjacent literals)
        # -- whole-span replacement must handle this correctly by
        # construction, not by looking for the "next" quote character.
        text = "NOTE = 'it''s'"
        span = (text.index("'"), len(text) - 1)
        masked, stats = mask_text(text, [span])
        self.assertEqual(masked, "NOTE = '****'")
        self.assertEqual(stats["masked"], 1)

    def test_multiple_non_overlapping_spans_in_source_order(self):
        text = "ACCT_ID IN ('0000001', '0000002')"
        first = text.index("'0000001'")
        second = text.index("'0000002'")
        spans = [(first, first + len("'0000001'") - 1),
                (second, second + len("'0000002'") - 1)]
        masked, stats = mask_text(text, spans)
        self.assertEqual(masked, "ACCT_ID IN ('****', '****')")
        self.assertEqual(stats["masked"], 2)

    def test_duplicate_span_deduped(self):
        text = "ACCT_ID = '0000001'"
        span = (text.index("'"), len(text) - 1)
        masked, stats = mask_text(text, [span, span])
        self.assertEqual(masked, "ACCT_ID = '****'")
        self.assertEqual(stats["masked"], 1)

    def test_overlapping_span_skipped_not_corrupted(self):
        text = "ACCT_ID = '0000001'"
        full = (text.index("'"), len(text) - 1)
        overlapping = (full[0] + 1, full[1])  # starts inside `full`
        warnings = []
        masked, stats = mask_text(text, [full, overlapping], warn=warnings.append)
        self.assertEqual(masked, "ACCT_ID = '****'")
        self.assertEqual(stats["skipped_overlap"], 1)
        self.assertTrue(warnings)

    def test_unmaskable_shape_skipped_not_corrupted(self):
        # A bare NULL keyword must never be masked even if a span for it
        # somehow reached mask_text (defense in depth -- see
        # _literal_replacement's docstring for why this matters).
        text = "ACCT_ID = NULL"
        span = (text.index("NULL"), len(text) - 1)
        warnings = []
        masked, stats = mask_text(text, [span], warn=warnings.append)
        self.assertEqual(masked, text)  # completely unchanged
        self.assertEqual(stats["skipped_unmaskable"], 1)
        self.assertTrue(warnings)

    def test_no_spans_is_a_no_op(self):
        text = "SELECT 1;"
        masked, stats = mask_text(text, [])
        self.assertEqual(masked, text)
        self.assertEqual(stats, {"masked": 0, "skipped_overlap": 0, "skipped_unmaskable": 0})


class TestWriteMaskedFiles(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def _write(self, name, content, encoding="utf-8"):
        path = os.path.join(self.d, name)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return path

    @staticmethod
    def _span_of(content, literal):
        start = content.index(literal)
        return start, start + len(literal) - 1

    def test_rewrites_file_in_place(self):
        content = "SELECT * FROM t WHERE ACCT_ID = '0000001';"
        path = self._write("report.sql", content)
        start, end = self._span_of(content, "'0000001'")
        findings = [_finding(path, start, end)]

        written = write_masked_files(findings)

        self.assertEqual(written, [path])
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "SELECT * FROM t WHERE ACCT_ID = '****';")

    def test_no_bom_introduced_when_original_has_none(self):
        # io_utils.read_text tries "utf-8-sig" first, which also silently
        # decodes a plain UTF-8 file with no BOM -- write_masked_files must
        # not mistake that for "this file should be written with a BOM".
        content = "SELECT * FROM t WHERE ACCT_ID = '0000001';"
        path = self._write("report.sql", content)
        start, end = self._span_of(content, "'0000001'")
        findings = [_finding(path, start, end)]

        written = write_masked_files(findings)

        with open(written[0], "rb") as f:
            raw = f.read()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))

    def test_bom_preserved_when_original_has_one(self):
        content = "SELECT * FROM t WHERE ACCT_ID = '0000001';"
        path = self._write("report.sql", content, encoding="utf-8-sig")
        start, end = self._span_of(content, "'0000001'")
        findings = [_finding(path, start, end)]

        written = write_masked_files(findings)

        with open(written[0], "rb") as f:
            raw = f.read()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))

    def test_file_with_no_maskable_spans_is_left_untouched(self):
        content = "SELECT * FROM t WHERE ACCT_ID = NULL;"
        path = self._write("report.sql", content)
        start, end = self._span_of(content, "NULL")
        findings = [_finding(path, start, end)]

        written = write_masked_files(findings)

        self.assertEqual(written, [])
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_finding_missing_offsets_is_ignored(self):
        content = "SELECT * FROM t WHERE ACCT_ID = '0000001';"
        path = self._write("report.sql", content)
        findings = [_finding(path, None, None)]

        written = write_masked_files(findings)

        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
