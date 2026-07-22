# -*- coding: utf-8 -*-
"""Orchestrates a full scan: scan_file() drives one file end to end through
metadata extraction (table/column/function/relation references, opt-in via
--extract-metadata) alongside sensitive-column comparison detection and
known-name matching (always on) and split-select counting (opt-in);
scan_tree() walks a directory tree and merges per-file results, optionally
across worker processes.

Sensitive-column comparison detection (FINDING) matches a hardcoded literal
against a sensitive column, via a tiered ANTLR parse over live code
(statement_driver.py, in_comment=N) plus an isolated re-parse of each
comment's own text (comment_rescan.py, in_comment=Y).

Known-name matching (FINDING) matches a literal's exact text against a
curated list rather than a heuristic: any 2-4 Hangul-syllable quoted literal
(NAME_LITERAL_RE) is a name candidate, found via a whole-file regex pass
over raw text. A candidate in `known_names` becomes a finding the same way a
comparison-detection column match does; a candidate in `stopwords` is
dropped; everything else is returned as `name_candidates`, the
still-unclassified pool that feeds strings.txt.
"""

from __future__ import annotations

import bisect
import os
import re
import time
from typing import Any, Callable, Iterator

from antlr4.Token import Token

from metchurial.detect.bad_file_check import check_file_quality
from metchurial.detect.comment_rescan import comment_tokens, rescan_comments
from metchurial.detect.extractor_visitor import ExtractorVisitor
from metchurial.detect.supplementary_checks import make_token_scan_fallback
from metchurial.io_utils import read_text
from metchurial.models.bad_file import BadFileReason
from metchurial.models.findings import Finding
from metchurial.models.options import DEFAULT_SENSITIVE_COLUMNS, ScanOptions
from metchurial.models.parse_stats import ParseStats
from metchurial.models.references import ColumnUse, FunctionCall, TableUse
from metchurial.models.relations import RelationEdge
from metchurial.models.results import FileScanResult, TreeScanResult
from metchurial.models.split import SplitManifestRow
from metchurial.models.tables import QueryBlock
from metchurial.parsing.statement_driver import chunk_ranges, lex_file, parse_file
from metchurial.references import query_identity, relations, table_scan
from metchurial.references.function_visitor import FunctionVisitor
from metchurial.references.reference_visitor import ReferenceVisitor
from metchurial.split import select_blocks

# Backward-friendly alias; the actual defaults live on ScanOptions
# (models/options.py), the single source of truth for every scan knob.
DEFAULT_COLUMNS = list(DEFAULT_SENSITIVE_COLUMNS)

# One file finished scanning: called as progress(i, total, path, result) --
# `result` is that file's FileScanResult (cached or freshly scanned), so a
# caller (cli.py's --verbose) can report on result.parse_stats without
# engine.py needing to know anything about how that gets displayed.
ProgressFn = Callable[[int, int, str, FileScanResult], None]

# Cap on a Markdown/TSV snippet's length (one source line, already).
SNIPPET_MAX_LEN = 160

# Known-name matching's name-candidate shape filter: 2-4 hangul syllables
# inside quotes. Deliberately applied to the raw file text, not the token
# stream: the spec is "name-shaped quoted text anywhere in the file",
# which includes text inside comment tokens and inside regions the lexer
# couldn't cleanly tokenize -- neither of which surfaces as a
# STRING_LITERAL token. Comment-ness is reconciled afterwards against the
# lexer's comment-token spans (see in_comment below).
NAME_LITERAL_RE = re.compile(r"""['"]([가-힣]{2,4})['"]""")


def _is_blank_literal(value: str) -> bool:
    """True for an empty/whitespace-only quoted literal ('', "", '   '),
    which is a placeholder/default value rather than a real hardcoded
    sensitive value and shouldn't be reported."""
    if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
        return value[1:-1].strip() == ""
    return False


def _line_offsets(text: str) -> list[int]:
    """Return the 0-based character offset where each line starts, used to
    map a known-name-matching regex match's character position back to a
    line number."""
    offsets = [0]
    pos = text.find("\n")
    while pos != -1:
        offsets.append(pos + 1)
        pos = text.find("\n", pos + 1)
    return offsets


def _line_of(offsets: list[int], pos: int) -> int:
    return bisect.bisect_right(offsets, pos)


