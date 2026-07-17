# -*- coding: utf-8 -*-
"""Argparse CLI entry point: parses flags, drives scan_tree() over the
given root, and writes every output artifact (summary.md, findings.tsv,
strings.txt, stopwords.txt, known_names.txt, bad_files.txt, and the
--extract-metadata refs_*.tsv files) into the current working directory.
"""

import argparse
import os
import shlex
import sys

from src.references import query_identity as query_identity_module
from src.references import relations as relations_module
from src.io_utils import (ensure_known_names_template, ensure_stopwords_template, load_bad_files,
                          load_known_names, load_stopwords, write_bad_files)
from src.report import write_markdown_report, write_tsv_report, write_strings_file, write_refs_tsv
from src.scan import DEFAULT_COLUMNS, DEFAULT_EXTENSIONS, scan_tree
from src.detect.statement_driver import MAX_ITERATIONS_PER_CHUNK

# Plain 7-bit ASCII only (backslash/slash/underscore/equals/quote/hyphen/
# space) -- deliberately no Unicode box-drawing or em-dashes here, so this
# prints correctly on a default-codepage Windows console (cp437/cp1252),
# not just a UTF-8 one.
BANNER = r""" __    __     ______     ______      ______     __  __     __  __     ______     __     ______     __
/\ "-./  \   /\  ___\   /\__  _\    /\  ___\   /\ \_\ \   /\ \/\ \   /\  == \   /\ \   /\  __ \   /\ \
\ \ \-./\ \  \ \  __\   \/_/\ \/    \ \ \____  \ \  __ \  \ \ \_\ \  \ \  __<   \ \ \  \ \  __ \  \ \ \____
 \ \_\ \ \_\  \ \_____\    \ \_\     \ \_____\  \ \_\ \_\  \ \_____\  \ \_\ \_\  \ \_\  \ \_\ \_\  \ \_____\
  \/_/  \/_/   \/_____/     \/_/      \/_____/   \/_/\/_/   \/_____/   \/_/ /_/   \/_/   \/_/\/_/   \/_____/
                                                                                            by @cynicdog
"""

# Reserved output filenames -- not configurable, so a scan always produces
# the same, predictable set of artifacts (see README's Output Artifacts
# section) instead of needing a flag to find out what got written where.
SUMMARY_PATH = "summary.md"
FINDINGS_PATH = "findings.tsv"
STRINGS_PATH = "strings.txt"
STOPWORDS_PATH = "stopwords.txt"
KNOWN_NAMES_PATH = "known_names.txt"
BAD_FILES_PATH = "bad_files.txt"
REFS_TABLES_PATH = "refs_tables.tsv"
REFS_COLUMNS_PATH = "refs_columns.tsv"
FUNCTIONS_PATH = "refs_functions.tsv"
RELATIONS_PATH = "refs_relations.tsv"
QUERY_IDENTITY_PATH = "refs_query_identity.tsv"
QUERY_SIMILARITY_PATH = "refs_query_similarity.tsv"


