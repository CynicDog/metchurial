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

import bisect
import os
import re
import sys

from antlr4.Token import Token

from src.references import query_identity, relations, table_scan
from src.split import select_blocks
from src.detect.bad_file_check import check_file_quality
from src.detect.comment_rescan import comment_tokens, rescan_comments
from src.detect.extractor_visitor import ExtractorVisitor
from src.io_utils import read_text
from src.references.function_visitor import FunctionVisitor
from src.references.reference_visitor import ReferenceVisitor
from src.detect.statement_driver import MAX_ITERATIONS_PER_CHUNK, chunk_ranges, lex_file, parse_file
from src.detect.supplementary_checks import make_token_scan_fallback

# Default sensitive column names (case-insensitive). Override with
# --sensitive-columns.
DEFAULT_COLUMNS = ["ACCT_ID", "CTRT_NO", "ACCT_NM", "ACCT_NAME"]

# Default file extensions to scan (without the dot). DB2 SQL is sometimes
# exported/kept as plain .txt rather than .sql -- override via --extensions.
DEFAULT_EXTENSIONS = ["sql", "txt"]

# Cap on a Markdown/TSV snippet's length (one source line, already).
SNIPPET_MAX_LEN = 160

# Known-name matching's name-candidate shape filter: 2-4 hangul syllables inside quotes.
# Not a heuristic itself -- just what makes a literal "name-shaped" enough
# to be worth checking against known_names.txt/stopwords.txt at all.
NAME_LITERAL_RE = re.compile(r"""['"]([가-힣]{2,4})['"]""")


def _is_blank_literal(value):
    """True for an empty/whitespace-only quoted literal ('', "", '   '),
    which is a placeholder/default value rather than a real hardcoded
    sensitive value and shouldn't be reported."""
    if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
        return value[1:-1].strip() == ""
    return False


def _line_offsets(text):
    """Return the 0-based character offset where each line starts, used to
    map a known-name-matching regex match's character position back to a
    line number."""
    offsets = [0]
    offsets.extend(m.end() for m in re.finditer("\n", text))
    return offsets


def _line_of(offsets, pos):
    return bisect.bisect_right(offsets, pos)


def _snippet_of(lines, line_no):
    if 1 <= line_no <= len(lines):
        text = lines[line_no - 1].strip()
    else:
        text = ""
    if len(text) > SNIPPET_MAX_LEN:
        text = text[:SNIPPET_MAX_LEN] + "..."
    return text


