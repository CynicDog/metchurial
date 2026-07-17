# -*- coding: utf-8 -*-
"""SQL query identification (--extract-metadata, issue #8): assigns each
SQL statement a `core_id` -- a hash of its structural signature -- so
statements that differ only in column aliasing, SELECT-list projection,
or how a derived column is calculated collapse to the same id, while
statements that differ in which tables they touch, how those tables join,
or what they filter on do not. Statements that don't share a `core_id`
get a similarity score against the nearest existing cluster instead of
being left as disconnected rows (see compute_similarity below).

This is built entirely from facts table_scan.py/the parse tree already
give access to -- never from the SQL text itself. There's no "strip
comments/normalize whitespace/replace literals in the string" step the
way pt-fingerprint/pg_stat_statements' text-based query digests work:
the signature is assembled from structural facts already resolved to
real table/column names (table_scan.resolve_qualifier), so aliasing,
formatting, and comments were never part of the fact set to begin with,
rather than being stripped out by a rule that has to anticipate every
formatting variation.

Deliberately excluded from the signature: the SELECT list (aliasing,
column count, and derived-column calculation all live there -- excluding
it is what makes those three differences collapse to the same id, by
construction, per the issue's own definition) and every literal value
(two statements filtering the same column with the same operator but
different literal values are still the same core query, the same
normalize-the-literal-away principle pt-fingerprint/pg_stat_statements
use, just applied to structured facts instead of text).

Three components feed the signature, one set of canonical fact strings
per statement (chunk):

1. Table set -- from table_scan.iter_table_refs, already real-name and
   alias-independent, already flattens CTE-body/subquery tables (CTE
   names themselves already excluded, see table_scan.py).
2. Join-type multiset -- from table_scan.scan_join_edges, canonicalized
   (JOIN/INNER/COMMA all collapse to one "INNER" bucket; LEFT/RIGHT/FULL/
   CROSS kept distinct) and counted, e.g. "JOINTYPE|INNER=2". This module
   never trusts scan_join_edges for *pairing* -- only for this coarse
   join-type count -- which turned out to matter for a real, separate
   reason found while building this: `_apply_table_list` used to assign a
   connector's table pair *positionally* (entries[k]/entries[k+1] in
   FROM-clause order) rather than from what its own ON-clause predicate
   actually says, mislabeling a "hub table" pattern (`FROM a JOIN b ON
   a.x=b.x JOIN c ON a.y=c.y`, where `c` really joins to `a`, not `b`).
   That's now fixed directly in table_scan.py (`_resolve_pair_from_
   predicate` -- derives the real pair from the predicate's own
   qualifiers when resolvable, falling back to position only when it
   isn't, e.g. a USING clause's bare column list) -- a real correctness
   fix for relations.py's already-shipped refs_relations.tsv output too,
   not just this module. This module's own relationship pairing (3 below)
   was always independently correct regardless, since it was never built
   on scan_join_edges' pairing in the first place -- so nothing here
   needed to change once table_scan.py was fixed, but the join-type
   count and the relationship facts are now consistent with each other
   for the same reason, not just individually correct.
3. Relationship/predicate facts -- a new _PredicateFactVisitor (tree-
   walking, modeled on relations.py's _JoinPredicateVisitor: same
   resolve_qualifier-based alias resolution, so table-pair identity here
   is correct regardless of FROM-clause position, unlike (2)):
   - A two-operand comparison (=,<>,<,>,<=,>=) where both sides resolve
     to two *distinct* real tables is a relationship fact:
     "REL|op|table_a.col_a|table_b.col_b" (pair-sorted, order-
     independent). This is what a JOIN's ON-clause ordinarily is, and
     it's also how a comma-join's WHERE-clause equality is recovered --
     no join_type is attached (this module doesn't need it; (2) already
     covers join-type identity as a separate, decoupled signal, so the
     two together still distinguish e.g. a LEFT-vs-INNER flip on
     otherwise-identical relationships without needing precise per-edge
     join_type-to-pair correlation -- confirmed sufficient against
     issue #8's fixture corpus, see tests/test_query_identity.py).
   - A single-operand filter predicate (comparison/BETWEEN/LIKE/IS NULL/
     IN, dispatched via function_visitor.classify_predicate's existing
     shape-classification logic) where the column-shaped operand resolves
     to a real table is a filter fact: "PRED|table.col|op" -- the literal/
     value side is never inspected.
   - Any operand that isn't a resolvable field_reference (bare unqualified
     column, function-call-wrapped expression) contributes nothing for
     that operand -- same silent-skip convention _JoinPredicateVisitor
     already uses. A predicate whose only column-shaped operand is inside
     a correlated subquery and refers to an *outer* query's alias also
     doesn't resolve (resolve_qualifier only checks the innermost
     enclosing block's own alias_map, not parent scopes) -- this is
     deliberate, not a bug: it's exactly what makes a JOIN-based filter
     and a semantically-similar correlated-EXISTS-subquery rewrite of the
     same filter produce different signatures (issue #8's documented
     non-goal -- proving semantic equivalence across those two forms is a
     fundamentally different, harder problem than structural comparison).
   - A JOIN's `USING (...)` column list produces no comparison predicate
     in the tree at all (it's a bare column list, not a search_condition)
     -- such a join contributes no relationship fact here, a known,
     documented gap shared with relations.py's WHERE-IMPLICIT sourcing.

Similarity for statements that don't share a core_id: Jaccard similarity
(stdlib set operations only -- this project's dist/metchurial.py bundle
is contractually zero-third-party, see tests/test_bundle.py, so no tree-
edit-distance library) over each distinct core_id's representative fact
set, computed once, corpus-wide, after a full scan_tree() completes (see
compute_similarity) -- not per-file, and not pairwise over every
individual statement: given the issue's own framing ("thousands of
files, a few dozen actual queries"), this is O(unique-core-ids^2), not
O(files^2).
"""