def _snippet_of(lines: list[str], line_no: int) -> str:
    if 1 <= line_no <= len(lines):
        text = lines[line_no - 1].strip()
    else:
        text = ""
    if len(text) > SNIPPET_MAX_LEN:
        text = text[:SNIPPET_MAX_LEN] + "..."
    return text


def scan_file(path: str, options: ScanOptions | None = None) -> FileScanResult:
    """Scan one file. Returns a FileScanResult (metchurial/models/results.py).

    `options` (default: a plain ScanOptions()) carries every knob: which
    column names count as sensitive, the known_names/stopwords sets that
    drive known-name matching (a name-shaped literal in `known_names`
    becomes a finding; `name_candidates` is every name-shaped literal in
    neither set, still awaiting triage -- see write_strings_file), which
    opt-in extract_* analyses run, and the tiered parse driver's per-chunk
    resync-loop cap (statement_driver.py). `options.split_selects` also
    writes -NN split files alongside `path` as a side effect.

    `bad_reason` is None on a normal scan; otherwise a BadFileReason
    (models/bad_file.py), with every other field empty/zero. Set for an
    unreadable file (OSError), a cheap up-front quality check
    (bad_file_check.py) that skipped the expensive parse entirely, or an
    unexpected exception caught here so one bad file can't take down a
    whole tree scan. Not printed per-file to stderr -- recorded in
    bad_files.tsv, with cli.py printing one aggregate count at the end.

    `parse_stats` (models/parse_stats.py) is set on the returned result
    for a normal scan, None for a bad file -- there's no ANTLR work to
    report on in that case. `elapsed_seconds` covers this whole call
    (lexing, quality gate, and every detection/extraction pass), not just
    the tiered parse -- see cli.py's --verbose summary line."""
    options = options if options is not None else ScanOptions()
    t0 = time.perf_counter()
    try:
        text, enc = read_text(path)
    except OSError as e:
        return FileScanResult(bad_reason=BadFileReason(
            category="unreadable", item=type(e).__name__,
            message="cannot read: {}: {}".format(type(e).__name__, e)))

    # Cheap lex-only quality gate: catches the common case (heavy non-SQL
    # noise) before spending any time in the expensive tiered driver. The
    # lex result is threaded through to parse_file so each file is lexed
    # exactly once.
    lexed = lex_file(text)
    bad_reason = check_file_quality(*lexed)
    if bad_reason is not None:
        return FileScanResult(bad_reason=bad_reason)

    try:
        result = _scan_file_body(path, text, enc, options, lexed)
    except Exception as e:
        return FileScanResult(bad_reason=BadFileReason(
            category="crash", item=type(e).__name__,
            message="crashed while scanning: {}: {}".format(type(e).__name__, e)))
    if result.parse_stats is not None:
        result.parse_stats.elapsed_seconds = time.perf_counter() - t0
    return result


