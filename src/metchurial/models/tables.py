# -*- coding: utf-8 -*-
"""SQL structure models: table references, per-SELECT scopes, and JOIN
edges, as discovered by the token-scan engine (references/table_scan.py)."""

from __future__ import annotations

from dataclasses import dataclass, field

# Placeholder values for a reference whose schema/table could not be
# resolved (bare unqualified column, unknown alias, CTE excluded from
# resolution).
PLACEHOLDER_SCHEMA = "(no-schema)"
PLACEHOLDER_TABLE = "(no-table)"


@dataclass
class TableRef:
    """One table reference in a FROM/JOIN/UPDATE/INTO table list.

    `is_cte` marks a reference to a CTE name rather than a real schema
    object -- still resolvable via QueryBlock.alias_map (a later
    `cte_alias.col` must resolve to *something*) but excluded from
    `QueryBlock.tables`/refs_tables.tsv's real-table set and from
    refs_relations.tsv; only query identity's signature-building consumes
    CTE-participating join edges, deliberately."""

    schema: str
    table: str
    alias: str
    line: int
    start_char: int
    stop_char: int
    is_cte: bool = False


@dataclass
class QueryBlock:
    """One SELECT's own scope -- [start_char, stop_char) character range,
    its FROM/JOIN/UPDATE/INTO table references, and the alias->TableRef map
    used to resolve a qualified column reference (`a.col1`) back to a real
    schema.table. Scoped per query block (not globally) since a
    correlation name is only valid within the block that declares it.

    `join_connectors` holds one (left_ref, right_ref, join_type,
    predicate_text) tuple per comma/JOIN connector between two
    successfully-recognized tables in this block's own FROM-clause table
    list."""

    start_char: int
    stop_char: int | None = None
    tables: list[TableRef] = field(default_factory=list)
    alias_map: dict[str, TableRef] = field(default_factory=dict)
    join_connectors: list[tuple[TableRef, TableRef, str, str]] = field(default_factory=list)

    def add_table(self, ref: TableRef) -> None:
        # A CTE reference still needs to be resolvable via alias_map (a
        # later `cte_alias.col` must resolve to *something*), but must
        # never appear in `.tables` -- that's the "CTE names excluded from
        # real tables" contract iter_table_refs/refs_tables.tsv depend on.
        if not ref.is_cte:
            self.tables.append(ref)
        self.alias_map[ref.alias] = ref
        # DB2 allows using the real table name as its own qualifier even
        # when an explicit alias is also given -- but an explicit alias
        # always wins the same dict key, so only fill this in if unset.
        self.alias_map.setdefault(ref.table, ref)


@dataclass
class JoinEdge:
    """One resolved JOIN connector between two table references."""

    left: TableRef
    right: TableRef
    join_type: str
    predicate_text: str
    line: int
