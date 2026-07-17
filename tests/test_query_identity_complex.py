# -*- coding: utf-8 -*-
"""Complex-query hardening tests for query_identity.py, run through the
real scan_file() pipeline on inline SQL.

Covers the enterprise canonicalization contract: two statements are the
same core query iff they share tables, join topology and types, filter
predicates, and grouping -- SELECT-list projection, aliasing, derived-
column arithmetic, formatting, literal values, and ORDER BY never
discriminate. Also pins the constructs that historically broke the
signature silently: GROUP BY in aggregate (COUNT/MAX) statements,
reserved-keyword CTE/table names (BASE, ...), and multi-CTE statements.

Deliberate exclusions (HAVING, ORDER BY, the SELECT list) and the
supplementary columns field are pinned so a future behavior change is a
conscious one.

Run:
    python -m unittest tests.test_query_identity_complex
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src  # noqa: E402  (bootstraps generated/ onto sys.path)
from src import scan as scanner  # noqa: E402


def _identity_rows(sql):
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write(sql)
        path = f.name
    try:
        result = scanner.scan_file(path, scanner.DEFAULT_COLUMNS, set(),
                                   extract_query_identity=True)
        assert result.bad_reason is None, result.bad_reason
        return result.identity_rows
    finally:
        os.unlink(path)


def _core_id(sql):
    rows = _identity_rows(sql)
    assert len(rows) == 1, rows
    return rows[0].core_id


def _facts(sql):
    rows = _identity_rows(sql)
    assert len(rows) == 1, rows
    return rows[0].fact_set


AGG_BASE = ("SELECT a.dept_cd, COUNT(a.emp_id), MAX(a.sal) FROM tbemp a "
            "JOIN tbdept b ON a.dept_cd = b.dept_cd "
            "WHERE a.stat = 'A' GROUP BY a.dept_cd;")


class TestGroupByIsPartOfTheSignature(unittest.TestCase):
    """GROUP BY items are signature facts -- statements differing only in
    grouping are different core queries, including in aggregate
    (COUNT/MAX) statements, which parse as one clean tree since the
    grammar's function_name rule accepts those reserved names."""

    def test_different_group_by_columns_do_not_collapse(self):
        variant = AGG_BASE.replace("GROUP BY a.dept_cd", "GROUP BY a.stat")
        self.assertNotEqual(_core_id(AGG_BASE), _core_id(variant))

    def test_group_by_vs_no_group_by_do_not_collapse(self):
        no_group = ("SELECT a.dept_cd FROM tbemp a "
                    "JOIN tbdept b ON a.dept_cd = b.dept_cd WHERE a.stat = 'A';")
        with_group = no_group.replace(";", " GROUP BY a.dept_cd;")
        self.assertNotEqual(_core_id(no_group), _core_id(with_group))

    def test_extra_group_by_column_does_not_collapse(self):
        wider = AGG_BASE.replace("GROUP BY a.dept_cd", "GROUP BY a.dept_cd, a.stat")
        self.assertNotEqual(_core_id(AGG_BASE), _core_id(wider))

    def test_alias_renaming_keeps_group_by_signature(self):
        renamed = (AGG_BASE.replace("tbemp a", "tbemp emp").replace("tbdept b", "tbdept d")
                   .replace("a.", "emp.").replace("b.", "d."))
        self.assertEqual(_core_id(AGG_BASE), _core_id(renamed))

    def test_group_by_facts_resolve_aliases_to_real_tables(self):
        facts = _facts(AGG_BASE)
        self.assertIn("GROUPBY|TBEMP.DEPT_CD", facts)

    def test_unqualified_group_by_column_still_contributes_a_fact(self):
        sql = "SELECT dept_cd, COUNT(emp_id) FROM tbemp GROUP BY dept_cd;"
        self.assertIn("GROUPBY|DEPT_CD", _facts(sql))

    def test_order_by_never_discriminates(self):
        ordered = AGG_BASE.replace(";", " ORDER BY a.dept_cd DESC;")
        self.assertEqual(_core_id(AGG_BASE), _core_id(ordered))


CTE_BASE = (
    "WITH base AS (SELECT a.id, a.amt FROM tbord a WHERE a.st = 'A'),\n"
    "     agg AS (SELECT b.id, SUM(b.qty) qty FROM tbitem b GROUP BY b.id)\n"
    "SELECT x.id, x.amt FROM base x LEFT JOIN agg y ON x.id = y.id WHERE x.amt > 0;"
)


