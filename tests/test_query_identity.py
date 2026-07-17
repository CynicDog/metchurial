# -*- coding: utf-8 -*-
"""End-to-end tests for query_identity.py (issue #8) against the 18-file
stress corpus at tests/fixtures/20-37, run through the real scan_file()
pipeline -- not just the module's own functions in isolation, since the
whole point is that core_id assignment survives the full tiered-parser/
token-scan pipeline, not just a hand-built QueryBlock list.

Each fixture's own header comment documents which cluster it belongs to
and why -- this file is the assertion of that documented intent. See
query_identity.py's module docstring for the design (canonical table set
+ join-type multiset + alias-resolved relationship/predicate facts,
hashed for exact matches, Jaccard-scored for near-misses).

Run:
    python -m unittest tests.test_query_identity
"""

import os
import sys
import unittest

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src import scan as scanner  # noqa: E402
from src.references import query_identity  # noqa: E402

CORE_A = ["20_query_identity_base.sql", "21_query_identity_alias_variant.sql",
         "22_query_identity_extra_column.sql", "23_query_identity_derived_column_variant.sql",
         "30_query_identity_comma_join_variant.sql", "31_query_identity_join_order_variant.sql"]
CORE_B = ["34_query_identity_core_b_base.sql", "35_query_identity_core_b_alias_variant.sql",
         "36_query_identity_core_b_extra_column.sql"]
NEAR_MISS = ["24_query_near_miss_extra_join.sql", "25_query_near_miss_different_predicate.sql",
            "32_query_near_miss_join_type_change.sql"]
NEGATIVE = ["26_query_distinct_unrelated_domain.sql", "27_query_distinct_single_table.sql"]
HARD_CASES = ["33_query_hard_case_subquery_rewrite.sql", "37_query_hard_case_union_all.sql"]


def _identity_rows(filename):
    path = os.path.join(FIXTURES_DIR, filename)
    result = scanner.scan_file(path, scanner.DEFAULT_COLUMNS, set(), extract_query_identity=True)
    assert result.bad_reason is None, (filename, result.bad_reason)
    return result.identity_rows


def _core_id(filename):
    """Every fixture in this corpus is exactly one real statement -- one
    identity row once the trailing-EOF-chunk artifact is filtered (see
    scan.py)."""
    rows = _identity_rows(filename)
    assert len(rows) == 1, (filename, rows)
    return rows[0].core_id


def _fact_set(filename):
    rows = _identity_rows(filename)
    return rows[0].fact_set


class TestCoreAClusterCollapses(unittest.TestCase):
    """20-23/30/31 differ only in things a core signature must ignore:
    alias renaming, an extra SELECT column, a differently-calculated
    derived column, a comma-join rewrite of one edge, and a permuted
    FROM-clause order -- all must land on the same core_id as the base."""

    def test_every_core_a_variant_shares_one_core_id(self):
        ids = {f: _core_id(f) for f in CORE_A}
        distinct = set(ids.values())
        self.assertEqual(len(distinct), 1, ids)


class TestCoreBClusterCollapsesAndIsDistinctFromCoreA(unittest.TestCase):
    def test_every_core_b_variant_shares_one_core_id(self):
        ids = {f: _core_id(f) for f in CORE_B}
        self.assertEqual(len(set(ids.values())), 1, ids)

    def test_core_b_differs_from_core_a(self):
        self.assertNotEqual(_core_id(CORE_B[0]), _core_id(CORE_A[0]))


class TestNearMissesGetDistinctIdsButScoreSimilar(unittest.TestCase):
    """An added JOIN, a changed predicate set, and a single join-type flip
    (LEFT OUTER -> INNER) must each produce a core_id different from
    CORE_A's (and from each other), but score highly similar against it --
    the smallest of the three, the join-type flip, should score highest,
    since it's the smallest possible edit against an otherwise-identical
    statement."""

    def test_each_near_miss_has_its_own_distinct_core_id(self):
        core_a_id = _core_id(CORE_A[0])
        ids = [_core_id(f) for f in NEAR_MISS]
        for f, cid in zip(NEAR_MISS, ids):
            self.assertNotEqual(cid, core_a_id, f)
        self.assertEqual(len(set(ids)), len(ids), ids)  # also distinct from each other

    def test_each_near_miss_scores_highly_similar_to_core_a(self):
        core_a_facts = _fact_set(CORE_A[0])
        for f in NEAR_MISS:
            score = query_identity._jaccard(core_a_facts, _fact_set(f))
            self.assertGreater(score, 0.5, f)

    def test_join_type_flip_is_the_smallest_edit(self):
        core_a_facts = _fact_set(CORE_A[0])
        flip_score = query_identity._jaccard(core_a_facts, _fact_set("32_query_near_miss_join_type_change.sql"))
        predicate_score = query_identity._jaccard(
            core_a_facts, _fact_set("25_query_near_miss_different_predicate.sql"))
        self.assertGreater(flip_score, predicate_score)


