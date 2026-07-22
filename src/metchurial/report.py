# -*- coding: utf-8 -*-
"""Writes every report artifact a scan produces (summary.md, findings.tsv,
strings.txt, refs_*.tsv) from the domain models (metchurial/models) engine.py
produces.

summary.md is an index into the other artifacts, not a duplicate of them:
every section beyond "Sensitive Findings" is a bounded count-plus-top-N view
with a pointer to the full artifact file (strings.txt, bad_files.txt,
stopwords.txt, known_names.txt, refs_*.tsv), so its size stays
fixed regardless of how large the scan is.
"""

from __future__ import annotations

import datetime
import os
from typing import Any, Callable, Iterable, Sequence, TextIO

from metchurial.models.findings import Finding
from metchurial.models.identity import IdentityRow, SimilarityPair
from metchurial.models.references import ColumnUse, FunctionCall, TableUse
from metchurial.models.relations import RelationRollup
from metchurial.models.results import TreeScanResult
from metchurial.tsv import _clean

# Cap on how many literals get joined into one Markdown "Value(s)" cell
# (e.g. a large IN(...) list) before switching to "...(+N more)" -- an
# unbounded join can produce a single cell thousands of characters wide,
# which most Markdown viewers wrap so badly it looks like a broken table.
MAX_GROUPED_VALUES = 10

# Per-file cap on rows in the "## Sensitive Findings" detail subsections --
# full, uncapped detail is always in findings.tsv.
DETAIL_CAP = 15


def md_escape(text: object) -> str:
    """Escape/normalize text for a Markdown table cell. A literal can
    legally contain an embedded newline (a quoted string spanning physical
    lines); left as-is that breaks the table row, so whitespace is
    collapsed to single spaces the same way the TSV writer does."""
    text = str(text).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return text.replace("|", "\\|").replace("`", "'")


def _format_grouped_values(values: Sequence[str]) -> str:
    """Join grouped literals for one Markdown cell, capped at
    MAX_GROUPED_VALUES so a large IN(...)/repeated-comparison list (which
    the .tsv already reports one-row-per-literal, uncapped) can't blow up
    a single cell to thousands of characters."""
    if len(values) > MAX_GROUPED_VALUES:
        shown = values[:MAX_GROUPED_VALUES]
        return "{}; ... (+{} more, see findings.tsv)".format(
            "; ".join(shown), len(values) - MAX_GROUPED_VALUES)
    return "; ".join(values)


def _group_for_detail(items: list[Finding]) -> list[dict[str, Any]]:
    """Collapse findings that share file/line/column/operator into one row
    with their values joined -- keeps an IN(...)/BETWEEN explosion (which
    the .tsv reports one-row-per-literal, by design) from also exploding
    the Markdown detail table row-for-row."""
    groups: dict[tuple[int, str, str], dict[str, Any]] = {}
    order = []
    for f in items:
        key = (f.line, f.column_name, f.operator)
        if key not in groups:
            groups[key] = {"values": [], "snippet": f.snippet}
            order.append(key)
        groups[key]["values"].append(f.value)
    rows = []
    for key in order:
        line, column, operator = key
        g = groups[key]
        rows.append({
            "line": line, "column_name": column, "operator": operator,
            "value": _format_grouped_values(g["values"]), "snippet": g["snippet"],
        })
    rows.sort(key=lambda r: r["line"])
    return rows


def _name_candidate_counts(name_candidates: list[str]) -> dict[str, int]:
    """{name-shaped literal: occurrence count} across all not-yet-classified
    candidates -- shared by write_strings_file and the "## String
    Occurrences" summary section so the two never drift apart."""
    counts = {}
    for word in name_candidates:
        counts[word] = counts.get(word, 0) + 1
    return counts


