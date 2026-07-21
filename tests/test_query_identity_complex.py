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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import engine as scanner  # noqa: E402
from metchurial.models.options import ScanOptions  # noqa: E402


def _identity_rows(sql):
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as f:
        f.write(sql)
        path = f.name
    try:
        result = scanner.scan_file(path, ScanOptions(extract_query_identity=True))
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


class TestWrapperDoesNotCollapseOntoBareQuery(unittest.TestCase):
    """A statement that only wraps another query in a CTE or a derived-
    table subquery -- `WITH cte AS (<q>) SELECT * FROM cte` or
    `SELECT * FROM (<q>) x` -- adds no join/predicate/grouping fact of its
    own, so its fact_set used to be exactly `<q>`'s own fact_set. That
    silently merged two structurally different statements (living in two
    different .sql files, e.g. one file holding the whole CTE query and
    another holding just the shared SELECT it wraps) onto one core_id.
    SHAPE|BLOCKS=n (the query-block count) now discriminates a wrapper
    from the bare query it wraps, while still collapsing cosmetic-only
    differences between two wrappers of the same shape."""

    BARE = "SELECT a.id, a.amt FROM tbord a WHERE a.st = 'A';"
    CTE_WRAPPED = ("WITH base AS (SELECT a.id, a.amt FROM tbord a WHERE a.st = 'A') "
                  "SELECT * FROM base;")
    SUBQUERY_WRAPPED = ("SELECT s.id, s.amt FROM "
                       "(SELECT a.id, a.amt FROM tbord a WHERE a.st = 'A') s;")
    # UNION'd with itself -- same tables/predicate as BARE on both
    # branches, so TBL/PRED alone don't discriminate it from BARE either;
    # only SHAPE|BLOCKS (2 query blocks, one per branch, vs BARE's 1) does.
    UNION_WRAPPED = ("SELECT a.id, a.amt FROM tbord a WHERE a.st = 'A' "
                    "UNION "
                    "SELECT a.id, a.amt FROM tbord a WHERE a.st = 'A';")

    def test_cte_wrapper_does_not_match_the_bare_query_it_wraps(self):
        # Two separate .sql files: one holding the whole `WITH ... SELECT
        # * FROM base` statement, the other holding just the SELECT its
        # CTE body wraps -- these must not canonicalize to the same
        # core_id, even though the CTE body's own facts are identical.
        self.assertNotEqual(_core_id(self.CTE_WRAPPED), _core_id(self.BARE))

    def test_subquery_wrapper_does_not_match_the_bare_query_it_wraps(self):
        self.assertNotEqual(_core_id(self.SUBQUERY_WRAPPED), _core_id(self.BARE))

    def test_union_wrapper_does_not_match_the_bare_query_it_wraps(self):
        # A UNION of two branches (even two copies of the same branch) is
        # a genuinely different query from either branch alone -- UNION
        # dedups rows, UNION ALL doubles them; neither is equivalent to
        # running just one branch. Must not canonicalize onto BARE.
        self.assertNotEqual(_core_id(self.UNION_WRAPPED), _core_id(self.BARE))

    def test_cte_wrapper_alias_rename_still_collapses(self):
        renamed = (self.CTE_WRAPPED.replace("base", "cte2").replace("tbord a", "tbord x")
                  .replace("a.", "x."))
        self.assertEqual(_core_id(self.CTE_WRAPPED), _core_id(renamed))