def _scan_file_body(path: str, text: str, enc: str, options: ScanOptions,
                    lexed: tuple[list[Token], list[tuple[int, int, str]]] | None = None,
                    ) -> FileScanResult:
    """Runs the actual scan; split out from scan_file() so its try/except
    wraps one simple call. Everything below assumes well-formed input --
    it isn't itself defensive."""
    columns = options.sensitive_columns
    stopwords = options.stopwords
    known_names = options.known_names
    result = FileScanResult()
    result.parse_stats = ParseStats()
    # One (query_blocks, predicate_visitor, line, tokens) tuple per chunk,
    # appended inside pre_chunk_hook -- can only be turned into final
    # IdentityRows *after* parse_file() returns for the whole file, since a
    # chunk's predicate_visitor keeps accumulating across however many
    # times the tiered driver calls .visit() on that chunk's own committed
    # fragments (see query_identity.py's module docstring). `tokens` is the
    # chunk's own token slice, kept around so has_cte/has_union can be read
    # off it directly (table_scan's token-scan) rather than the parse tree.
    query_identity_chunks: list[tuple[list[QueryBlock], Any, int | None, list[Token]]] = []
    lines = text.splitlines()
    seen_hit_lines: set[int] = set()

    def make_hit(column: str, operator: str, value: str, line: int, in_comment: str,
                 start_offset: int | None = None, end_offset: int | None = None) -> None:
        if _is_blank_literal(value):
            return
        result.findings.append(Finding(
            severity="FINDING",
            file=path,
            line=line,
            column_name=column.upper(),
            operator=operator.strip().upper(),
            value=value,
            snippet=_snippet_of(lines, line),
            encoding=enc,
            in_comment=in_comment,
            start_offset=start_offset,
            end_offset=end_offset,
        ))
        seen_hit_lines.add(line)

    visitor = ExtractorVisitor(
        columns,
        lambda col, op, val, line, so, eo: make_hit(col, op, val, line, "N", so, eo))
    fallback = make_token_scan_fallback(
        columns,
        lambda col, op, val, line, so, eo: make_hit(col, op, val, line, "N", so, eo))

    need_blocks = (options.extract_table_refs or options.extract_column_refs
                   or options.extract_relations or options.extract_query_identity)

    def pre_chunk_hook(all_tokens: list[Token], start: int, end: int) -> tuple[Any, ...]:
        extra_visitors: list[Any] = []
        if options.extract_functions:
            def fn_sink(name: str, params: str, line: int) -> None:
                result.function_calls.append(
                    FunctionCall(function=name, parameters=params, file=path, line=line))
            extra_visitors.append(FunctionVisitor(text, fn_sink))
        if not need_blocks:
            return tuple(extra_visitors)
        chunk_tokens = all_tokens[start:end]
        blocks = table_scan.scan_query_blocks(chunk_tokens)
        if options.extract_query_identity:
            predicate_visitor = query_identity.new_predicate_visitor(blocks)
            extra_visitors.append(predicate_visitor)
            chunk_line = next(
                (t.line for t in chunk_tokens if t.channel == Token.DEFAULT_CHANNEL), None)
            query_identity_chunks.append((blocks, predicate_visitor, chunk_line, chunk_tokens))
        if options.extract_table_refs:
            for tref in table_scan.iter_table_refs(blocks):
                result.table_uses.append(
                    TableUse(schema=tref.schema, table=tref.table, file=path, line=tref.line))
        if options.extract_relations:
            # Structural edges cover every join type except COMMA (which
            # carries no predicate); comma-joins get their predicate
            # exclusively from the WHERE-implicit visitor below, so
            # excluding them here avoids double-counting. A comma-joined
            # pair with no WHERE condition linking it goes unrecorded --
            # a known limitation, not a bug. A CTE-participating edge
            # (either side is_cte) is also excluded: refs_relations.tsv
            # deliberately only ever shows real table-to-table pairs, while
            # table_scan.py preserves CTE edges for query_identity.py's
            # join-type signal.
            structural_edges = [e for e in table_scan.scan_join_edges(blocks)
                               if e.join_type != "COMMA" and not e.left.is_cte and not e.right.is_cte]
            result.relation_edges.extend(
                relations.structural_edges_to_models(path, structural_edges))
            # An explicit `JOIN ... ON`'s own ON-clause is also visited by
            # the WHERE-implicit visitor below (it's independently
            # re-surfaced as an orphaned search_condition tree -- see
            # table_scan.py), so skip a table pair here once it already
            # has a structural edge. This chunk-level dedup can undercount
            # a genuinely separate redundant WHERE-equality for the same
            # pair in the same chunk, which is rare and preferable to
            # systematically overcounting every ordinary JOIN.
            structural_pairs = {
                tuple(sorted(((e.left.schema, e.left.table), (e.right.schema, e.right.table))))
                for e in structural_edges
            }

            def join_sink(lschema: str, ltable: str, rschema: str, rtable: str,
                          join_type: str, predicate: str, line: int) -> None:
                pair = tuple(sorted(((lschema, ltable), (rschema, rtable))))
                if pair in structural_pairs:
                    return
                result.relation_edges.append(RelationEdge(
                    file=path, line=line,
                    table_a_schema=lschema, table_a=ltable,
                    table_b_schema=rschema, table_b=rtable,
                    join_type=join_type, predicate=predicate,
                ))
            extra_visitors.append(relations.make_join_predicate_visitor(blocks, join_sink))
        if options.extract_column_refs:
            def col_sink(schema: str, table: str, column: str, line: int) -> None:
                result.column_uses.append(
                    ColumnUse(schema=schema, table=table, column=column, file=path, line=line))
            extra_visitors.append(ReferenceVisitor(blocks, col_sink))
        return tuple(extra_visitors)

    all_tokens, _lexer_errors = parse_file(
        text, visitor, fallback, max_iterations_per_chunk=options.max_chunk_iterations,
        pre_chunk_hook=pre_chunk_hook, lexed=lexed, stats=result.parse_stats)

    # Only safe to finalize now -- every chunk's predicate_visitor has
    # seen every committed fragment of its own chunk by the time
    # parse_file() returns for the whole file (see query_identity_chunks'
    # own comment above). chunk_ranges() always contributes one trailing
    # range past the last ';' consisting only of the EOF token -- and EOF
    # is on the default channel (not hidden), so _discover_blocks' own
    # "non-SELECT statement" special case (for a bare UPDATE/DELETE/INSERT
    # with no SELECT keyword) fires on it too, pushing one real, empty
    # QueryBlock. Filtered out by content (no tables/facts at all) rather
    # than by an empty `blocks` list, which this chunk doesn't actually
    # have -- every file's trailing empty chunk would otherwise share the
    # same degenerate empty-fact-set core_id, falsely "clustering" every
    # scanned file together.
    for blocks, predicate_visitor, line, tokens in query_identity_chunks:
        row = query_identity.build_identity_row(blocks, predicate_visitor, path, line, tokens)
        if row.table_count or row.join_count or row.predicate_count:
            result.identity_rows.append(row)

    rescan_comments(
        all_tokens, columns,
        lambda col, op, val, line, ic, so, eo: make_hit(col, op, val, line, ic, so, eo),
        max_iterations_per_chunk=options.max_chunk_iterations)

    offsets = _line_offsets(text)
    comment_spans = sorted(
        (t.start, t.stop) for t in comment_tokens(all_tokens) if t.start is not None)
    comment_starts = [s for s, _ in comment_spans]

    def in_comment(pos: int) -> bool:
        idx = bisect.bisect_right(comment_starts, pos) - 1
        if idx < 0:
            return False
        start, end = comment_spans[idx]
        return start <= pos <= end

    for m in NAME_LITERAL_RE.finditer(text):
        pos = m.start()
        ln = _line_of(offsets, pos)
        if ln in seen_hit_lines:
            continue  # already reported as a finding on this line
        word = m.group(1)
        if word in known_names:
            # m.end() is exclusive; -1 converts to the 0-based
            # inclusive-inclusive span convention used everywhere else
            # (see extractor_visitor.as_literal). The "'" + word + "'"
            # value is always single-quote-normalized regardless of the
            # source's actual quote character -- masking must read that
            # off the original text at start_offset instead.
            make_hit("-", "-", "'" + word + "'", ln, "Y" if in_comment(pos) else "N",
                     m.start(), m.end() - 1)
        elif word not in stopwords:
            result.name_candidates.append(word)

    result.findings.sort(key=lambda f: f.line)

    if options.split_selects:
        ranges = chunk_ranges(all_tokens)
        blocks = select_blocks.select_block_ranges(all_tokens, ranges)
        result.select_block_count = len(blocks)
        written = select_blocks.write_split_files(path, text, all_tokens, blocks)
        if written:
            known_extensions = (frozenset(e.lower().lstrip(".") for e in options.extensions)
                                | _BACKUP_LIKE_EXTENSIONS)
            _delete_backup_siblings(path, known_extensions)
        total = len(written)
        result.split_manifest = [
            SplitManifestRow(original_file=path, split_file=split_path,
                             block_number=i, total_blocks=total)
            for i, split_path in enumerate(written, 1)
        ]

    return result


