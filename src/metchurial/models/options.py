# -*- coding: utf-8 -*-
"""ScanOptions: every knob a scan takes, as one frozen value object.

One options object travels through the whole pipeline (cli -> scan_tree ->
worker processes -> scan_file) instead of a parallel set of positional
flags threaded through each signature -- adding a new analysis means
adding one field here, not touching five call sites. Stdlib-only, like
every model module (see models/__init__.py)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import AbstractSet

# Default sensitive column names (case-insensitive) for sensitive-column
# comparison detection. Placeholders, not real production names -- see
# README's "Public placeholder names". Override with --sensitive-columns /
# ScanOptions(sensitive_columns=...), which fully replaces this list.
DEFAULT_SENSITIVE_COLUMNS = ("ACCT_ID", "CTRT_NO", "ACCT_NM", "ACCT_NAME")

# Default file extensions to scan (without the dot). DB2 SQL is sometimes
# exported/kept as plain .txt rather than .sql.
DEFAULT_EXTENSIONS = ("sql", "txt")

# Default cap on the tiered resync driver's per-statement-chunk loop
# iterations -- a runtime bound, not a termination guarantee (see
# parsing/statement_driver.py, which owns the mechanism this bounds).
DEFAULT_MAX_CHUNK_ITERATIONS = 200000


@dataclass(frozen=True)
class ScanOptions:
    """What to detect and extract, and how hard to try.

    Detection (always on) is configured by `sensitive_columns` /
    `stopwords` / `known_names`; each `extract_*` field switches one
    opt-in analysis on; `split_selects` additionally writes -NN split
    files next to each multi-SELECT source file (a filesystem side
    effect, not just extra result fields).
    """

    sensitive_columns: tuple[str, ...] = DEFAULT_SENSITIVE_COLUMNS
    stopwords: AbstractSet[str] = frozenset()
    known_names: AbstractSet[str] = frozenset()
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS
    extract_table_refs: bool = False
    extract_column_refs: bool = False
    extract_relations: bool = False
    extract_functions: bool = False
    extract_query_identity: bool = False
    split_selects: bool = False
    workers: int = 1
    max_chunk_iterations: int = DEFAULT_MAX_CHUNK_ITERATIONS

    @classmethod
    def metadata(cls, **overrides: object) -> ScanOptions:
        """ScanOptions with every extract_* analysis switched on -- the
        library-side equivalent of the CLI's --extract-metadata flag.
        Keyword overrides are applied on top, so
        ``ScanOptions.metadata(workers=4)`` works as expected."""
        return replace(cls(
            extract_table_refs=True, extract_column_refs=True,
            extract_relations=True, extract_functions=True,
            extract_query_identity=True), **overrides)
