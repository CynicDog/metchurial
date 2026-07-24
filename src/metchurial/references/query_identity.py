# -*- coding: utf-8 -*-
"""SQL query identification (--extract-metadata): assigns each statement
a `core_id`, a hash of its structural signature, so a corpus of thousands
of files canonicalizes down to its distinct core queries.

Every statement's *full* fact set (canonical fact strings, one set per
statement) has six categories:

* ``TBL|schema|table``       -- every real table referenced, alias-free
* ``JOINTYPE|type=n``        -- join-type multiset (JOIN/INNER/COMMA
  collapse to INNER; LEFT/RIGHT/FULL/CROSS stay distinct)
* ``REL|op|t1.c1|t2.c2``     -- a comparison joining two distinct tables
  (pair-sorted), from ON clauses and comma-join WHERE equalities alike
* ``PRED|operand|op``        -- a WHERE filter predicate's operand
  signature and operator (comparison/BETWEEN/LIKE/IS [NOT] NULL/IN); the
  operand is ``table.col`` for a resolvable qualified column, a bare
  column's own name if unqualified, or ``FN(...)`` over either shape of
  its column arguments (function name plus column inputs -- literal
  arguments are always excluded)
* ``GROUPBY|operand``        -- each GROUP BY item, same operand
  signature (a bare unqualified column keeps its own name)
* ``SHAPE|BLOCKS=n``         -- total query-block count for the statement
  (the outer block plus every CTE body and derived-table subquery,
  table_scan.scan_query_blocks' own count). Without this, a statement that
  only wraps another query -- `WITH cte AS (<q>) SELECT * FROM cte` or
  `SELECT * FROM (<q>) x` with no join/predicate/grouping of its own --
  contributes zero TBL/JOINTYPE/REL/PRED/GROUPBY facts beyond `<q>`'s own,
  so it collapsed onto the bare statement `<q>` in another file even
  though one is a CTE/subquery wrapper and the other is not.

Condensed grouping -- core_id vs. the full fact set:
    `core_id` is NOT (necessarily) a hash of the full fact set above. It's a
    hash of a narrower subset selected by `--identity-granularity` (see
    `_facts_for_granularity` / `_GRANULARITY_PREFIXES`), one of four tiers,
    loosest to strictest:

    * ``table``      -- TBL only
    * ``structure``  -- TBL, JOINTYPE, REL, SHAPE (the default -- this was
      once the only option, and still reproduces that original hardcoded
      behavior exactly)
    * ``filtered``    -- structure + PRED
    * ``strict``      -- filtered + GROUPBY (= the full fact set)

    The point of identity here is to collapse a corpus of thousands of
    files down to a short list of *distinct core queries* -- at the
    `structure` default, the same report re-run with a narrower WHERE
    filter, or grouped by one extra column, is still the same underlying
    query touching the same tables through the same joins, and splitting
    it into its own core_id just re-inflates the "distinct queries" list
    back toward the file count, defeating the point. A looser tier
    (`table`) collapses further -- even a join-topology change stops
    mattering; a stricter tier (`filtered`/`strict`) re-introduces WHERE/
    GROUP BY as discriminators for callers doing finer-grained duplicate
    detection instead of a coarse query-count audit. Two statements
    sharing a core_id at a looser tier can still differ in facts a
    stricter tier would have split them on -- that's not lost information,
    it still lives in the full fact set (`IdentityRow.fact_set`), which
    `--query-similarity` scores over regardless of granularity (see
    below) -- it's just not always what *identity* discriminates on.

    At the `structure` default: statements that differ only in SELECT-list
    projection, column aliasing, derived-column arithmetic, table aliases,
    formatting, comments, literal values, ORDER BY, HAVING, WHERE filters,
    or grouping share a core_id; statements that differ in tables, join
    topology, or join types do not. All facts come from the parse tree
    and the token-scan (table_scan.py) with aliases resolved to real
    table names -- never from normalizing SQL text.

Each identity row also carries supplementary reporting-only fields, never
read back into the core_id: ``columns`` (every column the statement
references, alias-resolved where possible -- without table layout
information a ``SELECT *`` cannot be resolved to columns, so column sets
are not reliable identity evidence) and ``has_cte``/``has_subquery``/
``has_union`` (whether the statement's shape includes a WITH clause, a
derived-table/scalar/IN/EXISTS subquery, or a UNION/INTERSECT/EXCEPT --
SHAPE|BLOCKS above is what actually keeps these from collapsing a
wrapper statement onto the bare query it wraps; these three just surface
that shape in refs_query_identity.tsv).

Known limitations, each pinned by tests/test_query_identity_complex.py:

* Function fingerprints are name + column inputs only -- two calls
  differing solely in literal arguments or argument order collapse.
* A correlated subquery's reference to an outer alias doesn't resolve
  (scoping is per query block), so a JOIN and its correlated-EXISTS
  rewrite deliberately get different signatures.
* `has_subquery` is read off the parse tree (fullselect_in_parentheses/
  nested_table_reference), so it can under-report on a statement that
  doesn't parse as one clean tree -- e.g. a reserved-keyword-colliding
  alias elsewhere in the same statement (see TestReservedKeywordCteNames).
  `has_cte`/`has_union` don't share this weakness: they're read straight
  off the token stream (table_scan.find_cte_names/has_set_operator), no
  parse tree required.

Statements that don't share a core_id get a corpus-wide Jaccard
similarity score over each distinct core_id's representative *full* fact
set (compute_similarity, O(unique-core-ids^2), stdlib-only) -- unlike
core_id, similarity deliberately keeps PRED/GROUPBY granularity, since
its whole purpose is surfacing near-misses at a finer resolution than
identity does. Each scored pair also carries `only_in_a`/`only_in_b`: the
human-readable symmetric difference between the two representative fact
sets, so a reader can see *which* facts actually differ, not just that
they scored similar.

See docs/query-identity.md and docs/query-similarity.md for the full
design, worked examples, and how the two features relate.
"""

