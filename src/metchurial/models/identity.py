# -*- coding: utf-8 -*-
"""Query identity models: one structural-signature row per statement, and
one similarity score per near-miss pair of distinct core_ids."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IdentityRow:
    """One statement's structural identity. `fact_set` is the canonical
    fact strings the `core_id` hashes; it rides along for the corpus-wide
    similarity pass and is never written to TSV directly. `columns`,
    `tables`, `join_types`, `relations`, `predicates`, and `groupby` are
    human-readable breakouts of that same fact_set by category (see
    query_identity.build_identity_row) -- supplementary reporting only,
    never read back to recompute the core_id."""

    core_id: str
    file: str
    line: int | None
    table_count: int
    join_count: int
    predicate_count: int
    fact_set: frozenset[str]
    columns: tuple[str, ...]
    tables: tuple[str, ...]
    join_types: tuple[str, ...]
    relations: tuple[str, ...]
    predicates: tuple[str, ...]
    groupby: tuple[str, ...]


@dataclass
class SimilarityPair:
    """Jaccard similarity between two distinct core_ids' fact sets."""

    core_id_a: str
    core_id_b: str
    similarity: float
    shared_facts: int
