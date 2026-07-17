# -*- coding: utf-8 -*-
"""JOIN relationship extraction (--extract-metadata), aggregated once for
the whole scanned tree (a single global refs_relations.tsv, not one per
directory).

Two sources of join edges feed into this:

1. Structural edges from table_scan.scan_join_edges, restricted to
   *non*-comma join types (explicit JOIN...ON/USING -- table_scan.py's own
   token-scan discovery, independent of whether the parser can build a
   tree for the JOIN). scan.py's pre_chunk_hook filters out the COMMA join
   type here on purpose: table_scan's own comma-join edge carries no
   predicate at all, and source 2 below is exactly what recovers one for
   it -- so a comma-join is deliberately sourced *only* from source 2,
   never both, or every comma-join would be double-counted.
2. "WHERE-IMPLICIT" edges (_JoinPredicateVisitor below): an ordinary
   binary comparison between two table/alias-qualified columns that
   resolve, via table_scan.resolve_qualifier, to two distinct real tables
   in the same query block. This is the sole source for comma-joins (see
   above), and also independently catches an explicit JOIN's own
   ON-clause comparison as an ordinary descendant of the committed tree.
   scan.py's pre_chunk_hook dedupes that case against source 1's
   non-comma edges for the same table pair in the same chunk -- a coarser
   chunk-level dedup (not exact-predicate matching) that trades
   undercounting a rare, genuinely separate redundant WHERE-equality for
   the same pair against overcounting every ordinary JOIN.

A comma-joined pair with no WHERE condition linking it at all (a rare,
degenerate cross-join) goes unrecorded entirely -- a documented
limitation, not a silent wrong answer.
"""

from __future__ import annotations

from typing import Any, Callable

from Db2Parser import Db2Parser
from Db2ParserVisitor import Db2ParserVisitor

from src.models.relations import RelationEdge, RelationRollup
from src.models.tables import JoinEdge, QueryBlock
from src.parsing.predicates import COMPARISON_OPS, classify_predicate
from src.references import table_scan
from src.report import write_refs_tsv


class _JoinPredicateVisitor(Db2ParserVisitor):
    """Walks a chunk's committed trees looking for an ordinary binary
    comparison (=, <, >, <=, >=, <>) between two table/alias-qualified
    column references (field_reference -- a bare, unqualified column_name
    can never be told apart from two different tables) that resolve to
    two distinct real (non-placeholder) tables in the same query block."""

    def __init__(self, query_blocks: list[QueryBlock],
                 sink: Callable[[str, str, str, str, str, str, int], None]) -> None:
        self.query_blocks = query_blocks
        self.sink = sink

    def visitPredicate(self, ctx: Db2Parser.PredicateContext) -> Any:
        op = classify_predicate(ctx)
        if op in COMPARISON_OPS:
            exprs = ctx.expression()
            self._handle_comparison(exprs[0], exprs[1], op, ctx.start.line)
        return self.visitChildren(ctx)

    def _handle_comparison(self, left: Any, right: Any, operator: str, line: int) -> None:
        lfref = left.field_reference()
        rfref = right.field_reference()
        if lfref is None or rfref is None:
            return
        lq = lfref.row_variable_name().getText().upper()
        rq = rfref.row_variable_name().getText().upper()
        lschema, ltable = table_scan.resolve_qualifier(self.query_blocks, left.start.start, lq)
        rschema, rtable = table_scan.resolve_qualifier(self.query_blocks, right.start.start, rq)
        if ltable == table_scan.PLACEHOLDER_TABLE or rtable == table_scan.PLACEHOLDER_TABLE:
            return
        if (lschema, ltable) == (rschema, rtable):
            return  # same table on both sides -- not a join
        lcol = lfref.field_name().getText().upper()
        rcol = rfref.field_name().getText().upper()
        predicate = "{}.{} {} {}.{}".format(ltable, lcol, operator, rtable, rcol)
        self.sink(lschema, ltable, rschema, rtable, "WHERE-IMPLICIT", predicate, line)


def make_join_predicate_visitor(
        query_blocks: list[QueryBlock],
        sink: Callable[[str, str, str, str, str, str, int], None]) -> Db2ParserVisitor:
    """sink: callable(left_schema, left_table, right_schema, right_table,
    join_type, predicate, line) -- same shape edges are normalized to
    regardless of which of the two sources above produced them."""
    return _JoinPredicateVisitor(query_blocks, sink)


def structural_edges_to_models(path: str, edges: list[JoinEdge]) -> list[RelationEdge]:
    """edges: table_scan.scan_join_edges' output. Normalizes to the same
    RelationEdge shape WHERE-IMPLICIT edges use, so both sources merge
    into one list downstream."""
    return [RelationEdge(
        file=path, line=e.line,
        table_a_schema=e.left.schema, table_a=e.left.table,
        table_b_schema=e.right.schema, table_b=e.right.table,
        join_type=e.join_type, predicate=e.predicate_text,
    ) for e in edges]


def aggregate_edges(edges: list[RelationEdge]) -> list[RelationRollup]:
    """Groups by RelationEdge.pair_key() (unordered, so A-B and B-A
    collapse together). Returns one RelationRollup per table pair with
    its sorted distinct predicate strings, sorted by join_count desc then
    table names."""
    groups: dict[tuple[tuple[str, str], tuple[str, str]], dict[str, Any]] = {}
    for e in edges:
        g = groups.setdefault(e.pair_key(), {"count": 0, "predicates": set()})
        g["count"] += 1
        if e.predicate:
            g["predicates"].add(e.predicate)

    rows = [RelationRollup(
        table_a_schema=a[0], table_a=a[1],
        table_b_schema=b[0], table_b=b[1],
        join_count=g["count"],
        predicates=tuple(sorted(g["predicates"])),
    ) for (a, b), g in groups.items()]
    rows.sort(key=lambda r: (-r.join_count, r.table_a, r.table_b))
    return rows


def write_relations_tsv(path: str, aggregated: list[RelationRollup]) -> None:
    """Same TSV conventions as report.write_refs_tsv (utf-8-sig,
    tab-separated, header row always written even for an empty
    `aggregated` list); each row's distinct predicates are joined with
    '; ' into one column by the writer's sequence-cell convention."""
    write_refs_tsv(path, ["table_a_schema", "table_a", "table_b_schema", "table_b",
                          "join_count", "predicates"], aggregated)