from __future__ import annotations

import hashlib
from typing import Any

from metchurial._generated.Db2Parser import Db2Parser
from metchurial._generated.Db2ParserVisitor import Db2ParserVisitor

from metchurial.models.identity import IdentityRow, SimilarityPair
from metchurial.models.options import DEFAULT_IDENTITY_GRANULARITY
from metchurial.models.tables import QueryBlock
from metchurial.parsing.predicates import COMPARISON_OPS, classify_predicate, subject_expression
from metchurial.references import table_scan
from metchurial.tsv import write_refs_tsv

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


def _bare_column_operand(expr_ctx: Any) -> str | None:
    """`expr_ctx`'s own unqualified column_name text, upper-cased, if it is
    one -- the same fallback visitGrouping_expression already applies to a
    bare GROUP BY item ("a bare unqualified column keeps its own name"),
    reused here so an unqualified predicate operand (`WHERE mycol = 1`) or
    function argument (`SUBSTR(mycol, 1, 6)`) doesn't silently vanish just
    because it carries no table/alias qualifier to resolve."""
    col = expr_ctx.column_name()
    return col.getText().upper() if col is not None else None


def _operand_signature(expr_ctx: Any, query_blocks: list[QueryBlock]) -> str | None:
    """Canonical, alias- and literal-independent signature of a predicate
    operand or GROUP BY item: ``TABLE.COL`` for a resolvable qualified
    column, the column's own name if unqualified, ``FN(...)`` for a
    function call over its column arguments in either shape (literals and
    unresolvable arguments are dropped, so ``COUNT(*)`` becomes
    ``COUNT()`` and only the function name and its column inputs
    discriminate), else None."""
    resolved = _resolve_field_reference(expr_ctx, query_blocks)
    if resolved is not None:
        return "{}.{}".format(*resolved)
    fn = expr_ctx.function_invocation()
    if fn is None:
        return _bare_column_operand(expr_ctx)
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
            else:
                bare = _bare_column_operand(arg_expr)
                if bare is not None:
                    cols.append(bare)
    return "{}({})".format(name, ",".join(cols))


