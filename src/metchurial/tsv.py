# -*- coding: utf-8 -*-
"""Generic TSV writing, shared by the report layer (report.py) and the
extraction modules that write their own artifact (references/relations.py,
references/query_identity.py) -- lives below both so extraction never has
to import the report layer."""

from __future__ import annotations

from typing import Iterable


def _clean(v: object) -> str:
    """One TSV field: tabs/newlines inside a field would break TSV columns."""
    return str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def _cell(v: object) -> object:
    """A list/tuple attribute renders as one '; '-joined TSV cell (e.g. a
    rollup's predicates, an identity row's columns)."""
    if isinstance(v, (list, tuple)):
        return "; ".join(str(item) for item in v)
    return v


def write_refs_tsv(path: str, headers: list[str], rows: Iterable[object]) -> None:
    """Generic TSV writer for the --extract-metadata artifacts
    (refs_tables.tsv, refs_columns.tsv, refs_functions.tsv,
    refs_relations.tsv, refs_query_*.tsv), same conventions as
    report.write_tsv_report (utf-8-sig, tab-separated, header row always
    written even for an empty `rows` list, embedded tabs/newlines
    stripped). `rows` is a list of model objects; only the attributes
    named in `headers` are written, in that order -- generic over each
    file's differing column set (refs_tables.tsv has no "column" field,
    refs_columns.tsv does). A list/tuple attribute is joined with '; '
    into one cell (see _cell)."""
    with open(path, "w", encoding="utf-8-sig", newline="") as out:
        out.write("\t".join(headers) + "\n")
        for row in rows:
            out.write("\t".join(_clean(_cell(getattr(row, h))) for h in headers) + "\n")