class TestNegativeControlsScoreLow(unittest.TestCase):
    def test_negative_controls_have_their_own_distinct_ids(self):
        ids = [_core_id(f) for f in NEGATIVE]
        self.assertNotIn(_core_id(CORE_A[0]), ids)
        self.assertNotIn(_core_id(CORE_B[0]), ids)
        self.assertEqual(len(set(ids)), len(ids))

    def test_negative_controls_score_low_against_both_clusters(self):
        core_a_facts = _fact_set(CORE_A[0])
        core_b_facts = _fact_set(CORE_B[0])
        for f in NEGATIVE:
            facts = _fact_set(f)
            self.assertLess(query_identity._jaccard(core_a_facts, facts), 0.3, f)
            self.assertLess(query_identity._jaccard(core_b_facts, facts), 0.3, f)


class TestHardCasesDoNotFalselyCollapse(unittest.TestCase):
    """These are the two constructs a purely structural signature cannot
    and should not be expected to solve -- documented non-goals, not bugs.
    See each fixture's own header comment."""

    def test_exists_subquery_rewrite_does_not_match_core_a(self):
        # Same base tables/intent as CORE_A, but the TBSTAT relationship
        # is a correlated EXISTS subquery, not a JOIN -- resolve_qualifier
        # only checks the innermost enclosing block's own alias_map, so
        # the correlated reference to the outer query's alias doesn't
        # resolve, and no relationship fact forms for it. Must not match.
        self.assertNotEqual(
            _core_id("33_query_hard_case_subquery_rewrite.sql"), _core_id(CORE_A[0]))

    def test_union_all_merges_both_branches_into_one_signature(self):
        # Concrete resolution of the "which signature does a UNION get"
        # design question: one signature per chunk, both branches' tables
        # merged -- so this fixture's table set is CORE_B's own tables
        # plus whatever the second, diverging branch (TBCODE) adds. Note
        # JOINTYPE facts encode an exact count ("JOINTYPE|INNER=1"), so
        # they don't compose as a clean subset across merged branches the
        # way table/relationship facts do -- the merged statement's join-
        # type distribution genuinely differs from either branch alone,
        # which is the correct nuance, not a gap.
        union_facts = _fact_set("37_query_hard_case_union_all.sql")
        core_b_tables = {f for f in _fact_set(CORE_B[0]) if f.startswith("TBL|")}
        union_tables = {f for f in union_facts if f.startswith("TBL|")}
        self.assertNotEqual(_core_id("37_query_hard_case_union_all.sql"), _core_id(CORE_B[0]))
        self.assertTrue(core_b_tables <= union_tables, "CORE_B's own tables should be a subset")
        self.assertTrue(any("TBCODE" in f for f in union_tables))


class TestComputeSimilarityCorpusWide(unittest.TestCase):
    """compute_similarity operates on the whole corpus' identity rows at
    once (see cli.py -- called once after scan_tree(), not per file)."""

    def test_core_a_and_near_miss_pair_appears_above_threshold(self):
        all_rows = []
        for f in CORE_A[:1] + NEAR_MISS:
            all_rows.extend(_identity_rows(f))
        pairs = query_identity.compute_similarity(all_rows, threshold=0.5)
        core_a_id = _core_id(CORE_A[0])
        involving_core_a = [p for p in pairs if core_a_id in (p.core_id_a, p.core_id_b)]
        self.assertEqual(len(involving_core_a), len(NEAR_MISS))

    def test_identical_core_ids_are_never_scored_against_themselves(self):
        all_rows = []
        for f in CORE_A:
            all_rows.extend(_identity_rows(f))
        pairs = query_identity.compute_similarity(all_rows, threshold=0.0)
        self.assertEqual(pairs, [])  # one distinct core_id -> no pairs at all


if __name__ == "__main__":
    unittest.main()