class _PredicateFactVisitor(Db2ParserVisitor):
    """Accumulates canonical REL/PRED/GROUPBY fact strings, plus the
    supplementary `columns` set, across however many times
    statement_driver.py's tiered driver calls .visit() on this chunk's
    committed fragments (once per Tier-1/Tier-2 fragment) -- state just
    grows across calls, a chunk's own instance is only read back after
    the whole file's parse_file() call returns (see engine.py).

    REL/PRED/GROUPBY all land in the same `.facts` set here -- the split
    between "counts toward core_id" (REL) and "counts toward the full
    fact_set only" (PRED/GROUPBY) isn't made until build_identity_row
    calls _facts_for_core_id, downstream of this visitor entirely. Kept
    that way rather than filtering here so build_fact_set's *full* fact
    set (what compute_similarity scores over) doesn't need reassembling
    from two separate visitor-tracked sets."""

    def __init__(self, query_blocks: list[QueryBlock]) -> None:
        self.query_blocks = query_blocks
        self.facts: set[str] = set()
        # Every column the statement references, alias-resolved to
        # TABLE.COL where possible (bare columns keep their own name).
        # Reported as a supplementary TSV column only -- never part of
        # the signature, since SELECT * is unresolvable without table
        # layout information.
        self.columns: set[str] = set()
        # has_subquery -- a supplementary TSV column only, never part of
        # the signature (SHAPE|BLOCKS in build_fact_set already keeps a
        # CTE/subquery/UNION statement from collapsing onto the bare query
        # it wraps; this just makes that shape visible in the report).
        # has_cte/has_union are siblings of this flag but live outside this
        # visitor (build_identity_row derives them straight from
        # table_scan's token-scan -- see its own docstring for why).
        # has_subquery is read off the grammar instead: a CTE body's own
        # parens are written inline in common_table_expression's rule
        # (`AS '(' fullselect ')'`), never through the fullselect_in_
        # parentheses subrule a derived table or a scalar/IN/EXISTS/ANY/
        # ALL subquery goes through -- so the two can never be confused by
        # construction. The trade-off: like every other fact this visitor
        # collects, it only sees committed (successfully parsed) fragments
        # -- a statement that fails to parse as one clean tree (e.g. a
        # reserved-keyword-colliding alias elsewhere in it, see
        # TestReservedKeywordCteNames) can under-report a real subquery,
        # unlike has_cte/has_union's token-scan, which doesn't need a
        # parse tree at all.
        self.has_subquery = False

    def visitFullselect_in_parentheses(
            self, ctx: Db2Parser.Fullselect_in_parenthesesContext) -> Any:
        self.has_subquery = True
        return self.visitChildren(ctx)

    def visitNested_table_reference(self, ctx: Db2Parser.Nested_table_referenceContext) -> Any:
        # A derived table (`FROM (SELECT ...) x`) embeds its own
        # '(' fullselect ')' directly, the same way common_table_expression
        # does -- it doesn't go through fullselect_in_parentheses either,
        # so it needs its own hook.
        self.has_subquery = True
        return self.visitChildren(ctx)

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
    facts.add("SHAPE|BLOCKS={}".format(len(query_blocks)))
    return frozenset(facts)


# Fact-string prefixes each --identity-granularity tier includes, loosest
# to strictest -- see this module's docstring, "Condensed grouping". Every
# tier's facts still live in the full fact_set every IdentityRow carries
# (and that compute_similarity always scores over, regardless of the tier
# chosen); this only controls what core_id_for hashes.
_GRANULARITY_PREFIXES = {
    "table": ("TBL|",),
    "structure": ("TBL|", "JOINTYPE|", "REL|", "SHAPE|"),
    "filtered": ("TBL|", "JOINTYPE|", "REL|", "SHAPE|", "PRED|"),
    "strict": ("TBL|", "JOINTYPE|", "REL|", "SHAPE|", "PRED|", "GROUPBY|"),
}


