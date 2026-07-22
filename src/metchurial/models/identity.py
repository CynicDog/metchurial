# -*- coding: utf-8 -*-
"""Query identity models: one structural-signature row per statement, and
one similarity score per near-miss pair of distinct core_ids."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IdentityRow:
    """One statement's structural identity. `fact_set` is the *full*
    canonical fact set (tables, join types, join relationships, filter
    predicates, GROUP BY items, query shape) -- it rides along for the
    corpus-wide similarity pass (query_identity.compute_similarity) and is
    never written to TSV directly. `core_id` is NOT a hash of `fact_set`
    itself: it's a hash of a narrower subset that excludes PRED|/GROUPBY|
    facts (see query_identity.py's module docstring, "Condensed
    grouping") -- so two statements can share a core_id while their
    fact_sets (and therefore their similarity score against a third
    statement) still differ. `has_cte`, `has_subquery`, `has_union`,
    `columns`, `tables`, `join_types`, and `relations` are human-readable
    breakouts of the *identity-relevant* facts only (see
    query_identity.build_identity_row) -- supplementary reporting only,
    never read back to recompute the core_id."""

    core_id: str
    file: str
    line: int | None
    table_count: int
    join_count: int
    has_cte: bool
    has_subquery: bool
    has_union: bool
    fact_set: frozenset[str]
    columns: tuple[str, ...]
    tables: tuple[str, ...]
    join_types: tuple[str, ...]
    relations: tuple[str, ...]


@dataclass
class SimilarityPair:
    """Jaccard similarity between two distinct core_ids' *full* fact sets
    (tables, join types, join relationships, filter predicates, GROUP BY
    items, query shape -- everything IdentityRow.fact_set carries, not
    just the narrower subset core_id hashes). `only_in_a`/`only_in_b` are
    the human-readable symmetric difference -- every fact one side has
    that the other doesn't -- so a reader can see *why* two statements
    that don't share a core_id still scored as similar, not just that
    they did."""

    core_id_a: str
    core_id_b: str
    similarity: float
    shared_facts: int
    only_in_a: tuple[str, ...]
    only_in_b: tuple[str, ...]