import hashlib

from Db2Parser import Db2Parser
from Db2ParserVisitor import Db2ParserVisitor

from src.references import table_scan
from src.references.function_visitor import classify_predicate

_JOIN_TYPE_CANON = {
    "JOIN": "INNER", "INNER": "INNER", "COMMA": "INNER",
    "LEFT": "LEFT", "RIGHT": "RIGHT", "FULL": "FULL", "CROSS": "CROSS",
}

CORE_ID_LENGTH = 16


def _resolve_field_reference(expr_ctx, query_blocks):
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


class _PredicateFactVisitor(Db2ParserVisitor):
    """Accumulates canonical REL/PRED fact strings across however many
    times statement_driver.py's tiered driver calls .visit() on this
    chunk's committed fragments (once per Tier-1/Tier-2 fragment) -- state
    just grows across calls, a chunk's own instance is only read back
    after the whole file's parse_file() call returns (see scan.py)."""

    def __init__(self, query_blocks):
        self.query_blocks = query_blocks
        self.facts = set()

    def visitPredicate(self, ctx: Db2Parser.PredicateContext):
        op = classify_predicate(ctx)
        if op is not None:
            self._handle_predicate(ctx, op)
        return self.visitChildren(ctx)

    def _handle_predicate(self, ctx, op):
        exprs = ctx.expression()
        if op in ("=", "<>", "<", ">", "<=", ">="):
            self._handle_comparison(exprs[0], exprs[1], op)
            return
        if op in ("BETWEEN", "NOT BETWEEN", "IS NULL", "IS NOT NULL"):
            self._handle_single(exprs[0], op)
            return
        if op in ("LIKE", "NOT LIKE"):
            self._handle_single(ctx.me, op)
            return
        if op in ("IN", "NOT IN"):
            self._handle_single(ctx.e, op)
            return

    def _handle_comparison(self, left_ctx, right_ctx, op):
        left = _resolve_field_reference(left_ctx, self.query_blocks)
        right = _resolve_field_reference(right_ctx, self.query_blocks)
        if left is not None and right is not None:
            if left[0] == right[0]:
                return  # same table both sides -- not a relationship
            a, b = sorted(("{}.{}".format(*left), "{}.{}".format(*right)))
            self.facts.add("REL|{}|{}|{}".format(op, a, b))
        elif left is not None:
            self.facts.add("PRED|{}.{}|{}".format(left[0], left[1], op))
        elif right is not None:
            self.facts.add("PRED|{}.{}|{}".format(right[0], right[1], op))

    def _handle_single(self, expr_ctx, op):
        resolved = _resolve_field_reference(expr_ctx, self.query_blocks)
        if resolved is not None:
            self.facts.add("PRED|{}.{}|{}".format(resolved[0], resolved[1], op))