def _facts_for_granularity(fact_set: frozenset[str], granularity: str) -> frozenset[str]:
    """The subset of a statement's full fact set that actually
    discriminates its core_id at the given --identity-granularity tier.
    Two statements whose only difference is a fact category excluded at
    that tier (e.g. a WHERE predicate at `structure`) hash identically
    once passed through this filter, so they land on the same core_id even
    though their full fact_sets (and thus their Jaccard similarity against
    a third statement) still differ."""
    prefixes = _GRANULARITY_PREFIXES[granularity]
    return frozenset(f for f in fact_set if f.startswith(prefixes))


def core_id_for(fact_set: frozenset[str]) -> str:
    """Deterministic short hex id -- order-independent (fact_set is
    hashed via a sorted, joined repr, not Python's own unstable hash()).
    Callers pass the *narrowed* fact set (_facts_for_granularity's output),
    not a statement's full fact_set -- build_identity_row is the only
    caller and does this for you."""
    canonical = "\n".join(sorted(fact_set))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest[:CORE_ID_LENGTH]


def _facts_by_prefix(fact_set: frozenset[str], prefix: str) -> list[str]:
    """Every fact string in a given category, prefix stripped, sorted."""
    return sorted(f[len(prefix):] for f in fact_set if f.startswith(prefix))


def _reformat_rel(stripped: str) -> str:
    """A REL|-stripped fact is "op|a|b" (see _handle_comparison) --
    rendered "a op b" for the TSV. table/col/op names never contain "|"
    themselves, so a 3-way split is exact."""
    op, a, b = stripped.split("|", 2)
    return "{} {} {}".format(a, op, b)


def _reformat_pred(stripped: str) -> str:
    """A PRED|-stripped fact is "operand|op" (see _handle_single /
    _handle_comparison) -- rendered "operand op" for the TSV. The operand
    (a bare TABLE.COL or FN(TABLE.COL,...)) never contains "|"."""
    operand, op = stripped.split("|", 1)
    return "{} {}".format(operand, op)


def _humanize_fact(fact: str) -> str:
    """One raw fact string (as stored in a full fact_set) rendered for
    human reading -- used for the pairwise similarity TSV's
    only_in_a/only_in_b diff columns, which mix every fact category
    together in one cell, unlike IdentityRow's own per-category breakouts
    (tables/join_types/relations), which never include PRED/GROUPBY at
    all (see this module's docstring, "Condensed grouping")."""
    if fact.startswith("TBL|"):
        return "table {}".format(fact[len("TBL|"):].replace("|", "."))
    if fact.startswith("JOINTYPE|"):
        return "join-type {}".format(fact[len("JOINTYPE|"):])
    if fact.startswith("REL|"):
        return "join {}".format(_reformat_rel(fact[len("REL|"):]))
    if fact.startswith("PRED|"):
        return "predicate {}".format(_reformat_pred(fact[len("PRED|"):]))
    if fact.startswith("GROUPBY|"):
        return "group-by {}".format(fact[len("GROUPBY|"):])
    if fact.startswith("SHAPE|"):
        return "shape {}".format(fact[len("SHAPE|"):])
    return fact  # pragma: no cover -- every fact_set entry has a known prefix


