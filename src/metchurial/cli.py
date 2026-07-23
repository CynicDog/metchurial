# -*- coding: utf-8 -*-
"""Argparse CLI entry point: parses flags, drives scan_tree() over the
given root, and writes every output artifact (summary.md, findings.tsv,
strings.txt, stopwords.txt, known_names.txt, bad_files.tsv, the
--extract-metadata refs_*.tsv files, the --split-selects
split_manifest.tsv, the --incremental incremental_cache.json, and the
--quarantine quarantine_manifest.tsv) into the current working directory.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys

from metchurial.references import query_identity as query_identity_module
from metchurial.references import relations as relations_module
from metchurial.io_utils import (ensure_known_names_template, ensure_stopwords_template, load_bad_files,
                          load_known_names, load_stopwords, write_bad_files)
from metchurial.report import write_markdown_report, write_tsv_report, write_strings_file
from metchurial.tsv import write_refs_tsv
from metchurial.engine import scan_tree
from metchurial import incremental as incremental_module
from metchurial import quarantine as quarantine_module
from metchurial.models.options import (DEFAULT_EXTENSIONS, DEFAULT_MAX_CHUNK_ITERATIONS,
                                       DEFAULT_SENSITIVE_COLUMNS, ScanOptions)

# Plain 7-bit ASCII only (backslash/slash/underscore/equals/quote/hyphen/
# space) -- deliberately no Unicode box-drawing or em-dashes here, so this
# prints correctly on a default-codepage Windows console (cp437/cp1252),
# not just a UTF-8 one.
BANNER = r""" __    __     ______     ______      ______     __  __     __  __     ______     __     ______     __
/\ "-./  \   /\  ___\   /\__  _\    /\  ___\   /\ \_\ \   /\ \/\ \   /\  == \   /\ \   /\  __ \   /\ \
\ \ \-./\ \  \ \  __\   \/_/\ \/    \ \ \____  \ \  __ \  \ \ \_\ \  \ \  __<   \ \ \  \ \  __ \  \ \ \____
 \ \_\ \ \_\  \ \_____\    \ \_\     \ \_____\  \ \_\ \_\  \ \_____\  \ \_\ \_\  \ \_\  \ \_\ \_\  \ \_____\
  \/_/  \/_/   \/_____/     \/_/      \/_____/   \/_/\/_/   \/_____/   \/_/ /_/   \/_/   \/_/\/_/   \/_____/