def scan_file(path, columns, stopwords, known_names=None,
              max_iterations_per_chunk=MAX_ITERATIONS_PER_CHUNK,
              extract_table_refs=False, extract_column_refs=False, extract_relations=False,
              split_select=False, extract_functions=False, extract_query_identity=False):
    """Scan one file. Returns (hits, name_candidates, refs, relation_edges,
    select_block_count, function_calls, query_identity_rows, bad_reason).

    `known_names`/`stopwords` (sets of literal text) drive known-name
    matching: a name-shaped literal in `known_names` becomes a finding;
    `name_candidates` is every name-shaped literal in neither set, still
    awaiting triage (see write_strings_file).

    `max_iterations_per_chunk` caps the tiered parse driver's per-chunk
    resync loop (statement_driver.py); exposed here so cli.py's
    --max-chunk-iterations can reach it.

    `extract_table_refs`/`extract_column_refs` (off by default) populate
    `refs`, a flat list of {"kind": "table"|"column", "schema", "table",
    "column" (kind="column" only), "file", "line"} dicts, one per
    syntactic occurrence (not deduplicated here -- see
    report.write_refs_tsv).

    `extract_relations` populates `relation_edges`, a flat list of raw
    JOIN-edge dicts (see relations.py) from both structural and
    WHERE-implicit sources.

    `split_select` populates `select_block_count`, the number of
    standalone SELECT-block chunks in this file (see select_blocks.py),
    and writes -NN split files alongside `path` as a side effect.

    `extract_functions` populates `function_calls`, a flat list of
    {"function", "parameters", "file", "line"} dicts, one per call/
    operator site -- "function" holds either a function name (SUBSTR,
    UPPER, ...) or an operator name (=, IN, BETWEEN, LIKE, IS NULL, ...),
    "parameters" the operands' raw source text (see function_visitor.py
    for known gaps: COUNT/MAX/LOWER, schema-qualified calls, some
    predicate forms).

    `extract_query_identity` populates `query_identity_rows`, one dict per
    statement (see query_identity.py): {"core_id", "file", "line",
    "table_count", "join_count", "predicate_count", "fact_set"} --
    "fact_set" is carried along for cli.py's corpus-wide
    query_identity.compute_similarity() pass, not written to
    refs_query_identity.tsv directly (report.write_refs_tsv only writes
    the keys named in its own headers list).

    `bad_reason` is None on a normal scan; otherwise a short
    human-readable string, with every other return value empty/zero.
    Set for an unreadable file (OSError), a cheap up-front quality check
    (bad_file_check.py) that skipped the expensive parse entirely, or an
    unexpected exception caught here so one bad file can't take down a
    whole tree scan. Not printed per-file to stderr -- recorded in
    bad_files.txt, with cli.py printing one aggregate count at the end."""
    known_names = known_names or set()
    hits, name_candidates, refs, relation_edges, function_calls = [], [], [], [], []
    try:
        text, enc = read_text(path)
    except OSError as e:
        reason = "cannot read: {}: {}".format(type(e).__name__, e)
        return hits, name_candidates, refs, relation_edges, 0, function_calls, [], reason

    # Cheap pre-check: lex once up front (parse_file lexes again
    # internally for the tiered driver -- lexing is a fast single linear
    # pass, so the small duplicate cost is worth keeping this check simple
    # and decoupled). Catches the common case (heavy non-SQL noise) before
    # spending any time in the expensive tiered driver at all.
    precheck_tokens, precheck_lexer_errors = lex_file(text)
    bad_reason = check_file_quality(precheck_tokens, precheck_lexer_errors)
    if bad_reason is not None:
        return hits, name_candidates, refs, relation_edges, 0, function_calls, [], bad_reason

    try:
        return _scan_file_body(path, text, enc, columns, stopwords, known_names,
                               max_iterations_per_chunk, extract_table_refs, extract_column_refs,
                               extract_relations, split_select, extract_functions,
                               extract_query_identity)
    except Exception as e:
        reason = "crashed while scanning: {}: {}".format(type(e).__name__, e)
        return [], [], [], [], 0, [], [], reason