# Common backup-file suffixes, stripped alongside `options.extensions`
# itself when computing a file's identity for same-directory duplicate
# detection (see _file_identity) -- lets a ".bak" copy's *embedded* real
# extension (the ".sql" in "query1.sql.bak") also be peeled off, not just
# the outermost suffix that made it match the scan filter in the first
# place.
_BACKUP_LIKE_EXTENSIONS = frozenset({
    "bak", "backup", "bkup", "bk", "old", "orig", "save", "swp", "tmp",
})


def _file_identity(name: str, known_extensions: frozenset[str]) -> str:
    """Canonical identity for same-directory duplicate detection: strips
    trailing extensions one at a time as long as each one is either a
    configured scan extension or a common backup suffix
    (_BACKUP_LIKE_EXTENSIONS), so "query1.sql", "query1.sql.bak", and
    "query1.bak" all reduce to "query1". Case-folded so a case-insensitive
    filesystem (Windows/macOS default) doesn't split what's really one
    group."""
    stem = name
    while True:
        base, ext = os.path.splitext(stem)
        if not base or ext[1:].lower() not in known_extensions:
            return stem.lower()
        stem = base


def _delete_backup_siblings(path: str, known_extensions: frozenset[str]) -> None:
    """Called right after write_split_files has split `path` and deleted
    the original. Also deletes any same-directory, same-identity sibling
    (e.g. "query1.sql.bak" once "query1.sql" has been split) purely by
    name -- no content comparison, matching _dedupe_same_name_files'
    name-only rule below. Left alone, such a sibling wouldn't be caught by
    _dedupe_same_name_files on a later scan -- that only compares files
    present in the *same* run, and by the next run `path` itself is gone --
    so the sibling would look like fresh input and get split all over
    again under its own name, duplicating content this run already
    captured."""
    dirpath = os.path.dirname(path) or "."
    target_identity = _file_identity(os.path.basename(path), known_extensions)
    try:
        siblings = os.listdir(dirpath)
    except OSError:
        return
    for name in siblings:
        full = os.path.join(dirpath, name)
        if full == path or _file_identity(name, known_extensions) != target_identity:
            continue
        try:
            os.remove(full)
        except OSError:
            pass


