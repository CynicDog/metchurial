# -*- coding: utf-8 -*-
"""Per-file result cache for --incremental: on a huge tree, most files are
unchanged between runs, so re-lexing and re-parsing every one of them from
scratch every time is wasted CPU-bound work that can add up to hours.
--incremental persists each file's FileScanResult (models/results.py) to
incremental_cache.json, keyed by absolute path, alongside a cheap identity
fingerprint (size, mtime_ns) and the `mode_signature` of the extract_*/
split_selects flags it was produced under. On a later run, a file whose
fingerprint and mode both still match is loaded straight from the cache
instead of being re-scanned -- its cached FileScanResult is merged into
the tree exactly as a fresh scan_file() call's result would be, so every
report (summary.md, refs_*.tsv, split_manifest.tsv, ...) stays complete
across incremental runs instead of shrinking to just the files touched
this run.

The fingerprint is (size, mtime_ns), not a content hash -- avoids reading
every unchanged file's full contents just to prove it is unchanged, which
would undercut the whole point of skipping the expensive work. This is
the same tradeoff make/ninja/ccache make by default: touching a file
without changing its content forces one extra rescan, which is cheap
insurance, not a correctness gap.

The mode signature exists because different flag combinations extract
different data -- a file "processed" by a plain scan hasn't had
--extract-metadata's analyses run on it yet, so a later --extract-metadata
run must not treat it as up to date just because its content hasn't
changed. Only an exact mode match is reused; any other mode difference
falls back to a fresh scan.
"""

from __future__ import annotations

import json
import os

from metchurial.models.findings import Finding
from metchurial.models.identity import IdentityRow
from metchurial.models.options import ScanOptions
from metchurial.models.references import ColumnUse, FunctionCall, TableUse
from metchurial.models.relations import RelationEdge
from metchurial.models.results import FileScanResult
from metchurial.models.split import SplitManifestRow

Fingerprint = tuple[int, int]


def mode_signature(options: ScanOptions) -> str:
    """Canonical string of the flags that change what a scan of a given
    file actually extracts -- sensitive_columns/stopwords/known_names/
    extensions/workers/max_chunk_iterations deliberately excluded, since
    none of them change what data a *matching* fingerprint's cached
    result represents for a *particular* file the same way extract_*/
    split_selects do wholesale (changing sensitive_columns, for instance,
    is already outside this feature's guarantees -- see README)."""
    flags = (
        options.extract_table_refs, options.extract_column_refs,
        options.extract_relations, options.extract_functions,
        options.extract_query_identity, options.split_selects,
    )
    return ",".join("1" if f else "0" for f in flags)


def fingerprint(path: str) -> Fingerprint:
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def load_cache(path: str) -> dict[str, dict]:
    """Loads incremental_cache.json. Returns {} if missing, or if it's
    unreadable/corrupt (a hand-edited or truncated cache file should
    degrade to "cache miss for everything", never crash the run)."""
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_cache(path: str, entries: dict[str, dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f)


def lookup(cache: dict[str, dict], abspath: str, mode: str) -> FileScanResult | None:
    """Returns the cached FileScanResult for `abspath` if the cache has an
    entry for it whose mode matches `mode` and whose stored fingerprint
    matches the file's current on-disk (size, mtime_ns) -- None otherwise
    (no entry, mode mismatch, changed/missing file)."""
    entry = cache.get(abspath)
    if entry is None or entry.get("mode") != mode:
        return None
    try:
        current = fingerprint(abspath)
    except OSError:
        return None
    if list(current) != entry.get("fingerprint"):
        return None
    return _deserialize_result(entry["result"])


def record(cache: dict[str, dict], abspath: str, mode: str, result: FileScanResult) -> None:
    """Updates `cache` in place with `result` under `abspath`, keyed by
    its current on-disk fingerprint. No-ops if `abspath` no longer exists
    -- e.g. a --split-selects original deleted as part of this very scan
    has nothing left to fingerprint, and its replacement split files get
    their own fresh cache entries under their own paths once scanned."""
    try:
        fp = fingerprint(abspath)
    except OSError:
        return
    cache[abspath] = {
        "mode": mode,
        "fingerprint": list(fp),
        "result": _serialize_result(result),
    }


def _serialize_result(result: FileScanResult) -> dict:
    return {
        "findings": [vars(f) for f in result.findings],
        "name_candidates": list(result.name_candidates),
        "table_uses": [vars(t) for t in result.table_uses],
        "column_uses": [vars(c) for c in result.column_uses],
        "relation_edges": [vars(r) for r in result.relation_edges],
        "select_block_count": result.select_block_count,
        "split_manifest": [vars(s) for s in result.split_manifest],
        "function_calls": [vars(fn) for fn in result.function_calls],
        "identity_rows": [_serialize_identity_row(r) for r in result.identity_rows],
        "bad_reason": result.bad_reason,
    }


def _serialize_identity_row(row: IdentityRow) -> dict:
    d = vars(row).copy()
    d["fact_set"] = sorted(d["fact_set"])
    return d


def _deserialize_identity_row(d: dict) -> IdentityRow:
    d = d.copy()
    d["fact_set"] = frozenset(d["fact_set"])
    d["columns"] = tuple(d["columns"])
    d["tables"] = tuple(d["tables"])
    d["join_types"] = tuple(d["join_types"])
    d["relations"] = tuple(d["relations"])
    d["predicates"] = tuple(d["predicates"])
    d["groupby"] = tuple(d["groupby"])
    return IdentityRow(**d)


def _deserialize_result(d: dict) -> FileScanResult:
    return FileScanResult(
        findings=[Finding(**f) for f in d["findings"]],
        name_candidates=list(d["name_candidates"]),
        table_uses=[TableUse(**t) for t in d["table_uses"]],
        column_uses=[ColumnUse(**c) for c in d["column_uses"]],
        relation_edges=[RelationEdge(**r) for r in d["relation_edges"]],
        select_block_count=d["select_block_count"],
        split_manifest=[SplitManifestRow(**s) for s in d["split_manifest"]],
        function_calls=[FunctionCall(**fn) for fn in d["function_calls"]],
        identity_rows=[_deserialize_identity_row(r) for r in d["identity_rows"]],
        bad_reason=d["bad_reason"],
    )