def _scan_file_body(path, text, enc, columns, stopwords, known_names, max_iterations_per_chunk,
                    extract_table_refs, extract_column_refs, extract_relations, split_select,
                    extract_functions=False, extract_query_identity=False):
    """Runs the actual scan; split out from scan_file() so its try/except
    wraps one simple call. Everything below assumes well-formed input --
    it isn't itself defensive."""
    hits, name_candidates, refs, relation_edges, function_calls = [], [], [], [], []
    # One (query_blocks, predicate_visitor, line) tuple per chunk, appended
    # inside pre_chunk_hook -- can only be turned into final core_id rows
    # *after* parse_file() returns for the whole file, since a chunk's
    # predicate_visitor keeps accumulating across however many times the
    # tiered driver calls .visit() on that chunk's own committed fragments
    # (see query_identity.py's module docstring).
    query_identity_chunks = []
    lines = text.splitlines()
    seen_hit_lines = set()

    def make_hit(column, operator, value, line, in_comment, start_offset=None, end_offset=None):
        if _is_blank_literal(value):
            return
        hits.append({
            "severity": "FINDING",
            "file": path,
            "line": line,
            "column_name": column.upper(),
            "operator": operator.strip().upper(),
            "value": value,
            "snippet": _snippet_of(lines, line),
            "encoding": enc,
            "in_comment": in_comment,
            "start_offset": start_offset,
            "end_offset": end_offset,
        })
        seen_hit_lines.add(line)

    visitor = ExtractorVisitor(
        columns,
        lambda col, op, val, line, so, eo: make_hit(col, op, val, line, "N", so, eo))
    fallback = make_token_scan_fallback(
        columns,
        lambda col, op, val, line, so, eo: make_hit(col, op, val, line, "N", so, eo))

    need_blocks = extract_table_refs or extract_column_refs or extract_relations or extract_query_identity

    def pre_chunk_hook(all_tokens, start, end):
        extra_visitors = []
        if extract_functions:
            def fn_sink(name, params, line):
                function_calls.append({"function": name, "parameters": params,
                                       "file": path, "line": line})
            extra_visitors.append(FunctionVisitor(text, fn_sink))
        if not need_blocks:
            return tuple(extra_visitors)
        blocks = table_scan.scan_query_blocks(all_tokens[start:end])
        if extract_query_identity:
            predicate_visitor = query_identity.new_predicate_visitor(blocks)
            extra_visitors.append(predicate_visitor)
            chunk_line = next(
                (t.line for t in all_tokens[start:end] if t.channel == Token.DEFAULT_CHANNEL), None)
            query_identity_chunks.append((blocks, predicate_visitor, chunk_line))
        if extract_table_refs or extract_relations:
            for tref in table_scan.iter_table_refs(blocks):
                if extract_table_refs:
                    refs.append({"kind": "table", "schema": tref.schema, "table": tref.table,
                                "file": path, "line": tref.line})
        if extract_relations:
            # Structural edges cover every join type except COMMA (which
            # carries no predicate); comma-joins get their predicate
            # exclusively from the WHERE-implicit visitor below, so
            # excluding them here avoids double-counting. A comma-joined
            # pair with no WHERE condition linking it goes unrecorded --
            # a known limitation, not a bug. A CTE-participating edge
            # (either side is_cte) is also excluded here -- table_scan.py
            # now preserves those (needed for query_identity.py's join-type
            # signal), but refs_relations.tsv's own shipped output
            # deliberately continues to only ever show real table-to-table
            # pairs, unchanged from before that fix.
            structural_edges = [e for e in table_scan.scan_join_edges(blocks)
                               if e.join_type != "COMMA" and not e.left.is_cte and not e.right.is_cte]
            relation_edges.extend(relations.structural_edges_to_dicts(path, structural_edges))
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

            def join_sink(lschema, ltable, rschema, rtable, join_type, predicate, line):
                pair = tuple(sorted(((lschema, ltable), (rschema, rtable))))
                if pair in structural_pairs:
                    return
                relation_edges.append({
                    "file": path, "line": line,
                    "table_a_schema": lschema, "table_a": ltable,
                    "table_b_schema": rschema, "table_b": rtable,
                    "join_type": join_type, "predicate": predicate,
                })
            extra_visitors.append(relations.make_join_predicate_visitor(blocks, join_sink))
        if extract_column_refs:
            def col_sink(schema, table, column, line):
                refs.append({"kind": "column", "schema": schema, "table": table,
                            "column": column, "file": path, "line": line})
            extra_visitors.append(ReferenceVisitor(blocks, col_sink))
        return tuple(extra_visitors)

    all_tokens, _lexer_errors = parse_file(
        text, visitor, fallback, max_iterations_per_chunk=max_iterations_per_chunk,
        pre_chunk_hook=pre_chunk_hook)

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
    query_identity_rows = []
    for blocks, predicate_visitor, line in query_identity_chunks:
        row = query_identity.build_identity_row(blocks, predicate_visitor.facts, path, line)
        if row["table_count"] or row["join_count"] or row["predicate_count"]:
            query_identity_rows.append(row)

    rescan_comments(
        all_tokens, columns,
        lambda col, op, val, line, ic, so, eo: make_hit(col, op, val, line, ic, so, eo),
        max_iterations_per_chunk=max_iterations_per_chunk)

    offsets = _line_offsets(text)
    comment_spans = sorted(
        (t.start, t.stop) for t in comment_tokens(all_tokens) if t.start is not None)
    comment_starts = [s for s, _ in comment_spans]

    def in_comment(pos):
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
            name_candidates.append(word)

    hits.sort(key=lambda f: f["line"])

    select_block_count = 0
    if split_select:
        ranges = chunk_ranges(all_tokens)
        blocks = select_blocks.select_block_ranges(all_tokens, ranges)
        select_block_count = len(blocks)
        select_blocks.write_split_files(path, text, all_tokens, blocks)

    return (hits, name_candidates, refs, relation_edges, select_block_count, function_calls,
            query_identity_rows, None)


def _matching_files(root, suffixes, exclude_paths):
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.lower().endswith(suffixes):
                continue
            # A --split-select output file (e.g. report-01.sql) is scan
            # output, not fresh input -- skip it, or a later scan of the
            # same tree double-counts every split block under its own
            # filename alongside the untouched original.
            if select_blocks.looks_like_split_output(name):
                continue
            full = os.path.join(dirpath, name)
            if os.path.abspath(full) in exclude_paths:
                continue
            yield full