def _dedupe_same_name_files(names: list[str], known_extensions: frozenset[str]) -> list[str]:
    """Collapses files that share a directory and an identity (see
    _file_identity) down to one representative, purely by name -- no
    content comparison. "query1.sql" and "query1.sql.bak" (or a lone
    "query1.bak") are always treated as the same file for scanning
    purposes, on the assumption that a backup-suffixed sibling is always
    just a copy (stale or otherwise) of the real file, never independent
    data.

    A name whose outer extension is backup-like (_BACKUP_LIKE_EXTENSIONS)
    always loses to one that isn't, regardless of length -- plain
    shortest-name-wins breaks down for a bare backup file like
    "query1.bak" sitting next to "query1.sql": both reduce to identity
    "query1" and are the same length, so a length-only tie-break falls
    through to alphabetical order, where "bak" sorts before "sql" and the
    backup copy would win, leaving the real source file completely
    unscanned. Among two non-backup (or two backup) names, the shortest
    is kept, tie-broken alphabetically for determinism."""
    groups: dict[str, list[str]] = {}
    for name in names:
        groups.setdefault(_file_identity(name, known_extensions), []).append(name)

    def rank(name: str) -> tuple[bool, int, str]:
        outer_ext = os.path.splitext(name)[1][1:].lower()
        return (outer_ext in _BACKUP_LIKE_EXTENSIONS, len(name), name)

    return [min(group, key=rank) for group in groups.values()]


def _is_stale_split_output(name: str, sibling_names: set[str]) -> bool:
    """True iff `name` looks like a --split-select output file (e.g.
    "report-01.sql") AND its un-suffixed original ("report.sql") is still
    present among `sibling_names` -- the actual double-count risk (split
    block counted once under the original's name, once under its own).
    write_split_files always deletes the original once its split siblings
    are written, so once that's actually happened, the split files are
    the only copy of that data left on disk and must be scanned like any
    other file -- otherwise a later, separate run (e.g. --extract-metadata
    by itself, after an earlier --split-selects run already deleted the
    original) would find nothing for that file, forever."""
    original = select_blocks.split_output_original_name(name)
    return original is not None and original in sibling_names


def _matching_files(root: str, suffixes: tuple[str, ...], extensions: tuple[str, ...],
                    exclude_paths: set[str]) -> Iterator[str]:
    known_extensions = (frozenset(e.lower().lstrip(".") for e in extensions)
                        | _BACKUP_LIKE_EXTENSIONS)
    for dirpath, _dirnames, filenames in os.walk(root):
        name_set = set(filenames)
        candidates = [name for name in filenames if name.lower().endswith(suffixes)
                     and not _is_stale_split_output(name, name_set)]
        for name in _dedupe_same_name_files(candidates, known_extensions):
            full = os.path.join(dirpath, name)
            if os.path.abspath(full) in exclude_paths:
                continue
            yield full


def _merge_result(tree: TreeScanResult, path: str, result: FileScanResult,
                  split_select: bool) -> None:
    """Fold one file's FileScanResult into the tree-wide accumulator."""
    tree.findings.extend(result.findings)
    tree.name_candidates.extend(result.name_candidates)
    tree.table_uses.extend(result.table_uses)
    tree.column_uses.extend(result.column_uses)
    tree.relation_edges.extend(result.relation_edges)
    tree.function_calls.extend(result.function_calls)
    tree.identity_rows.extend(result.identity_rows)
    if split_select:
        tree.select_block_counts[path] = result.select_block_count
        tree.split_manifest.extend(result.split_manifest)
    if result.bad_reason is not None:
        tree.bad_files[path] = result.bad_reason


