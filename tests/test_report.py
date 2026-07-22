# -*- coding: utf-8 -*-
"""Unit tests for report.py's Markdown-writing helpers -- specifically the
truncation pointer each grouped/capped section prints when it has more
rows than MAX_GROUPED_VALUES ("... see <file>"), which must name the TSV
that section's own uncapped detail actually lives in, not a hardcoded one
borrowed from a different section.

Run:
    python -m unittest tests.test_report
"""

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial.models.relations import RelationRollup  # noqa: E402
from metchurial.report import _format_grouped_values, _write_relations  # noqa: E402


class TestFormatGroupedValuesPointer(unittest.TestCase):
    def test_defaults_to_findings_tsv(self):
        values = [str(i) for i in range(15)]
        text = _format_grouped_values(values)
        self.assertIn("findings.tsv", text)

    def test_accepts_a_different_pointer_file(self):
        values = [str(i) for i in range(15)]
        text = _format_grouped_values(values, "refs_relations.tsv")
        self.assertIn("refs_relations.tsv", text)
        self.assertNotIn("findings.tsv", text)

    def test_no_pointer_when_under_the_cap(self):
        text = _format_grouped_values(["a", "b"], "refs_relations.tsv")
        self.assertNotIn(".tsv", text)


class TestWriteRelationsPredicateTruncationPointer(unittest.TestCase):
    def test_truncated_predicates_point_at_refs_relations_tsv_not_findings_tsv(self):
        row = RelationRollup(
            table_a_schema="S1", table_a="T1", table_b_schema="S1", table_b="T2",
            join_count=5, predicates=tuple("PRED{} =".format(i) for i in range(15)))
        out = io.StringIO()
        _write_relations(out, [row])
        text = out.getvalue()
        self.assertIn("refs_relations.tsv", text)
        self.assertNotIn("findings.tsv", text)


if __name__ == "__main__":
    unittest.main()
