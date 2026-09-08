# -*- coding: utf-8 -*-
"""Unit tests for relations.py (Feature 3: JOIN relationship extraction).

Pins down the double-counting bugs caught during development: an explicit
JOIN...ON's own predicate is independently re-visited as an orphaned
search_condition tree (statement_driver's Tier 2 resync), and a
comma-join's structural edge carries no predicate at all -- both of these
would silently double-count every ordinary JOIN/comma-join if not
deliberately deduped in engine.py's pre_chunk_hook (see there and
relations.py's module docstring for the full explanation).

Run:
    python -m unittest tests.test_relations
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial.models.relations import RelationEdge  # noqa: E402
from metchurial.references import relations  # noqa: E402
from metchurial import engine as scanner  # noqa: E402
from metchurial.models.options import ScanOptions  # noqa: E402


def relation_edges_for(text):
    fd, path = tempfile.mkstemp(suffix=".sql")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        result = scanner.scan_file(path, ScanOptions(extract_relations=True))
        return result.relation_edges
    finally:
        os.unlink(path)


class TestNoDoubleCounting(unittest.TestCase):
    def test_explicit_join_produces_exactly_one_edge(self):
        edges = relation_edges_for("SELECT * FROM t1 x JOIN t2 y ON x.id = y.id;")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].join_type, "JOIN")
        self.assertIn("id", edges[0].predicate)

    def test_comma_join_produces_exactly_one_edge(self):
        edges = relation_edges_for("SELECT * FROM t3 tb1, t4 tb2 WHERE tb1.id = tb2.id;")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].join_type, "WHERE-IMPLICIT")
        self.assertIn("T3.ID", edges[0].predicate)
        self.assertIn("T4.ID", edges[0].predicate)

    def test_left_join_produces_exactly_one_edge(self):
        edges = relation_edges_for("SELECT * FROM t1 x LEFT JOIN t2 y ON x.id = y.id;")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].join_type, "LEFT")

    def test_comma_join_with_no_where_condition_is_unrecorded(self):
        # Documented limitation: a degenerate cross-join with nothing
        # linking the two tables produces no edge at all (not a wrong
        # answer, just nothing to report).
        edges = relation_edges_for("SELECT * FROM t1 a, t2 b;")
        self.assertEqual(edges, [])

    def test_comma_joined_self_join_produces_an_edge(self):
        # Regression guard: a real self-join (two aliases of the same
        # table) used to be silently dropped -- the same-table filter
        # compared resolved (schema, table) strings, which are identical
        # for e1/e2 even though they're two distinct TableRef instances.
        edges = relation_edges_for(
            "SELECT * FROM emp e1, emp e2 WHERE e1.mgr_id = e2.emp_id;")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].join_type, "WHERE-IMPLICIT")
        self.assertEqual((edges[0].table_a, edges[0].table_b), ("EMP", "EMP"))

    def test_same_alias_both_sides_is_still_not_a_join(self):
        # The filter this replaces still needs to catch the case it was
        # originally meant for: a single table's own alias and its bare
        # table name both resolve to the *same* TableRef (see
        # QueryBlock.add_table), so comparing two of that table's own
        # columns must not be misread as a join.
        edges = relation_edges_for(
            "SELECT * FROM emp e WHERE e.hire_date = emp.term_date;")
        self.assertEqual(edges, [])


class TestAggregateEdges(unittest.TestCase):
    def test_unordered_pair_collapses(self):
        edges = [
            RelationEdge(file="f", line=1, table_a_schema="S", table_a="T1",
                         table_b_schema="S", table_b="T2", join_type="JOIN", predicate="a"),
            RelationEdge(file="f", line=1, table_a_schema="S", table_a="T2",
                         table_b_schema="S", table_b="T1", join_type="JOIN", predicate="b"),
        ]
        agg = relations.aggregate_edges(edges)
        self.assertEqual(len(agg), 1)
        self.assertEqual(agg[0].join_count, 2)
        self.assertEqual(agg[0].predicates, ("a", "b"))

    def test_sorted_by_join_count_desc(self):
        edges = [
            RelationEdge(file="f", line=1, table_a_schema="S", table_a="T1",
                         table_b_schema="S", table_b="T2", join_type="JOIN", predicate=""),
            RelationEdge(file="f", line=2, table_a_schema="S", table_a="T3",
                         table_b_schema="S", table_b="T4", join_type="JOIN", predicate=""),
            RelationEdge(file="f", line=3, table_a_schema="S", table_a="T3",
                         table_b_schema="S", table_b="T4", join_type="JOIN", predicate=""),
        ]
        agg = relations.aggregate_edges(edges)
        self.assertEqual(agg[0].table_a, "T3")
        self.assertEqual(agg[0].join_count, 2)
        self.assertEqual(agg[1].table_a, "T1")
        self.assertEqual(agg[1].join_count, 1)


if __name__ == "__main__":
    unittest.main()
