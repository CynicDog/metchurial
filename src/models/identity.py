# -*- coding: utf-8 -*-
"""Query identity models: one structural-signature row per statement, and
one similarity score per near-miss pair of distinct core_ids."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IdentityRow:
    """One statement's structural identity. `fact_set` is the canonical
    fact strings the `core_id` hashes; it rides along for the corpus-wide
    similarity pass and is never written to TSV directly. `columns` lists
    every column the statement references (alias-resolved where possible)
    -- supplementary reporting only, never part of the core_id."""

    core_id: str
    file: str
    line: int | None
    table_count: int
    join_count: int
    predicate_count: int
    fact_set: frozenset[str]
    columns: tuple[str, ...]


@dataclass
class SimilarityPair:
    """Jaccard similarity between two distinct core_ids' fact sets."""

    core_id_a: str
    core_id_b: str
    similarity: float
    shared_facts: int
