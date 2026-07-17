# -*- coding: utf-8 -*-
"""SQL query identification (--extract-metadata): assigns each statement
a `core_id`, a hash of its structural signature, so a corpus of thousands
of files canonicalizes down to its distinct core queries.

Signature contents (canonical fact strings, one set per statement):

* ``TBL|schema|table``       -- every real table referenced, alias-free
* ``JOINTYPE|type=n``        -- join-type multiset (JOIN/INNER/COMMA
  collapse to INNER; LEFT/RIGHT/FULL/CROSS stay distinct)
* ``REL|op|t1.c1|t2.c2``     -- a comparison joining two distinct tables
  (pair-sorted), from ON clauses and comma-join WHERE equalities alike
* ``PRED|operand|op``        -- a WHERE filter predicate's operand
  signature and operator (comparison/BETWEEN/LIKE/IS [NOT] NULL/IN); the
  operand is ``table.col`` or ``FN(table.col,...)`` (function name plus
  resolvable column arguments -- literal values are always excluded)
* ``GROUPBY|operand``        -- each GROUP BY item, same operand
  signature (a bare unqualified column keeps its own name)

Statements that differ only in SELECT-list projection, column aliasing,
derived-column arithmetic, table aliases, formatting, comments, literal
values, ORDER BY, or HAVING share a core_id; statements that differ in
tables, join topology, join types, WHERE filters, or grouping do not.
All facts come from the parse tree and the token-scan (table_scan.py)
with aliases resolved to real table names -- never from normalizing SQL
text.

Each identity row also carries a supplementary ``columns`` field -- every
column the statement references, alias-resolved where possible. It is
reporting-only and never enters the core_id: without table layout
information a ``SELECT *`` cannot be resolved to columns, so column sets
are not reliable identity evidence.

Known limitations, each pinned by tests/test_query_identity_complex.py:

* Function fingerprints are name + column inputs only -- two calls
  differing solely in literal arguments or argument order collapse.
* A correlated subquery's reference to an outer alias doesn't resolve
  (scoping is per query block), so a JOIN and its correlated-EXISTS
  rewrite deliberately get different signatures.

Statements that don't share a core_id get a corpus-wide Jaccard
similarity score over each distinct core_id's representative fact set
(compute_similarity, O(unique-core-ids^2), stdlib-only).
"""

from __future__ import annotations

import hashlib
from typing import Any

from Db2Parser import Db2Parser
from Db2ParserVisitor import Db2ParserVisitor

from src.models.identity import IdentityRow, SimilarityPair
from src.models.tables import QueryBlock
from src.parsing.predicates import COMPARISON_OPS, classify_predicate, subject_expression
from src.references import table_scan
from src.report import write_refs_tsv

_JOIN_TYPE_CANON = {
    "JOIN": "INNER", "INNER": "INNER", "COMMA": "INNER",
    "LEFT": "LEFT", "RIGHT": "RIGHT", "FULL": "FULL", "CROSS": "CROSS",
}

CORE_ID_LENGTH = 16


def _resolve_field_reference(expr_ctx: Any,
                             query_blocks: list[QueryBlock]) -> tuple[str, str] | None:
    """expr_ctx: an ExpressionContext. Returns (table, col) using the real,
    resolved table name (never an alias) if expr_ctx is a table/alias-
    qualified field_reference resolving to a real (non-placeholder) table,
    else None -- same resolvability convention relations.py's
    _JoinPredicateVisitor uses."""
    fref = expr_ctx.field_reference()
    if fref is None:
        return None
    qualifier = fref.row_variable_name().getText().upper()
    _schema, table = table_scan.resolve_qualifier(
        query_blocks, expr_ctx.start.start, qualifier, include_cte=True)
    if table == table_scan.PLACEHOLDER_TABLE:
        return None
    col = fref.field_name().getText().upper()
    return (table, col)