def new_predicate_visitor(query_blocks):
    return _PredicateFactVisitor(query_blocks)


def _join_type_facts(query_blocks):
    counts = {}
    for edge in table_scan.scan_join_edges(query_blocks):
        canon = _JOIN_TYPE_CANON.get(edge.join_type, edge.join_type)
        counts[canon] = counts.get(canon, 0) + 1
    return {"JOINTYPE|{}={}".format(t, n) for t, n in counts.items()}


def build_fact_set(query_blocks, predicate_facts):
    """query_blocks: table_scan.scan_query_blocks' output for one chunk.
    predicate_facts: the .facts set of a _PredicateFactVisitor that has
    already visited every committed fragment of that same chunk."""
    facts = set()
    for ref in table_scan.iter_table_refs(query_blocks):
        facts.add("TBL|{}|{}".format(ref.schema, ref.table))
    facts |= _join_type_facts(query_blocks)
    facts |= predicate_facts
    return frozenset(facts)


def core_id_for(fact_set):
    """Deterministic short hex id -- order-independent (fact_set is
    hashed via a sorted, joined repr, not Python's own unstable hash())."""
    canonical = "\n".join(sorted(fact_set))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:CORE_ID_LENGTH]


def build_identity_row(query_blocks, predicate_facts, path, line):
    fact_set = build_fact_set(query_blocks, predicate_facts)
    table_count = sum(1 for f in fact_set if f.startswith("TBL|"))
    join_count = sum(1 for f in fact_set if f.startswith("REL|"))
    predicate_count = sum(1 for f in fact_set if f.startswith("PRED|"))
    return {
        "core_id": core_id_for(fact_set), "file": path, "line": line,
        "table_count": table_count, "join_count": join_count,
        "predicate_count": predicate_count, "fact_set": fact_set,
    }


def _jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def compute_similarity(identity_rows, threshold=0.5):
    """Groups rows by core_id, takes one representative fact_set per
    distinct core_id, and scores every pair of distinct core_ids against
    each other -- corpus-wide, called once after a full scan_tree()
    completes (not per-file: needs every core_id discovered across the
    whole scan to be meaningful). Returns a list of dicts (core_id_a,
    core_id_b, similarity, shared_facts), one per pair scoring at or
    above `threshold`, sorted by similarity desc."""
    representatives = {}
    for row in identity_rows:
        representatives.setdefault(row["core_id"], row["fact_set"])

    ids = sorted(representatives)
    pairs = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            score = _jaccard(representatives[a], representatives[b])
            if score >= threshold:
                pairs.append({
                    "core_id_a": a, "core_id_b": b,
                    "similarity": round(score, 3),
                    "shared_facts": len(representatives[a] & representatives[b]),
                })
    pairs.sort(key=lambda p: -p["similarity"])
    return pairs


def write_similarity_tsv(path, similarity_rows):
    """Same TSV conventions as relations.write_relations_tsv (utf-8-sig,
    tab-separated, header row always written even for an empty list)."""
    headers = ["core_id_a", "core_id_b", "similarity", "shared_facts"]

    def clean(v):
        return str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")

    with open(path, "w", encoding="utf-8-sig", newline="") as out:
        out.write("\t".join(headers) + "\n")
        for row in similarity_rows:
            out.write("\t".join(clean(row[h]) for h in headers) + "\n")