def scan_tree(root: str, options: ScanOptions | None = None, *,
              exclude_paths: set[str] | None = None,
              progress: ProgressFn | None = None,
              cached_results: dict[str, FileScanResult] | None = None,
              on_file_result: Callable[[str, FileScanResult], None] | None = None,
              ) -> TreeScanResult:
    """Recursively scans files under root whose extension is in
    `options.extensions` (case-insensitive, without the dot). Returns a
    TreeScanResult (metchurial/models/results.py) merging every file's
    FileScanResult. One ScanOptions value configures everything
    (detection inputs, opt-in extract_* analyses, worker count, resync
    cap); it's handed unchanged to every scan_file() call.

    Same-directory files that share a name once backup-style extensions
    are stripped (e.g. "query1.sql" and "query1.sql.bak", or a lone
    "query1.bak") count as one file, not two -- see _file_identity /
    _dedupe_same_name_files. This is purely name-based, no content
    comparison: a same-identity sibling is always assumed to be a copy of
    the real file, so only one representative is ever scanned (and, under
    --split-selects, any same-identity sibling left over after a split is
    deleted too -- see _delete_backup_siblings).

    `exclude_paths` is an optional set of absolute paths to skip -- keeps
    the scanner's own output files from being scanned if they happen to
    live inside the scanned tree.

    `progress`, if given, is called as progress(i, total, path, result) as
    each file finishes -- the library itself never prints (cli.py passes
    a stderr printer here, unconditionally on now; --verbose only changes
    how much that printer shows per file).

    `cached_results`, if given, maps abspath -> a previously-computed
    FileScanResult to reuse instead of calling scan_file() for that path
    (--incremental; see incremental.py, which owns fingerprint/mode
    matching -- this function only consumes whatever the caller already
    decided is reusable). A file not present here is scanned normally.
    `on_file_result`, if given, is called as on_file_result(path, result)
    for every file once its result (cached or freshly scanned) is known
    -- lets a caller (cli.py) persist an updated cache without engine.py
    needing to know anything about cache file formats itself.

    `options.workers` > 1 scans files in separate processes
    (concurrent.futures.ProcessPoolExecutor -- parsing is CPU-bound pure
    Python, so this is real parallelism, not threads). Each file is
    scanned independently with no shared state, so only the merge order
    depends on completion order; report writers already group/sort
    findings by file and line regardless. This holds for identity rows
    too -- each row's own `core_id` is a pure hash of that one
    statement's own facts, so it comes back correct from any worker in
    any order; only query_identity.compute_similarity's corpus-wide pass
    (see cli.py) needs every row gathered back here first, so it
    deliberately isn't run per-worker."""
    options = options if options is not None else ScanOptions()
    suffixes = tuple("." + ext.lower().lstrip(".") for ext in options.extensions)
    exclude_paths = exclude_paths or set()
    cached_results = cached_results or {}
    tree = TreeScanResult()

    files = list(_matching_files(root, suffixes, options.extensions, exclude_paths))
    tree.file_count = len(files)

    def merge_one(full: str, result: FileScanResult) -> None:
        _merge_result(tree, full, result, options.split_selects)
        if on_file_result:
            on_file_result(full, result)

    if options.workers <= 1:
        for i, full in enumerate(files, 1):
            cached = cached_results.get(os.path.abspath(full))
            result = cached if cached is not None else scan_file(full, options)
            merge_one(full, result)
            if progress:
                progress(i, tree.file_count, full, result)
        return tree

    import concurrent.futures

    to_scan = [f for f in files if os.path.abspath(f) not in cached_results]

    with concurrent.futures.ProcessPoolExecutor(max_workers=options.workers) as pool:
        futures = {pool.submit(scan_file, full, options): full for full in to_scan}
        done = 0
        for full in files:
            cached = cached_results.get(os.path.abspath(full))
            if cached is not None:
                merge_one(full, cached)
                done += 1
                if progress:
                    progress(done, tree.file_count, full, cached)
        for fut in concurrent.futures.as_completed(futures):
            full = futures[fut]
            result = fut.result()
            merge_one(full, result)
            done += 1
            if progress:
                progress(done, tree.file_count, full, result)
    return tree