class TestStatementShapeFlags(unittest.TestCase):
    """has_cte/has_subquery/has_union: supplementary refs_query_identity.tsv
    columns surfacing whether a statement wraps a CTE, a derived-table/
    scalar/IN/EXISTS subquery, or a UNION/INTERSECT/EXCEPT -- reporting
    only, never part of the core_id (SHAPE|BLOCKS already handles that,
    see TestWrapperDoesNotCollapseOntoBareQuery)."""

    def _flags(self, sql):
        row = _identity_rows(sql)[0]
        return row.has_cte, row.has_subquery, row.has_union

    def test_bare_query_has_no_shape_flags_set(self):
        sql = "SELECT a.id, a.amt FROM tbord a WHERE a.st = 'A';"
        self.assertEqual(self._flags(sql), (False, False, False))

    def test_cte_wrapper_sets_has_cte_only(self):
        sql = "WITH mycte AS (SELECT a.id FROM tbord a) SELECT * FROM mycte;"
        self.assertEqual(self._flags(sql), (True, False, False))

    def test_derived_table_sets_has_subquery_only(self):
        sql = "SELECT dv.id FROM (SELECT a.id FROM tbord a) dv;"
        self.assertEqual(self._flags(sql), (False, True, False))

    def test_exists_subquery_sets_has_subquery_only(self):
        sql = ("SELECT a.id FROM tbord a "
              "WHERE EXISTS (SELECT 1 FROM tbitem b WHERE b.ord_id = a.id);")
        self.assertEqual(self._flags(sql), (False, True, False))

    def test_union_sets_has_union_only(self):
        sql = ("SELECT a.id FROM tbord a WHERE a.st = 'A' "
              "UNION SELECT a.id FROM tbord a WHERE a.st = 'B';")
        self.assertEqual(self._flags(sql), (False, False, True))

    def test_union_inside_a_cte_body_sets_both_flags(self):
        sql = ("WITH mycte AS (SELECT a.id FROM tbord a UNION SELECT a.id FROM tbord a) "
              "SELECT * FROM mycte;")
        self.assertEqual(self._flags(sql), (True, False, True))

    def test_has_cte_is_robust_to_a_reserved_keyword_cte_name(self):
        # has_cte/has_union are read off the token stream, not the parse
        # tree, so a CTE named "base" (a reserved keyword that keeps this
        # statement from parsing as one clean tree, per
        # TestReservedKeywordCteNames) still sets has_cte correctly.
        sql = "WITH base AS (SELECT a.id FROM tbord a) SELECT * FROM base;"
        self.assertTrue(_identity_rows(sql)[0].has_cte)

    def test_has_subquery_can_under_report_on_a_reserved_keyword_alias(self):
        # Documented limitation (see query_identity.py's module docstring
        # and _PredicateFactVisitor.has_subquery): unlike has_cte/
        # has_union, has_subquery is read off the parse tree, so a derived
        # table aliased "s" (single-letter reserved token, see
        # table_scan.py's _ALIAS_TOKEN_TYPES comment) keeps this statement
        # from parsing as one clean tree and has_subquery goes unset, even
        # though the query genuinely has a subquery -- pinned here so a
        # future grammar/driver fix that closes this gap is a conscious,
        # visible change, not a silent one.
        sql = "SELECT s.id FROM (SELECT a.id FROM tbord a) s;"
        self.assertFalse(_identity_rows(sql)[0].has_subquery)


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

    def test_bare_column_function_argument_keeps_its_own_name(self):
        # SUBSTR(mydatecolumn, 1, 6) used to resolve to no column at all
        # (_resolve_field_reference requires a table/alias qualifier,
        # which a bare argument doesn't have) -- the operand silently
        # became "SUBSTR()", indistinguishable from SUBSTR(*any* other
        # unqualified column, ...). It now falls back to the bare name,
        # the same convention GROUP BY already applies to an unqualified
        # item.
        sql = "SELECT a.id FROM tbord a WHERE SUBSTR(mydatecolumn, 1, 6) <= '202512';"
        self.assertIn("PRED|SUBSTR(MYDATECOLUMN)|<=", _facts(sql))

    def test_qualified_and_bare_function_argument_do_not_collapse(self):
        # A qualified argument still resolves to the more precise
        # TABLE.COL signature -- distinct from, not merged with, the bare-
        # name fallback for the same column left unqualified.
        bare = "SELECT a.id FROM tbord a WHERE SUBSTR(mydatecolumn, 1, 6) <= '202512';"
        qualified = "SELECT a.id FROM tbord a WHERE SUBSTR(a.mydatecolumn, 1, 6) <= '202512';"
        self.assertNotEqual(_core_id(bare), _core_id(qualified))
        self.assertIn("PRED|SUBSTR(TBORD.MYDATECOLUMN)|<=", _facts(qualified))

    def test_bare_column_top_level_predicate_keeps_its_own_name(self):
        # Same root cause, one level up: `WHERE mydatecolumn <= 'x'` with
        # no function call used to contribute no PRED fact at all --
        # completely invisible to the signature, not just imprecise.
        sql = "SELECT a.id FROM tbord a WHERE mydatecolumn <= '202512';"
        self.assertIn("PRED|MYDATECOLUMN|<=", _facts(sql))


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