def build_identity_row(query_blocks: list[QueryBlock], predicate_visitor: _PredicateFactVisitor,
                       path: str, line: int | None, tokens: list[Any],
                       granularity: str = DEFAULT_IDENTITY_GRANULARITY) -> IdentityRow:
    """predicate_visitor: a _PredicateFactVisitor that has already visited
    every committed fragment of this chunk. Its `columns` set, its
    `has_subquery` flag, and the per-category fact breakouts below
    (`tables`/`join_types`/`relations`), ride along as supplementary
    information only -- human-readable views of the TBL/JOINTYPE/REL facts
    for the TSV, deliberately read from the *full* fact_set rather than the
    granularity-narrowed one, so they stay meaningful regardless of
    `granularity` (at the loosest `table` tier, `identity_facts` below
    carries no JOINTYPE/REL facts at all -- these fields would silently
    read as empty/zero if they were sourced from it instead). `fact_set`
    itself carries every fact (including PRED/GROUPBY, excluded from
    core_id at some or all tiers -- see this module's docstring) for
    compute_similarity to score over.

    `granularity`: one of IDENTITY_GRANULARITIES (models/options.py) --
    which fact categories discriminate `core_id` for this statement. Never
    affects `fact_set`, `columns`, `has_cte`/`has_subquery`/`has_union`, or
    the tables/join_types/relations breakouts -- only `core_id` itself.

    `tokens`: this chunk's own token slice (same one scan_query_blocks(tokens)
    was built from) -- `has_cte`/`has_union` are read straight off it via
    table_scan's token-scan (find_cte_names/has_set_operator), not off the
    parse tree, so they stay accurate even when this chunk doesn't parse
    as one clean tree (see _PredicateFactVisitor.has_subquery's own
    docstring for why that's not equally true of `has_subquery`)."""
    fact_set = build_fact_set(query_blocks, predicate_visitor.facts)
    identity_facts = _facts_for_granularity(fact_set, granularity)
    return IdentityRow(
        core_id=core_id_for(identity_facts), file=path, line=line,
        table_count=sum(1 for f in fact_set if f.startswith("TBL|")),
        join_count=sum(1 for f in fact_set if f.startswith("REL|")),
        has_cte=bool(table_scan.find_cte_names(tokens)),
        has_subquery=predicate_visitor.has_subquery,
        has_union=table_scan.has_set_operator(tokens),
        fact_set=fact_set,
        columns=tuple(sorted(predicate_visitor.columns)),
        tables=tuple(f.replace("|", ".") for f in _facts_by_prefix(fact_set, "TBL|")),
        join_types=tuple(_facts_by_prefix(fact_set, "JOINTYPE|")),
        relations=tuple(_reformat_rel(f) for f in _facts_by_prefix(fact_set, "REL|")),
    )


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def compute_similarity(identity_rows: list[IdentityRow],
                       threshold: float = 0.5) -> list[SimilarityPair]:
    """Groups rows by core_id, takes one representative *full* fact_set
    per distinct core_id (including PRED/GROUPBY -- see this module's
    docstring, "Condensed grouping": core_id itself deliberately excludes
    them, but similarity scoring deliberately keeps them, since surfacing
    a finer-grained near-miss than identity does is the whole point of
    this pass), and scores every pair of distinct core_ids against each
    other -- corpus-wide, called once after a full scan_tree() completes
    (not per-file: needs every core_id discovered across the whole scan
    to be meaningful). Returns one SimilarityPair per pair scoring at or
    above `threshold`, sorted by similarity desc. `only_in_a`/`only_in_b`
    on each pair are the human-readable symmetric difference (see
    _humanize_fact) -- sorted for stable output, not by any notion of
    importance."""
    representatives: dict[str, frozenset[str]] = {}
    for row in identity_rows:
        representatives.setdefault(row.core_id, row.fact_set)

    ids = sorted(representatives)
    pairs = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            facts_a, facts_b = representatives[a], representatives[b]
            score = _jaccard(facts_a, facts_b)
            if score >= threshold:
                pairs.append(SimilarityPair(
                    core_id_a=a, core_id_b=b,
                    similarity=round(score, 3),
                    shared_facts=len(facts_a & facts_b),
                    only_in_a=tuple(sorted(_humanize_fact(f) for f in facts_a - facts_b)),
                    only_in_b=tuple(sorted(_humanize_fact(f) for f in facts_b - facts_a)),
                ))
    pairs.sort(key=lambda p: -p.similarity)
    return pairs


def write_similarity_tsv(path: str, similarity_rows: list[SimilarityPair]) -> None:
    """Same TSV conventions as tsv.write_refs_tsv (utf-8-sig,
    tab-separated, header row always written even for an empty list)."""
    write_refs_tsv(path, ["core_id_a", "core_id_b", "similarity", "shared_facts",
                          "only_in_a", "only_in_b"],
                   similarity_rows)