def _operand_signature(expr_ctx: Any, query_blocks: list[QueryBlock]) -> str | None:
    """Canonical, alias- and literal-independent signature of a predicate
    operand or GROUP BY item: ``TABLE.COL`` for a resolvable qualified
    column, ``FN(TABLE.COL,...)`` for a function call over its resolvable
    column arguments (literals and unresolvable arguments are dropped, so
    ``COUNT(*)`` becomes ``COUNT()`` and only the function name and its
    column inputs discriminate), else None."""
    resolved = _resolve_field_reference(expr_ctx, query_blocks)
    if resolved is not None:
        return "{}.{}".format(*resolved)
    fn = expr_ctx.function_invocation()
    if fn is None:
        return None
    name = fn.function_name().getText().upper()
    cols = []
    if fn.arg_list() is not None:
        for arg in fn.arg_list().argument():
            arg_expr = arg.expression()
            if arg_expr is None:
                continue
            r = _resolve_field_reference(arg_expr, query_blocks)
            if r is not None:
                cols.append("{}.{}".format(*r))
    return "{}({})".format(name, ",".join(cols))


class _PredicateFactVisitor(Db2ParserVisitor):
    """Accumulates canonical REL/PRED/GROUPBY fact strings, plus the
    supplementary `columns` set, across however many times
    statement_driver.py's tiered driver calls .visit() on this chunk's
    committed fragments (once per Tier-1/Tier-2 fragment) -- state just
    grows across calls, a chunk's own instance is only read back after
    the whole file's parse_file() call returns (see scan.py)."""

    def __init__(self, query_blocks: list[QueryBlock]) -> None:
        self.query_blocks = query_blocks
        self.facts: set[str] = set()
        # Every column the statement references, alias-resolved to
        # TABLE.COL where possible (bare columns keep their own name).
        # Reported as a supplementary TSV column only -- never part of
        # the signature, since SELECT * is unresolvable without table
        # layout information.
        self.columns: set[str] = set()

    def visitPredicate(self, ctx: Db2Parser.PredicateContext) -> Any:
        op = classify_predicate(ctx)
        if op is not None:
            self._handle_predicate(ctx, op)
        return self.visitChildren(ctx)

    def visitHaving_clause(self, ctx: Db2Parser.Having_clauseContext) -> Any:
        # HAVING is parsed (so the statement doesn't shred) but excluded
        # from the signature: like the SELECT list and ORDER BY, it
        # doesn't change which tables/joins/filters define the core
        # query. Column references inside it still count as used columns.
        self._collect_columns(ctx)
        return None

    def visitField_reference(self, ctx: Db2Parser.Field_referenceContext) -> Any:
        qualifier = ctx.row_variable_name().getText().upper()
        _schema, table = table_scan.resolve_qualifier(
            self.query_blocks, ctx.start.start, qualifier, include_cte=True)
        col = ctx.field_name().getText().upper()
        if table == table_scan.PLACEHOLDER_TABLE:
            self.columns.add(col)
        else:
            self.columns.add("{}.{}".format(table, col))
        return self.visitChildren(ctx)

    def visitColumn_name(self, ctx: Db2Parser.Column_nameContext) -> Any:
        self.columns.add(ctx.getText().upper())
        return self.visitChildren(ctx)

    def _collect_columns(self, ctx: Any) -> None:
        """Column-only walk of a subtree excluded from fact collection."""
        collector = _PredicateFactVisitor(self.query_blocks)
        collector.visitChildren(ctx)
        self.columns |= collector.columns

    def visitGrouping_expression(self, ctx: Db2Parser.Grouping_expressionContext) -> Any:
        # One GROUP BY item (`grouping_expression : expression`): a
        # qualified column or function call gets its canonical operand
        # signature; a bare column keeps its own name (it contains no
        # alias by construction). Anything else contributes nothing,
        # matching the predicate facts' silent-skip convention.
        expr = ctx.expression()
        sig = _operand_signature(expr, self.query_blocks)
        if sig is not None:
            self.facts.add("GROUPBY|{}".format(sig))
        else:
            col = expr.column_name()
            if col is not None:
                self.facts.add("GROUPBY|{}".format(col.getText().upper()))
        return self.visitChildren(ctx)

    def _handle_predicate(self, ctx: Db2Parser.PredicateContext, op: str) -> None:
        if op in COMPARISON_OPS:
            exprs = ctx.expression()
            self._handle_comparison(exprs[0], exprs[1], op)
            return
        subject = subject_expression(ctx, op)
        if subject is not None:
            self._handle_single(subject, op)

    def _handle_comparison(self, left_ctx: Any, right_ctx: Any, op: str) -> None:
        left = _resolve_field_reference(left_ctx, self.query_blocks)
        right = _resolve_field_reference(right_ctx, self.query_blocks)
        if left is not None and right is not None:
            if left[0] == right[0]:
                return  # same table both sides -- not a relationship
            a, b = sorted(("{}.{}".format(*left), "{}.{}".format(*right)))
            self.facts.add("REL|{}|{}|{}".format(op, a, b))
            return
        for sig in (_operand_signature(left_ctx, self.query_blocks),
                    _operand_signature(right_ctx, self.query_blocks)):
            if sig is not None:
                self.facts.add("PRED|{}|{}".format(sig, op))

    def _handle_single(self, expr_ctx: Any, op: str) -> None:
        sig = _operand_signature(expr_ctx, self.query_blocks)
        if sig is not None:
            self.facts.add("PRED|{}|{}".format(sig, op))