class TestReservedKeywordCteNames(unittest.TestCase):
    """`base` lexes as the reserved token BASE, not ID -- CTE/table
    discovery accepts it by position (looks_like_name_start), so the outer
    query's join topology and filters stay in the signature instead of
    silently vanishing (which made structurally different CTE queries
    collapse to the same impoverished core_id)."""

    def test_full_signature_survives_reserved_cte_names(self):
        facts = _facts(CTE_BASE)
        self.assertIn("JOINTYPE|LEFT=1", facts)
        self.assertIn("REL|=|AGG.ID|BASE.ID", facts)
        self.assertIn("PRED|BASE.AMT|>", facts)
        self.assertIn("PRED|TBORD.ST|=", facts)
        self.assertIn("GROUPBY|TBITEM.ID", facts)

    def test_alias_and_literal_variant_collapses(self):
        variant = (CTE_BASE.replace("tbord a", "tbord ord_row").replace("a.", "ord_row.")
                   .replace("'A'", "'ZZZ'").replace("base x", "base outer_b")
                   .replace("x.", "outer_b."))
        self.assertEqual(_core_id(CTE_BASE), _core_id(variant))

    def test_join_type_flip_does_not_collapse(self):
        flipped = CTE_BASE.replace("LEFT JOIN", "INNER JOIN")
        self.assertNotEqual(_core_id(CTE_BASE), _core_id(flipped))

    def test_cte_body_predicate_change_does_not_collapse(self):
        changed = CTE_BASE.replace("b.id, SUM(b.qty) qty FROM tbitem b GROUP BY b.id",
                                   "b.id, SUM(b.qty) qty FROM tbitem b "
                                   "WHERE b.del_yn = 'N' GROUP BY b.id")
        self.assertNotEqual(_core_id(CTE_BASE), _core_id(changed))


class TestAggregateStatementsParseWhole(unittest.TestCase):
    """COUNT/MAX in the SELECT list must not shred the statement into
    resync fragments -- the join REL fact (only reachable through the
    statement's own tree before the WHERE resync anchor) proves the
    statement parsed as one tree."""

    def test_count_statement_keeps_join_relationship_fact(self):
        self.assertIn("REL|=|TBDEPT.DEPT_CD|TBEMP.DEPT_CD", _facts(AGG_BASE))


class TestDeliberateExclusions(unittest.TestCase):
    """HAVING is parsed (the statement must not shred) but, like the
    SELECT list and ORDER BY, deliberately excluded from the signature."""

    def test_having_never_discriminates(self):
        having = AGG_BASE.replace(";", " HAVING COUNT(a.emp_id) > 5;")
        self.assertEqual(_core_id(AGG_BASE), _core_id(having))

    def test_having_statement_keeps_its_group_by_fact(self):
        having = AGG_BASE.replace(";", " HAVING COUNT(a.emp_id) > 5;")
        self.assertIn("GROUPBY|TBEMP.DEPT_CD", _facts(having))


class TestFunctionWrappedPredicates(unittest.TestCase):
    """A function-wrapped predicate operand contributes a
    FN(table.col,...) fingerprint -- the function name and its column
    inputs discriminate, literal arguments never do."""

    def test_different_functions_do_not_collapse(self):
        upper = "SELECT a.c1 FROM t1 a WHERE UPPER(a.nm) = 'X';"
        coalesce = "SELECT a.c1 FROM t1 a WHERE COALESCE(a.nm, '') = 'X';"
        self.assertNotEqual(_core_id(upper), _core_id(coalesce))

    def test_literal_argument_change_collapses(self):
        one = "SELECT a.c1 FROM t1 a WHERE COALESCE(a.nm, 'x') = 'X';"
        two = "SELECT a.c1 FROM t1 a WHERE COALESCE(a.nm, 'y') = 'ZZ';"
        self.assertEqual(_core_id(one), _core_id(two))

    def test_function_fingerprint_resolves_aliases(self):
        sql = "SELECT a.c1 FROM t1 a WHERE UPPER(a.nm) = 'X';"
        self.assertIn("PRED|UPPER(T1.NM)|=", _facts(sql))


class TestSupplementaryColumns(unittest.TestCase):
    """The identity row's `columns` field lists every referenced column,
    alias-resolved -- supplementary reporting only, never in the
    core_id."""

    def test_columns_lists_resolved_references(self):
        rows = _identity_rows(AGG_BASE)
        cols = rows[0].columns
        self.assertIn("TBEMP.DEPT_CD", cols)
        self.assertIn("TBEMP.EMP_ID", cols)
        self.assertIn("TBEMP.SAL", cols)
        self.assertIn("TBEMP.STAT", cols)
        self.assertIn("TBDEPT.DEPT_CD", cols)

    def test_columns_do_not_affect_core_id(self):
        wider = AGG_BASE.replace("SELECT a.dept_cd,", "SELECT a.dept_cd, a.hire_dt,")
        self.assertEqual(_core_id(AGG_BASE), _core_id(wider))
        self.assertNotEqual(_identity_rows(AGG_BASE)[0].columns,
                            _identity_rows(wider)[0].columns)


class TestMultiStatementFiles(unittest.TestCase):
    def test_each_statement_gets_its_own_identity_row(self):
        two = AGG_BASE + "\n" + CTE_BASE
        rows = _identity_rows(two)
        self.assertEqual(len(rows), 2)
        self.assertEqual({r.core_id for r in rows},
                         {_core_id(AGG_BASE), _core_id(CTE_BASE)})


if __name__ == "__main__":
    unittest.main()