def main(argv=None):
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
    ap.add_argument("--sensitive-columns", nargs="+", default=DEFAULT_COLUMNS,
                    help="Sensitive column names (default: %(default)s)")
    ap.add_argument("--extensions", nargs="+", default=DEFAULT_EXTENSIONS,
                    help="File extensions to scan, without the dot (default: %(default)s)")
    ap.add_argument("--verbose", action="store_true",
                    help="Print a [i/N] progress line to stderr as each file is scanned")
    ap.add_argument("--workers", type=int, default=1, metavar="N",
                    help="Scan files in N worker processes instead of one "
                        "(default: %(default)s, i.e. serial). Parsing is "
                        "CPU-bound, so this is real parallelism, not threads; "
                        "each file is independent so results are unaffected "
                        "other than being merged in completion order.")
    ap.add_argument("--max-chunk-iterations", type=int, default=MAX_ITERATIONS_PER_CHUNK,
                    metavar="N",
                    help="Per-statement-chunk safety-valve cap on the ANTLR resync "
                        "driver's loop iterations, so a pathological chunk the grammar "
                        "can't make sense of can't spin indefinitely (default: %(default)s). "
                        "Does not affect the token-adjacency fallback (bare '(' / "
                        "double-quoted literals) -- see README's Known Limitations.")
    ap.add_argument("--extract-metadata", action="store_true",
                    help="Emit refs_tables.tsv/refs_columns.tsv (every schema.table and "
                        "schema.table.column reference found), refs_relations.tsv (table-to-table "
                        "JOIN usage -- comma-joins and explicit JOIN...ON/USING alike), "
                        "refs_functions.tsv (every function call and predicate operator found), "
                        "and refs_query_identity.tsv/refs_query_similarity.tsv (a core_id per "
                        "statement -- structurally identical statements share one id regardless "
                        "of column aliasing/projection/derived-column-calculation differences -- "
                        "plus a similarity score between statements that don't share one), "
                        "plus matching sections in summary.md (default: off; see README's "
                        "Known Limitations for the JOIN/CTE-related resolution gaps)")
    ap.add_argument("--split-selects", action="store_true",
                    help="Count standalone SELECT blocks per file (## Select Blocks "
                        "section in summary.md) and, when a file has 2+ blocks, write "
                        "one <stem>-NN<ext> file per block alongside the original (a "
                        "file with a single SELECT block is left as-is -- there's "
                        "nothing to split apart). CTE bodies are never miscounted as "
                        "their own block (default: off)")
    ap.add_argument("--mask-literals", action="store_true",
                    help="Rewrite in place each file with a finding: "
                        "every flagged literal's content is replaced with a fixed "
                        "placeholder ('****' for a quoted literal, preserving its "
                        "own quote character; '0000' for an unquoted numeric "
                        "literal), everything else byte-for-byte identical. A file "
                        "with no findings is left untouched (default: off)")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.root):
        print("ERROR: not a directory: {}".format(args.root), file=sys.stderr)
        sys.exit(2)

    # Files already marked bad on a previous run are skipped entirely this
    # run (not even attempted) -- delete a line from bad_files.txt (after
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
                      QUERY_SIMILARITY_PATH if args.extract_metadata else None) if p}
    exclude_paths |= set(previously_bad)

    (hits, name_candidates, refs, relation_edges, select_block_counts, function_calls,
     new_bad, query_identity_rows, file_count) = scan_tree(
        args.root, args.sensitive_columns, stopwords, known_names,
        extensions=args.extensions, exclude_paths=exclude_paths,
        max_iterations_per_chunk=args.max_chunk_iterations,
        verbose=args.verbose, workers=args.workers,
        extract_table_refs=args.extract_metadata, extract_column_refs=args.extract_metadata,
        extract_relations=args.extract_metadata, split_select=args.split_selects,
        extract_functions=args.extract_metadata, extract_query_identity=args.extract_metadata)

    # Preserve skipped (still-unfixed) entries from previous runs, and add
    # anything newly flagged this run -- a file the user removed from
    # bad_files.txt and that scanned clean this time simply doesn't appear
    # in either set, so it naturally drops off the list.
    all_bad = dict(previously_bad)
    all_bad.update(new_bad)
    write_bad_files(BAD_FILES_PATH, all_bad)

    relations_summary = (relations_module.aggregate_edges(relation_edges)
                         if args.extract_metadata else None)
    # Corpus-wide, single post-aggregation pass (not per-file/per-worker):
    # needs every core_id discovered across the whole scan to be
    # meaningful (see query_identity.py's module docstring).
    query_similarity_rows = (query_identity_module.compute_similarity(query_identity_rows)
                             if args.extract_metadata else None)

    invocation = "metchurial " + " ".join(
        shlex.quote(a) for a in (argv if argv is not None else sys.argv[1:]))
    run_info = {
        "invocation": invocation, "root": args.root, "file_count": file_count,
        "sensitive_columns": args.sensitive_columns, "extensions": args.extensions,
        "workers": args.workers, "max_chunk_iterations": args.max_chunk_iterations,
        "extract_metadata": args.extract_metadata, "split_selects": args.split_selects,
        "mask_literals": args.mask_literals, "verbose": args.verbose,
    }
    write_markdown_report(
        SUMMARY_PATH, run_info, hits, name_candidates, previously_bad, new_bad,
        len(stopwords), stopwords_freshly_created,
        len(known_names), known_names_freshly_created,
        refs=refs if args.extract_metadata else None,
        function_calls=function_calls if args.extract_metadata else None,
        relations_summary=relations_summary,
        select_block_counts=select_block_counts if args.split_selects else None,
        query_identity_rows=query_identity_rows if args.extract_metadata else None,
        query_similarity_rows=query_similarity_rows)

    all_findings = hits
    write_tsv_report(FINDINGS_PATH, all_findings)
    write_strings_file(STRINGS_PATH, name_candidates)

    masked_written = []
    if args.mask_literals:
        from src.mask import write_masked_files
        masked_written = write_masked_files(
            all_findings, warn=lambda msg: print(msg, file=sys.stderr))

    if args.extract_metadata:
        table_rows = sorted((r for r in refs if r["kind"] == "table"),
                            key=lambda r: (r["schema"], r["table"], r["file"], r["line"]))
        column_rows = sorted((r for r in refs if r["kind"] == "column"),
                             key=lambda r: (r["schema"], r["table"], r["column"], r["file"], r["line"]))
        write_refs_tsv(REFS_TABLES_PATH, ["schema", "table", "file", "line"], table_rows)
        write_refs_tsv(REFS_COLUMNS_PATH, ["schema", "table", "column", "file", "line"], column_rows)

        function_rows = sorted(function_calls,
                               key=lambda r: (r["function"], r["file"], r["line"]))
        write_refs_tsv(FUNCTIONS_PATH, ["function", "parameters", "file", "line"], function_rows)

        relations_module.write_relations_tsv(RELATIONS_PATH, relations_summary)

        identity_rows = sorted(query_identity_rows, key=lambda r: (r["core_id"], r["file"], r["line"]))
        write_refs_tsv(QUERY_IDENTITY_PATH,
                      ["core_id", "file", "line", "table_count", "join_count", "predicate_count"],
                      identity_rows)
        query_identity_module.write_similarity_tsv(QUERY_SIMILARITY_PATH, query_similarity_rows)

    print("Scanned {} file(s) (.{}). Findings: {}".format(
        file_count, ", .".join(args.extensions), len(hits)))
    print("Summary        : {}".format(os.path.abspath(SUMMARY_PATH)))
    print("Findings       : {}".format(os.path.abspath(FINDINGS_PATH)))
    print("Strings        : {}".format(os.path.abspath(STRINGS_PATH)))
    if name_candidates:
        print("Names to review: {} unique unclassified name-like literal(s) in {} -- "
             "copy a real name into known_names.txt (flagged as a finding next run), or a "
             "non-name into stopwords.txt (won't show up again).".format(
                 len(set(name_candidates)), os.path.abspath(STRINGS_PATH)))
    if args.extract_metadata:
        print("Table refs     : {}".format(os.path.abspath(REFS_TABLES_PATH)))
        print("Column refs    : {}".format(os.path.abspath(REFS_COLUMNS_PATH)))
        print("Functions      : {}".format(os.path.abspath(FUNCTIONS_PATH)))
        print("Relations      : {}".format(os.path.abspath(RELATIONS_PATH)))
        print("Query identity : {} ({} statement(s), {} distinct core_id(s))".format(
            os.path.abspath(QUERY_IDENTITY_PATH), len(query_identity_rows),
            len({r["core_id"] for r in query_identity_rows})))
        print("Query similarity: {}".format(os.path.abspath(QUERY_SIMILARITY_PATH)))
    if args.split_selects:
        print("Select blocks  : {} standalone SELECT block(s) across {} file(s), "
             "split files written alongside originals for files with 2+ blocks".format(
                 sum(select_block_counts.values()),
                 sum(1 for c in select_block_counts.values() if c > 0)))
    if args.mask_literals:
        print("Masked files   : {} file(s) rewritten in place".format(
            len(masked_written)))
    if previously_bad or new_bad:
        print("Bad files      : {} skipped (already in bad_files.txt), {} newly flagged "
             "this run -- see {}".format(
                 len(previously_bad), len(new_bad), os.path.abspath(BAD_FILES_PATH)))

    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