"""

# Reserved output filenames -- not configurable, so a scan always produces
# the same, predictable set of artifacts (see README's Output Artifacts
# section) instead of needing a flag to find out what got written where.
SUMMARY_PATH = "summary.md"
FINDINGS_PATH = "findings.tsv"
STRINGS_PATH = "strings.txt"
STOPWORDS_PATH = "stopwords.txt"
KNOWN_NAMES_PATH = "known_names.txt"
BAD_FILES_PATH = "bad_files.tsv"
REFS_TABLES_PATH = "refs_tables.tsv"
REFS_COLUMNS_PATH = "refs_columns.tsv"
FUNCTIONS_PATH = "refs_functions.tsv"
RELATIONS_PATH = "refs_relations.tsv"
QUERY_IDENTITY_PATH = "refs_query_identity.tsv"
QUERY_SIMILARITY_PATH = "refs_query_similarity.tsv"
SPLIT_MANIFEST_PATH = "split_manifest.tsv"
INCREMENTAL_CACHE_PATH = "incremental_cache.json"
QUARANTINE_DIR = "quarantine"
QUARANTINE_MANIFEST_PATH = "quarantine_manifest.tsv"


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass

    print(BANNER)

    ap = argparse.ArgumentParser(
        description="Parse DB2 SQL into structured metadata (table/column/function/"
                    "predicate references, JOIN relationships) and detect hardcoded "
                    "sensitive values (IDs, policy numbers, Korean names), in .sql "
                    "(and, by default, .txt) files.")
    ap.add_argument("root", help="Root directory to scan recursively")
    ap.add_argument("--sensitive-columns", nargs="+", default=list(DEFAULT_SENSITIVE_COLUMNS),
                    help="Sensitive column names (default: %(default)s)")
    ap.add_argument("--extensions", nargs="+", default=list(DEFAULT_EXTENSIONS),
                    help="File extensions to scan, without the dot (default: %(default)s)")
    ap.add_argument("--verbose", action="store_true",
                    help="Also print a one-line ANTLR processing summary to stderr after "
                        "each file's [i/N] progress line: chunk count, tiered-loop "
                        "iterations (broken down into direct structural/token-scan hits, "
                        "Tier 2 resyncs, and Tier 3 single-token skips -- see "
                        "parsing/statement_driver.py), and elapsed time -- a summary, not "
                        "a full profile, meant to show at a glance which file(s) in a "
                        "large tree are the slow ones and roughly why. The [i/N] progress "
                        "line itself is always printed regardless of this flag "
                        "(default: off)")
    ap.add_argument("--workers", type=int, default=1, metavar="N",
                    help="Scan files in N worker processes instead of one "
                        "(default: %(default)s, i.e. serial). Parsing is "
                        "CPU-bound, so this is real parallelism, not threads; "
                        "each file is independent so results are unaffected "
                        "other than being merged in completion order.")
    ap.add_argument("--max-chunk-iterations", type=int, default=DEFAULT_MAX_CHUNK_ITERATIONS,
                    metavar="N",
                    help="Per-statement-chunk runtime cap on the ANTLR resync driver's "
                        "loop iterations -- bounds the time spent on an enormous chunk "
                        "the grammar can't make sense of, whose retry-per-token cost "
                        "would otherwise grow quadratically with chunk size "
                        "(default: %(default)s). Does not affect the token-adjacency "
                        "fallback (bare '(' / double-quoted literals) -- see README's "
                        "Known Limitations.")
    ap.add_argument("--extract-metadata", action="store_true",
                    help="Emit refs_tables.tsv/refs_columns.tsv (every schema.table and "
                        "schema.table.column reference found), refs_relations.tsv (every "
                        "table-to-table JOIN edge found, one row per occurrence with join "
                        "type/predicate/file/line -- comma-joins and explicit JOIN...ON/USING "
                        "alike), "
                        "refs_functions.tsv (every function call and predicate operator found), "
                        "and refs_query_identity.tsv (a core_id per statement -- structurally "
                        "identical statements share one id regardless of column aliasing/"
                        "projection/derived-column-calculation differences), "
                        "plus matching sections in summary.md (default: off; see README's "
                        "Known Limitations for the JOIN/CTE-related resolution gaps)")
    ap.add_argument("--query-similarity", action="store_true",
                    help="Also emit refs_query_similarity.tsv: a pairwise Jaccard similarity "
                        "score between statements that don't share a core_id. Opt-in because "
                        "the pass is O(n^2) in the number of distinct core_ids -- fine for "
                        "thousands of distinct queries, slow for tens of thousands. Requires "
                        "--extract-metadata (default: off)")
    ap.add_argument("--split-selects", action="store_true",
                    help="Count standalone SELECT blocks per file (## Select Blocks "
                        "section in summary.md) and, when a file has 2+ blocks, write "
                        "one <stem>-NN<ext> file per block alongside the original, then "
                        "delete the original (a file with a single SELECT block is left "
                        "as-is -- there's nothing to split apart). split_manifest.tsv "
                        "records, one row per split file, which original each came from. "
                        "CTE bodies are never miscounted as their own block. Only safe "
                        "to run against a tree you already have a separate copy of "
                        "(default: off)")
    ap.add_argument("--mask-literals", action="store_true",
                    help="Rewrite in place each file with a finding: "
                        "every flagged literal's content is replaced with a fixed "
                        "placeholder ('****' for a quoted literal, preserving its "
                        "own quote character; '0000' for an unquoted numeric "
                        "literal), everything else byte-for-byte identical. A file "
                        "with no findings is left untouched (default: off)")
    ap.add_argument("--quarantine", action="store_true",
                    help="Before scanning, recursively move every file under root whose "
                        "extension isn't in --extensions into ./quarantine (created if "
                        "needed), mirroring each file's path relative to root -- "
                        "'sub/notes.docx' lands at 'quarantine/sub/notes.docx' -- so the "
                        "folder it was found in stays visible. quarantine_manifest.tsv "
                        "records one row per file moved (original path -> quarantine "
                        "path). The scan itself only ever looked at --extensions files "
                        "anyway, so this doesn't change what gets scanned -- it just "
                        "clears everything else out of the tree first (default: off)")
    ap.add_argument("--incremental", action="store_true",
                    help="Skip re-scanning a file whose size+mtime and requested "
                        "--extract-metadata/--split-selects flags both match its "
                        "entry in incremental_cache.json from a previous run -- its "
                        "cached results are merged into this run's reports exactly "
                        "as if it had been freshly scanned, so refs_*.tsv/summary.md/"
                        "split_manifest.tsv stay complete across incremental runs on "
                        "a large tree instead of shrinking to just the files touched "
                        "this run. A file with no cache entry, a changed fingerprint, "
                        "or a cache entry recorded under a different flag combination "
                        "is always scanned fresh (default: off)")
    args = ap.parse_args(argv)

    if args.query_similarity and not args.extract_metadata:
        ap.error("--query-similarity requires --extract-metadata "
                 "(it scores the core_ids metadata extraction discovers)")

    if not os.path.isdir(args.root):
        print("ERROR: not a directory: {}".format(args.root), file=sys.stderr)
        sys.exit(2)

    # Files already marked bad on a previous run are skipped entirely this
    # run (not even attempted) -- delete a row from bad_files.tsv (after
    # fixing that file) to have it re-scanned on the next run.
    previously_bad = load_bad_files(BAD_FILES_PATH)

    # stopwords.txt/known_names.txt are created empty (with a format-
    # explaining header) on first run rather than requiring one to exist
    # already -- a fresh checkout just runs with neither populated until
    # the user triages strings.txt into them.
    stopwords_freshly_created = not os.path.isfile(STOPWORDS_PATH)
    ensure_stopwords_template(STOPWORDS_PATH)
    stopwords = load_stopwords(STOPWORDS_PATH)

    known_names_freshly_created = not os.path.isfile(KNOWN_NAMES_PATH)
    ensure_known_names_template(KNOWN_NAMES_PATH)
    known_names = load_known_names(KNOWN_NAMES_PATH)

    # Don't let the scanner re-scan its own output files if they happen to
    # live inside the scanned tree (relevant now that .txt is scanned by
    # default, since strings.txt/stopwords.txt/known_names.txt are also
    # .txt files).
    exclude_paths = {os.path.abspath(p) for p in
                     (SUMMARY_PATH, FINDINGS_PATH, STRINGS_PATH, STOPWORDS_PATH, KNOWN_NAMES_PATH,
                      BAD_FILES_PATH,
                      REFS_TABLES_PATH if args.extract_metadata else None,
                      REFS_COLUMNS_PATH if args.extract_metadata else None,
                      FUNCTIONS_PATH if args.extract_metadata else None,
                      RELATIONS_PATH if args.extract_metadata else None,
                      QUERY_IDENTITY_PATH if args.extract_metadata else None,
                      QUERY_SIMILARITY_PATH if args.query_similarity else None,
                      SPLIT_MANIFEST_PATH if args.split_selects else None,
                      QUARANTINE_MANIFEST_PATH if args.quarantine else None) if p}
    exclude_paths |= set(previously_bad)

    # Runs before the scan itself: once this returns, everything left
    # under args.root matches --extensions, so scan_tree sees exactly the
    # same tree it would have anyway -- --quarantine changes what's left
    # lying around afterward, not what gets scanned.
    quarantine_rows = (quarantine_module.quarantine_non_matching(
        args.root, tuple(args.extensions), QUARANTINE_DIR, exclude_paths=exclude_paths)
        if args.quarantine else [])

    common = dict(
        sensitive_columns=tuple(args.sensitive_columns), stopwords=stopwords,
        known_names=known_names, extensions=tuple(args.extensions),
        split_selects=args.split_selects, workers=args.workers,
        max_chunk_iterations=args.max_chunk_iterations)
    options = (ScanOptions.metadata(**common) if args.extract_metadata
               else ScanOptions(**common))

    def print_progress(i: int, total: int, path: str, result: object) -> None:
        print("[{}/{}] Scanned: {}".format(i, total, path), file=sys.stderr)
        if not args.verbose:
            return
        if result.bad_reason is not None:
            print("        antlr: skipped -- [{}] {}".format(
                result.bad_reason.category, result.bad_reason.message), file=sys.stderr)
        elif result.parse_stats is None:
            print("        antlr: reused from cache (--incremental)", file=sys.stderr)
        else:
            s = result.parse_stats
            print("        antlr: {} chunk(s), {} iteration(s) "
                 "(struct={} scan={} resync={} skip={}), {:.3f}s".format(
                     s.chunks, s.iterations, s.tier1_structural, s.tier1_token_scan,
                     s.tier2_resync, s.tier3_skip, s.elapsed_seconds), file=sys.stderr)

    # --incremental: reuse a previous run's cached FileScanResult for any
    # file whose (size, mtime_ns) and extract_*/split_selects mode both
    # still match -- see incremental.py's module docstring for why those
    # are the only two things checked. cached_results primes scan_tree
    # with what's reusable; on_file_result captures every file's result
    # (cached or freshly scanned) back into `incremental_cache`, which
    # gets written out once the scan finishes so the next run benefits.
    incremental_cache: dict[str, dict] = {}
    cached_results: dict[str, object] = {}
    mode = incremental_module.mode_signature(options)
    if args.incremental:
        incremental_cache = incremental_module.load_cache(INCREMENTAL_CACHE_PATH)
        for abspath in list(incremental_cache):
            cached = incremental_module.lookup(incremental_cache, abspath, mode)
            if cached is not None:
                cached_results[abspath] = cached
        exclude_paths.add(os.path.abspath(INCREMENTAL_CACHE_PATH))

    def on_file_result(path: str, result: object) -> None:
        incremental_module.record(incremental_cache, os.path.abspath(path), mode, result)

    tree = scan_tree(args.root, options, exclude_paths=exclude_paths,
                     progress=print_progress,
                     cached_results=cached_results if args.incremental else None,
                     on_file_result=on_file_result if args.incremental else None)

    if args.incremental:
        incremental_module.save_cache(INCREMENTAL_CACHE_PATH, incremental_cache)

    # Preserve skipped (still-unfixed) entries from previous runs, and add
    # anything newly flagged this run -- a file the user removed from
    # bad_files.tsv and that scanned clean this time simply doesn't appear
    # in either set, so it naturally drops off the list.
    all_bad = dict(previously_bad)
    all_bad.update(tree.bad_files)
    write_bad_files(BAD_FILES_PATH, all_bad)

    relations_summary = (relations_module.aggregate_edges(tree.relation_edges)
                         if args.extract_metadata else None)
    # Corpus-wide, single post-aggregation pass (not per-file/per-worker):
    # needs every core_id discovered across the whole scan to be
    # meaningful (see query_identity.py's module docstring). Opt-in via
    # --query-similarity: O(n^2) in distinct core_ids.
    query_similarity_rows = (query_identity_module.compute_similarity(tree.identity_rows)
                             if args.query_similarity else None)

    invocation = "metchurial " + " ".join(
        shlex.quote(a) for a in (argv if argv is not None else sys.argv[1:]))
    run_info = {
        "invocation": invocation, "root": args.root, "file_count": tree.file_count,
        "sensitive_columns": args.sensitive_columns, "extensions": args.extensions,
        "workers": args.workers, "max_chunk_iterations": args.max_chunk_iterations,
        "extract_metadata": args.extract_metadata, "query_similarity": args.query_similarity,
        "split_selects": args.split_selects,
        "mask_literals": args.mask_literals, "incremental": args.incremental,
        "quarantine": args.quarantine,
        "verbose": args.verbose,
    }
    write_markdown_report(
        SUMMARY_PATH, run_info, tree,
        previously_bad=previously_bad,
        stopwords_count=len(stopwords), stopwords_freshly_created=stopwords_freshly_created,
        known_names_count=len(known_names), known_names_freshly_created=known_names_freshly_created,
        relations_summary=relations_summary,
        query_similarity_rows=query_similarity_rows,
        extract_metadata=args.extract_metadata, split_selects=args.split_selects)

    all_findings = tree.findings
    write_tsv_report(FINDINGS_PATH, all_findings)
    write_strings_file(STRINGS_PATH, tree.name_candidates)

    masked_written = []
    if args.mask_literals:
        from metchurial.mask import write_masked_files
        masked_written = write_masked_files(
            all_findings, warn=lambda msg: print(msg, file=sys.stderr))

    if args.extract_metadata:
        table_rows = sorted(tree.table_uses, key=lambda r: (r.schema, r.table, r.file, r.line))
        column_rows = sorted(tree.column_uses,
                             key=lambda r: (r.schema, r.table, r.column, r.file, r.line))
        write_refs_tsv(REFS_TABLES_PATH, ["schema", "table", "file", "line"], table_rows)
        write_refs_tsv(REFS_COLUMNS_PATH, ["schema", "table", "column", "file", "line"], column_rows)

        function_rows = sorted(tree.function_calls, key=lambda r: (r.function, r.file, r.line))
        write_refs_tsv(FUNCTIONS_PATH, ["function", "parameters", "file", "line"], function_rows)

        relation_rows = sorted(tree.relation_edges, key=lambda r: (r.file, r.line))
        relations_module.write_relations_tsv(RELATIONS_PATH, relation_rows)

        identity_rows = sorted(tree.identity_rows, key=lambda r: (r.core_id, r.file, r.line or 0))
        write_refs_tsv(QUERY_IDENTITY_PATH,
                      ["core_id", "file", "line", "table_count", "join_count",
                       "has_cte", "has_subquery", "has_union",
                       "columns", "tables", "join_types", "relations"],
                      identity_rows)
        if args.query_similarity:
            query_identity_module.write_similarity_tsv(QUERY_SIMILARITY_PATH, query_similarity_rows)

    if args.split_selects:
        split_rows = sorted(tree.split_manifest, key=lambda r: (r.original_file, r.block_number))
        write_refs_tsv(SPLIT_MANIFEST_PATH,
                      ["original_file", "split_file", "block_number", "total_blocks"],
                      split_rows)

    if args.quarantine:
        write_refs_tsv(QUARANTINE_MANIFEST_PATH,
                      ["original_file", "quarantined_file"], quarantine_rows)

    if args.quarantine:
        print("Quarantine     : {} non-matching file(s) moved to {} -- see {}".format(
            len(quarantine_rows), os.path.abspath(QUARANTINE_DIR),
            os.path.abspath(QUARANTINE_MANIFEST_PATH)))
    print("Scanned {} file(s) (.{}). Findings: {}".format(
        tree.file_count, ", .".join(args.extensions), len(tree.findings)))
    print("Summary        : {}".format(os.path.abspath(SUMMARY_PATH)))
    print("Findings       : {}".format(os.path.abspath(FINDINGS_PATH)))
    print("Strings        : {}".format(os.path.abspath(STRINGS_PATH)))
    if tree.name_candidates:
        print("Names to review: {} unique unclassified name-like literal(s) in {} -- "
             "copy a real name into known_names.txt (flagged as a finding next run), or a "
             "non-name into stopwords.txt (won't show up again).".format(
                 len(set(tree.name_candidates)), os.path.abspath(STRINGS_PATH)))
    if args.extract_metadata:
        print("Table refs     : {}".format(os.path.abspath(REFS_TABLES_PATH)))
        print("Column refs    : {}".format(os.path.abspath(REFS_COLUMNS_PATH)))
        print("Functions      : {}".format(os.path.abspath(FUNCTIONS_PATH)))
        print("Relations      : {}".format(os.path.abspath(RELATIONS_PATH)))
        print("Query identity : {} ({} statement(s), {} distinct core_id(s))".format(
            os.path.abspath(QUERY_IDENTITY_PATH), len(tree.identity_rows),
            len({r.core_id for r in tree.identity_rows})))
    if args.query_similarity:
        print("Query similarity: {}".format(os.path.abspath(QUERY_SIMILARITY_PATH)))
    if args.split_selects:
        split_files_written = sum(1 for c in tree.select_block_counts.values() if c > 1)
        print("Select blocks  : {} standalone SELECT block(s) across {} file(s), "
             "{} file(s) split and deleted -- see {}".format(
                 sum(tree.select_block_counts.values()),
                 sum(1 for c in tree.select_block_counts.values() if c > 0),
                 split_files_written, os.path.abspath(SPLIT_MANIFEST_PATH)))
    if args.mask_literals:
        print("Masked files   : {} file(s) rewritten in place".format(
            len(masked_written)))
    if previously_bad or tree.bad_files:
        print("Bad files      : {} skipped (already in bad_files.tsv), {} newly flagged "
             "this run -- see {}".format(
                 len(previously_bad), len(tree.bad_files), os.path.abspath(BAD_FILES_PATH)))
    if args.incremental:
        print("Incremental    : {} file(s) reused from cache, {} scanned fresh -- see {}".format(
            len(cached_results), tree.file_count - len(cached_results),
            os.path.abspath(INCREMENTAL_CACHE_PATH)))

    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
