# -*- coding: utf-8 -*-
"""JOIN relationship models: raw per-occurrence edges and their corpus-wide
rollup (refs_relations.tsv)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RelationEdge:
    """One raw JOIN edge occurrence between two real tables, from either
    the structural token-scan (explicit JOIN...ON/USING) or the
    WHERE-implicit comparison visitor (comma-joins)."""

    file: str
    line: int
    table_a_schema: str
    table_a: str
    table_b_schema: str
    table_b: str
    join_type: str
    predicate: str

    def pair_key(self) -> tuple[tuple[str, str], tuple[str, str]]:
        """Unordered table-pair grouping key (A-B and B-A collapse)."""
        a = (self.table_a_schema, self.table_a)
        b = (self.table_b_schema, self.table_b)
        first, second = sorted((a, b))
        return first, second


@dataclass
class RelationRollup:
    """One table pair's aggregated JOIN usage across the whole scan.
    `predicates` holds the sorted distinct predicate strings seen for the
    pair."""

    table_a_schema: str
    table_a: str
    table_b_schema: str
    table_b: str
    join_count: int
    predicates: tuple[str, ...]