def scan_tree(root, columns, stopwords, known_names=None,
              extensions=DEFAULT_EXTENSIONS, exclude_paths=None,
              max_iterations_per_chunk=MAX_ITERATIONS_PER_CHUNK,
              verbose=False, workers=1,
              extract_table_refs=False, extract_column_refs=False,
              extract_relations=False, split_select=False, extract_functions=False,
              extract_query_identity=False):
    """Recursively scans files under root whose extension is in
    `extensions` (case-insensitive, without the dot).

    `exclude_paths` is an optional set of absolute paths to skip -- keeps
    the scanner's own output files from being scanned if they happen to
    live inside the scanned tree.

    `verbose` prints a "[i/N] path" progress line to stderr as each file
    finishes.

    `workers` > 1 scans files in separate processes
    (concurrent.futures.ProcessPoolExecutor -- parsing is CPU-bound pure
    Python, so this is real parallelism, not threads). Each file is
    scanned independently with no shared state, so only the merge order
    into `hits`/`name_candidates` depends on completion order; report
    writers already group/sort findings by file and line regardless. This
    holds for `query_identity_rows` too -- each row's own `core_id` is a
    pure hash of that one statement's own facts, so it comes back correct
    from any worker in any order; only query_identity.compute_similarity's
    corpus-wide pass (see cli.py) needs every row gathered back here
    first, so it deliberately isn't run per-worker.

    `extract_table_refs`/`extract_column_refs`/`extract_relations`/
    `split_select`/`extract_functions`/`extract_query_identity` are
    threaded straight through to scan_file() (see there for the shape of
    each corresponding return value).

    Returns (hits, name_candidates, refs, relation_edges,
    select_block_counts, function_calls, bad_files, query_identity_rows,
    file_count) -- select_block_counts is a {file: count} dict, bad_files
    is a {file: reason} dict."""
    suffixes = tuple("." + ext.lower().lstrip(".") for ext in extensions)
    exclude_paths = exclude_paths or set()
    hits, name_candidates, refs, relation_edges, function_calls = [], [], [], [], []
    query_identity_rows = []
    select_block_counts = {}
    bad_files = {}

    files = list(_matching_files(root, suffixes, exclude_paths))
    total = len(files)

    if workers <= 1:
        for i, full in enumerate(files, 1):
            h, nc, r, rel, sbc, fc, qi, bad = scan_file(full, columns, stopwords, known_names,
                                                     max_iterations_per_chunk=max_iterations_per_chunk,
                                                     extract_table_refs=extract_table_refs,
                                                     extract_column_refs=extract_column_refs,
                                                     extract_relations=extract_relations,
                                                     split_select=split_select,
                                                     extract_functions=extract_functions,
                                                     extract_query_identity=extract_query_identity)
            hits.extend(h)
            name_candidates.extend(nc)
            refs.extend(r)
            relation_edges.extend(rel)
            function_calls.extend(fc)
            query_identity_rows.extend(qi)
            if split_select:
                select_block_counts[full] = sbc
            if bad is not None:
                bad_files[full] = bad
            if verbose:
                print("[{}/{}] Scanned: {}".format(i, total, full), file=sys.stderr)
        return (hits, name_candidates, refs, relation_edges, select_block_counts, function_calls,
                bad_files, query_identity_rows, total)

    import concurrent.futures

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(scan_file, full, columns, stopwords, known_names,
                       max_iterations_per_chunk=max_iterations_per_chunk,
                       extract_table_refs=extract_table_refs,
                       extract_column_refs=extract_column_refs,
                       extract_relations=extract_relations,
                       split_select=split_select,
                       extract_functions=extract_functions,
                       extract_query_identity=extract_query_identity): full
            for full in files
        }
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            full = futures[fut]
            h, nc, r, rel, sbc, fc, qi, bad = fut.result()
            hits.extend(h)
            name_candidates.extend(nc)
            refs.extend(r)
            relation_edges.extend(rel)
            function_calls.extend(fc)
            query_identity_rows.extend(qi)
            if split_select:
                select_block_counts[full] = sbc
            if bad is not None:
                bad_files[full] = bad
            done += 1
            if verbose:
                print("[{}/{}] Scanned: {}".format(done, total, full), file=sys.stderr)
    return (hits, name_candidates, refs, relation_edges, select_block_counts, function_calls,
            bad_files, query_identity_rows, total)
