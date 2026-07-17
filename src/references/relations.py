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
   ON-clause. Before issue #4 / commit 7fea4c8 fixed the grammar's JOIN
   parse path, an ON-clause's search_condition was unreachable from
   Tier 1's tree at all and only ever surfaced as an orphaned fragment via
   statement_driver's Tier 2 resync; now that ANSI JOINs parse as one
   clean Tier-1 tree, the same visitor finds the ON-clause's comparison as
   an ordinary descendant of that tree instead. Either way, scan.py's
   pre_chunk_hook dedupes that case against source 1's non-comma edges for
   the same table pair in the same chunk, a coarser chunk-level dedup (not
   exact-predicate matching) that trades undercounting a rare, genuinely
   separate redundant WHERE-equality for the same pair against
   overcounting every ordinary JOIN.

A comma-joined pair with no WHERE condition linking it at all (a rare,
degenerate cross-join) goes unrecorded entirely -- a documented
limitation, not a silent wrong answer.
"""

from Db2Parser import Db2Parser
from Db2ParserVisitor import Db2ParserVisitor

from src.references import table_scan


class _JoinPredicateVisitor(Db2ParserVisitor):
    """Walks a chunk's committed trees looking for an ordinary binary
    comparison (=, <, >, <=, >=, <>) between two table/alias-qualified
    column references (field_reference -- a bare, unqualified column_name
    can never be told apart from two different tables) that resolve to
    two distinct real (non-placeholder) tables in the same query block."""

    def __init__(self, query_blocks, sink):
        self.query_blocks = query_blocks
        self.sink = sink

    def visitPredicate(self, ctx: Db2Parser.PredicateContext):
        exprs = ctx.expression()
        op_ctx = ctx.comparison_operator()
        if op_ctx is not None and len(exprs) == 2 and ctx.some_any_all() is None:
            self._handle_comparison(exprs[0], exprs[1], op_ctx.getText(), ctx.start.line)
        return self.visitChildren(ctx)

    def _handle_comparison(self, left, right, operator, line):
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


def make_join_predicate_visitor(query_blocks, sink):
    """sink: callable(left_schema, left_table, right_schema, right_table,
    join_type, predicate, line) -- same shape edges are normalized to
    regardless of which of the two sources above produced them."""
    return _JoinPredicateVisitor(query_blocks, sink)


def structural_edges_to_dicts(path, edges):
    """edges: list[table_scan.JoinEdge] (table_scan.scan_join_edges'
    output). Normalizes to the same flat edge-dict shape WHERE-IMPLICIT
    edges use, so both sources merge into one list downstream."""
    return [{
        "file": path, "line": e.line,
        "table_a_schema": e.left.schema, "table_a": e.left.table,
        "table_b_schema": e.right.schema, "table_b": e.right.table,
        "join_type": e.join_type, "predicate": e.predicate_text,
    } for e in edges]


def aggregate_edges(edges):
    """Groups by an unordered table-pair key (so A-B and B-A collapse
    together) -- (schema, table) 2-tuples sorted so grouping is
    deterministic regardless of which side happened to be "left"/"right"
    in the source SQL. Returns a list of dicts: table_a_schema, table_a,
    table_b_schema, table_b, join_count, predicates (sorted distinct
    predicate strings seen for this pair), sorted by join_count desc then
    table names."""
    groups = {}
    for e in edges:
        a = (e["table_a_schema"], e["table_a"])
        b = (e["table_b_schema"], e["table_b"])
        key = tuple(sorted((a, b)))
        g = groups.setdefault(key, {"count": 0, "predicates": set()})
        g["count"] += 1
        if e["predicate"]:
            g["predicates"].add(e["predicate"])

    rows = []
    for (a, b), g in groups.items():
        rows.append({
            "table_a_schema": a[0], "table_a": a[1],
            "table_b_schema": b[0], "table_b": b[1],
            "join_count": g["count"],
            "predicates": sorted(g["predicates"]),
        })
    rows.sort(key=lambda r: (-r["join_count"], r["table_a"], r["table_b"]))
    return rows


def write_relations_tsv(path, aggregated):
    """Same TSV conventions as report.py (utf-8-sig, tab-separated, header
    row always written even for an empty `aggregated` list)."""
    headers = ["table_a_schema", "table_a", "table_b_schema", "table_b",
              "join_count", "predicates"]

    def clean(v):
        return str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")

    with open(path, "w", encoding="utf-8-sig", newline="") as out:
        out.write("\t".join(headers) + "\n")
        for row in aggregated:
            values = [row["table_a_schema"], row["table_a"], row["table_b_schema"],
                     row["table_b"], row["join_count"], "; ".join(row["predicates"])]
            out.write("\t".join(clean(v) for v in values) + "\n")