def _ranked_counts(items: Iterable[Any],
                   key: Callable[[Any], str]) -> list[tuple[str, int]]:
    """{key(item): count}, sorted by count desc then key asc -- shared
    ranking helper for the Table/Column References and Functions summary
    sections."""
    counts = {}
    for item in items:
        k = key(item)
        counts[k] = counts.get(k, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def _write_run_info(out: TextIO, run_info: dict[str, Any]) -> None:
    out.write("# Scan Summary\n\n")
    out.write("| Item | Value |\n|---|---|\n")
    out.write("| Run at | {} |\n".format(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    out.write("| Command | `{}` |\n".format(md_escape(run_info["invocation"])))
    out.write("| Scan root | `{}` |\n".format(os.path.abspath(run_info["root"])))
    out.write("| Files scanned | {} |\n".format(run_info["file_count"]))
    out.write("| Sensitive columns | {} |\n".format(
        ", ".join("`{}`".format(c.upper()) for c in run_info["sensitive_columns"])))
    out.write("| Extensions | {} |\n".format(
        ", ".join("`.{}`".format(e) for e in run_info["extensions"])))
    out.write("| Workers | {} |\n".format(run_info["workers"]))
    out.write("| Max chunk iterations | {} |\n".format(run_info["max_chunk_iterations"]))
    out.write("| Extract metadata | {} |\n".format("ON" if run_info["extract_metadata"] else "OFF"))
    out.write("| Query similarity | {} |\n".format("ON" if run_info["query_similarity"] else "OFF"))
    out.write("| Split selects | {} |\n".format("ON" if run_info["split_selects"] else "OFF"))
    out.write("| Mask literals | {} |\n".format("ON" if run_info["mask_literals"] else "OFF"))
    out.write("| Incremental | {} |\n".format("ON" if run_info["incremental"] else "OFF"))
    out.write("| Verbose | {} |\n\n".format("ON" if run_info["verbose"] else "OFF"))


def _write_sensitive_hits(out: TextIO, hits: list[Finding]) -> None:
    by_file: dict[str, list[Finding]] = {}
    for f in hits:
        by_file.setdefault(f.file, []).append(f)

    out.write("## Sensitive Findings\n\n")
    if not by_file:
        out.write("No hardcoded sensitive values detected. ✅\n\n")
        return

    out.write("| # | File | Findings |\n")
    out.write("|---:|---|---:|\n")
    for i, fpath in enumerate(sorted(by_file), start=1):
        out.write("| {} | `{}` | {} |\n".format(i, md_escape(fpath), len(by_file[fpath])))
    out.write("| | **Total** | **{}** |\n\n".format(len(hits)))

    out.write("_Rows sharing the same file/line/column/operator are "
              "collapsed into one row with values joined by `; `. Each file is "
              "capped at {} rows below; see findings.tsv for the full, uncapped "
              "list._\n".format(DETAIL_CAP))
    for fpath in sorted(by_file):
        all_items = by_file[fpath]
        grouped = _group_for_detail(all_items)
        out.write("\n### `{}` — {} finding(s), {} row(s) below\n\n".format(
            md_escape(fpath), len(all_items), min(len(grouped), DETAIL_CAP)))
        out.write("| Line | Column | Operator | Value(s) | Snippet |\n")
        out.write("|---:|---|---|---|---|\n")
        for row in grouped[:DETAIL_CAP]:
            out.write("| {} | {} | `{}` | `{}` | `{}` |\n".format(
                row["line"], row["column_name"],
                md_escape(row["operator"]), md_escape(row["value"]),
                md_escape(row["snippet"])))
        remaining = len(grouped) - DETAIL_CAP
        if remaining > 0:
            out.write("\n_...+{} more row(s) for this file, see findings.tsv._\n".format(remaining))
    out.write("\n")


def _write_string_occurrences(out: TextIO, name_candidates: list[str]) -> None:
    out.write("## String Occurrences\n\n")
    counts = _name_candidate_counts(name_candidates)
    if not counts:
        out.write("No unclassified name-like literals -- nothing left to triage.\n\n")
        return
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    out.write("{} unique name-like literal(s) not yet classified, {} occurrence(s) total. "
              "Full list in strings.txt -- copy a real name into known_names.txt to flag "
              "it as a finding on the next run, or a non-name into stopwords.txt to stop seeing "
              "it here.\n\n".format(len(counts), sum(counts.values())))
    out.write("| Literal | Occurrences |\n|---|---:|\n")
    for word, count in ranked[:MAX_GROUPED_VALUES]:
        out.write("| `{}` | {} |\n".format(md_escape(word), count))
    if len(ranked) > MAX_GROUPED_VALUES:
        out.write("\n_...+{} more, see strings.txt._\n".format(len(ranked) - MAX_GROUPED_VALUES))
    out.write("\n")


def _write_bad_files(out: TextIO, previously_bad: dict[str, str],
                     new_bad: dict[str, str]) -> None:
    out.write("## Bad Files\n\n")
    all_bad = dict(previously_bad)
    all_bad.update(new_bad)
    if not all_bad:
        out.write("No bad files skipped or flagged.\n\n")
        return
    out.write("{} skipped (already in bad_files.txt), {} newly flagged this run. "
              "Full list in bad_files.txt.\n\n".format(len(previously_bad), len(new_bad)))
    out.write("| File | Reason | Newly flagged |\n|---|---|---|\n")
    for fpath in sorted(all_bad)[:MAX_GROUPED_VALUES]:
        out.write("| `{}` | {} | {} |\n".format(
            md_escape(fpath), md_escape(all_bad[fpath]), "Y" if fpath in new_bad else "N"))
    if len(all_bad) > MAX_GROUPED_VALUES:
        out.write("\n_...+{} more, see bad_files.txt._\n".format(len(all_bad) - MAX_GROUPED_VALUES))
    out.write("\n")


def _write_stopwords(out: TextIO, stopwords_count: int, freshly_created: bool) -> None:
    out.write("## Stopwords\n\n")
    if freshly_created:
        out.write("stopwords.txt didn't exist yet -- created an empty template this run. "
                  "0 stopword(s) loaded.\n\n")
    else:
        out.write("{} stopword(s) loaded from stopwords.txt.\n\n".format(stopwords_count))


def _write_known_names(out: TextIO, known_names_count: int,
                       freshly_created: bool) -> None:
    out.write("## Known Names\n\n")
    if freshly_created:
        out.write("known_names.txt didn't exist yet -- created an empty template this run. "
                  "0 known name(s) loaded.\n\n")
    else:
        out.write("{} known name(s) loaded from known_names.txt.\n\n".format(known_names_count))


def _write_references(out: TextIO, table_uses: list[TableUse],
                      column_uses: list[ColumnUse]) -> None:
    out.write("## Table & Column References\n\n")
    if not table_uses and not column_uses:
        out.write("No table/column references detected.\n\n")
        return
    out.write("{} table reference(s), {} column reference(s). Full detail in "
              "refs_tables.tsv / refs_columns.tsv.\n\n".format(len(table_uses), len(column_uses)))
    ranked = _ranked_counts(list(table_uses) + list(column_uses),
                            key=lambda r: "{}.{}".format(r.schema, r.table))
    out.write("| Table | References |\n|---|---:|\n")
    for name, count in ranked[:MAX_GROUPED_VALUES]:
        out.write("| `{}` | {} |\n".format(md_escape(name), count))
    if len(ranked) > MAX_GROUPED_VALUES:
        out.write("\n_...+{} more table(s), see refs_tables.tsv._\n".format(
            len(ranked) - MAX_GROUPED_VALUES))
    out.write("\n")


def _write_functions(out: TextIO, function_calls: list[FunctionCall]) -> None:
    out.write("## Functions\n\n")
    if not function_calls:
        out.write("No function calls detected.\n\n")
        return
    ranked = _ranked_counts(function_calls, key=lambda r: r.function)
    out.write("{} function call(s) found. Full detail in refs_functions.tsv.\n\n".format(
        len(function_calls)))
    out.write("| Function | Calls |\n|---|---:|\n")
    for name, count in ranked[:MAX_GROUPED_VALUES]:
        out.write("| `{}` | {} |\n".format(md_escape(name), count))
    if len(ranked) > MAX_GROUPED_VALUES:
        out.write("\n_...+{} more, see refs_functions.tsv._\n".format(len(ranked) - MAX_GROUPED_VALUES))
    out.write("\n")


def _write_relations(out: TextIO, relations_summary: list[RelationRollup]) -> None:
    out.write("## Relations\n\n")
    if not relations_summary:
        out.write("No JOIN relationships detected.\n\n")
        return
    out.write("_Top table-to-table relationships across the whole scan, by join count; "
              "the per-occurrence detail (file/line/predicate for every individual join "
              "edge) is in refs_relations.tsv._\n\n")
    out.write("| Table A | Table B | Join Count | Predicates |\n")
    out.write("|---|---|---:|---|\n")
    for row in relations_summary[:MAX_GROUPED_VALUES]:
        a = "{}.{}".format(row.table_a_schema, row.table_a)
        b = "{}.{}".format(row.table_b_schema, row.table_b)
        preds = _format_grouped_values(row.predicates) if row.predicates else ""
        out.write("| `{}` | `{}` | {} | `{}` |\n".format(
            md_escape(a), md_escape(b), row.join_count, md_escape(preds)))
    if len(relations_summary) > MAX_GROUPED_VALUES:
        out.write("\n_...+{} more table-pair(s) by count; see refs_relations.tsv for the "
                  "full per-occurrence list._\n".format(
            len(relations_summary) - MAX_GROUPED_VALUES))
    out.write("\n")


def _write_query_identity(out: TextIO, query_identity_rows: list[IdentityRow],
                          query_similarity_rows: list[SimilarityPair] | None) -> None:
    out.write("## Query Identity\n\n")
    if not query_identity_rows:
        out.write("No statements identified.\n\n")
        return
    clusters: dict[str, list[IdentityRow]] = {}
    for row in query_identity_rows:
        clusters.setdefault(row.core_id, []).append(row)
    ranked = sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    # query_similarity_rows is None when --query-similarity is off (the
    # similarity file doesn't exist then, so don't point readers at it).
    similarity_pointer = (", pairwise similarity scores for statements that don't share a "
                          "core_id in refs_query_similarity.tsv" if query_similarity_rows is not None else "")
    out.write("{} statement(s) across {} distinct core_id(s). Top clusters by size below "
              "-- full list in refs_query_identity.tsv{}.\n\n".format(
                  len(query_identity_rows), len(clusters), similarity_pointer))
    out.write("| core_id | Members | Example |\n|---|---:|---|\n")
    for core_id, rows in ranked[:MAX_GROUPED_VALUES]:
        example = "{}:{}".format(rows[0].file, rows[0].line)
        out.write("| `{}` | {} | `{}` |\n".format(md_escape(core_id), len(rows), md_escape(example)))
    if len(ranked) > MAX_GROUPED_VALUES:
        out.write("\n_...+{} more core_id(s), see refs_query_identity.tsv._\n".format(
            len(ranked) - MAX_GROUPED_VALUES))
    out.write("\n")
    if query_similarity_rows:
        out.write("{} core_id pair(s) scored as similar but not identical -- see "
                  "refs_query_similarity.tsv for the full list.\n\n".format(len(query_similarity_rows)))


def _write_select_blocks(out: TextIO, select_block_counts: dict[str, int]) -> None:
    out.write("## Select Blocks\n\n")
    nonzero = {f: c for f, c in select_block_counts.items() if c > 0}
    if not nonzero:
        out.write("No standalone SELECT blocks detected.\n\n")
        return
    out.write("| File | SELECT Blocks |\n|---|---:|\n")
    for fpath in sorted(nonzero):
        out.write("| `{}` | {} |\n".format(md_escape(fpath), nonzero[fpath]))
    out.write("| **Total** | **{}** |\n\n".format(sum(nonzero.values())))
    split_count = sum(1 for c in nonzero.values() if c > 1)
    if split_count:
        out.write("{} file(s) with 2+ blocks were split into per-block files and "
                  "deleted -- see split_manifest.tsv for the full original-to-split "
                  "mapping.\n\n".format(split_count))


def write_markdown_report(path: str, run_info: dict[str, Any], tree: TreeScanResult, *,
                          previously_bad: dict[str, str],
                          stopwords_count: int, stopwords_freshly_created: bool,
                          known_names_count: int, known_names_freshly_created: bool,
                          relations_summary: list[RelationRollup] | None = None,
                          query_similarity_rows: list[SimilarityPair] | None = None,
                          extract_metadata: bool = False,
                          split_selects: bool = False) -> None:
    """Writes summary.md, a fixed-size index into every artifact a scan
    produces (not a duplicate of any of them). `tree` is the finished
    TreeScanResult; everything section-worthy is read straight off it.
    Sections are written in order: run info, Sensitive Findings (with
    per-file detail subsections), String Occurrences, Bad Files,
    Stopwords, Known Names, then the opt-in sections -- Table & Column
    References / Functions / Relations / Query Identity, gated by
    `extract_metadata`; Select Blocks, gated by `split_selects`. A gated
    section is omitted entirely rather than rendered empty when its flag
    is off; a clean scan can still have JOIN relationships or bad files
    worth reporting, so those sections are independent of whether any
    finding was found. `query_similarity_rows` stays None when
    --query-similarity is off, so the Query Identity section never points
    at a similarity file that wasn't written.
    `run_info`: {invocation, root, file_count, sensitive_columns,
    extensions, workers, max_chunk_iterations, extract_metadata,
    query_similarity, split_selects, mask_literals, verbose}."""
    with open(path, "w", encoding="utf-8-sig") as out:
        _write_run_info(out, run_info)
        _write_sensitive_hits(out, tree.findings)
        _write_string_occurrences(out, tree.name_candidates)
        _write_bad_files(out, previously_bad, tree.bad_files)
        _write_stopwords(out, stopwords_count, stopwords_freshly_created)
        _write_known_names(out, known_names_count, known_names_freshly_created)
        if extract_metadata:
            _write_references(out, tree.table_uses, tree.column_uses)
            _write_functions(out, tree.function_calls)
            _write_relations(out, relations_summary or [])
            _write_query_identity(out, tree.identity_rows, query_similarity_rows)
        if split_selects:
            _write_select_blocks(out, tree.select_block_counts)


def write_strings_file(path: str, name_candidates: list[str]) -> None:
    """Write all unique name-like literals not yet classified into either
    known_names.txt or stopwords.txt (live code and comments alike, since
    comment-context examples still need triage), one per line, in the same
    format as stopwords.txt/known_names.txt so lines can be copied directly
    into either. Occurrence count is added as a '#' comment."""
    counts = _name_candidate_counts(name_candidates)

    with open(path, "w", encoding="utf-8-sig") as out:
        out.write("# Unique unclassified name-like literal(s) found in this scan: {}\n".format(
            len(counts)))
        out.write("# Copy a REAL name into known_names.txt to flag it as a finding on the next run.\n")
        out.write("# Copy a NON-name (false positive) into stopwords.txt to stop seeing it here.\n")
        out.write("# (format is compatible with both: word per line, '#' comment allowed)\n\n")
        # most frequent first: frequent words are most likely business terms
        for word in sorted(counts, key=lambda w: (-counts[w], w)):
            out.write("{}   # {} occurrence(s)\n".format(word, counts[word]))


def write_tsv_report(path: str, findings: list[Finding]) -> None:
    """Tab-separated report for pasting/filtering in Excel.
    Directory and file name are separate columns for easy filtering, and
    in_comment (Y/N) lets you filter live vs. commented-out findings
    independently of severity."""
    headers = ["severity", "in_comment", "directory", "file_name", "line",
               "column_name", "operator", "value", "snippet"]

    with open(path, "w", encoding="utf-8-sig", newline="") as out:
        out.write("\t".join(headers) + "\n")
        for f in findings:
            directory, file_name = os.path.split(f.file)
            row = [f.severity, f.in_comment, directory, file_name, f.line,
                   f.column_name, f.operator, f.value, f.snippet]
            out.write("\t".join(_clean(v) for v in row) + "\n")