def new_predicate_visitor(query_blocks: list[QueryBlock]) -> _PredicateFactVisitor:
    return _PredicateFactVisitor(query_blocks)


def _join_type_facts(query_blocks: list[QueryBlock]) -> set[str]:
    counts = {}
    for edge in table_scan.scan_join_edges(query_blocks):
        canon = _JOIN_TYPE_CANON.get(edge.join_type, edge.join_type)
        counts[canon] = counts.get(canon, 0) + 1
    return {"JOINTYPE|{}={}".format(t, n) for t, n in counts.items()}


def build_fact_set(query_blocks: list[QueryBlock],
                   predicate_facts: set[str]) -> frozenset[str]:
    """query_blocks: table_scan.scan_query_blocks' output for one chunk.
    predicate_facts: the .facts set of a _PredicateFactVisitor that has
    already visited every committed fragment of that same chunk."""
    facts = set()
    for ref in table_scan.iter_table_refs(query_blocks):
        facts.add("TBL|{}|{}".format(ref.schema, ref.table))
    facts |= _join_type_facts(query_blocks)
    facts |= predicate_facts
    return frozenset(facts)


def core_id_for(fact_set: frozenset[str]) -> str:
    """Deterministic short hex id -- order-independent (fact_set is
    hashed via a sorted, joined repr, not Python's own unstable hash())."""
    canonical = "\n".join(sorted(fact_set))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:CORE_ID_LENGTH]


def build_identity_row(query_blocks: list[QueryBlock], predicate_visitor: _PredicateFactVisitor,
                       path: str, line: int | None) -> IdentityRow:
    """predicate_visitor: a _PredicateFactVisitor that has already visited
    every committed fragment of this chunk. Its `columns` set rides along
    as supplementary information only -- it never enters the fact set or
    the core_id."""
    fact_set = build_fact_set(query_blocks, predicate_visitor.facts)
    return IdentityRow(
        core_id=core_id_for(fact_set), file=path, line=line,
        table_count=sum(1 for f in fact_set if f.startswith("TBL|")),
        join_count=sum(1 for f in fact_set if f.startswith("REL|")),
        predicate_count=sum(1 for f in fact_set if f.startswith("PRED|")),
        fact_set=fact_set,
        columns=tuple(sorted(predicate_visitor.columns)),
    )


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def compute_similarity(identity_rows: list[IdentityRow],
                       threshold: float = 0.5) -> list[SimilarityPair]:
    """Groups rows by core_id, takes one representative fact_set per
    distinct core_id, and scores every pair of distinct core_ids against
    each other -- corpus-wide, called once after a full scan_tree()
    completes (not per-file: needs every core_id discovered across the
    whole scan to be meaningful). Returns one SimilarityPair per pair scoring at
    or above `threshold`, sorted by similarity desc."""
    representatives: dict[str, frozenset[str]] = {}
    for row in identity_rows:
        representatives.setdefault(row.core_id, row.fact_set)

    ids = sorted(representatives)
    pairs = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            score = _jaccard(representatives[a], representatives[b])
            if score >= threshold:
                pairs.append(SimilarityPair(
                    core_id_a=a, core_id_b=b,
                    similarity=round(score, 3),
                    shared_facts=len(representatives[a] & representatives[b]),
                ))
    pairs.sort(key=lambda p: -p.similarity)
    return pairs


def write_similarity_tsv(path: str, similarity_rows: list[SimilarityPair]) -> None:
    """Same TSV conventions as report.write_refs_tsv (utf-8-sig,
    tab-separated, header row always written even for an empty list)."""
    write_refs_tsv(path, ["core_id_a", "core_id_b", "similarity", "shared_facts"],
                   similarity_rows)
