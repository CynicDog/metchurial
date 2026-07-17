# -*- coding: utf-8 -*-
"""--mask-literals: rewrites in place each file that has a finding, with
every flagged literal's content replaced by a fixed placeholder, everything
else in the file byte-for-byte unchanged.

This module never re-derives "is this a sensitive literal" itself -- it
strictly consumes the (start_offset, end_offset) span already captured on
each finding dict by extractor_visitor.py/supplementary_checks.py/
comment_rescan.py (sensitive-column comparison detection's finding, via
three independent detection paths) and scan.py's known_names.txt-matching
regex pass (known-name matching's finding). That division
of labor is what makes masking automatically safe against the large set of
edge cases those detectors already handle (bare-paren-before-literal,
double-quoted literals, IN-lists, BETWEEN bounds, reversed comparisons,
subquery scoping, malformed/truncated comment fragments, host variables,
bare identifiers, blank literals, ...): if a construct doesn't produce a
finding, masking never sees a span for it, so it's never touched.

Offsets follow the same convention used everywhere in this codebase (see
extractor_visitor.as_literal / references/function_visitor._slice):
0-based, inclusive-inclusive -- text[start_offset:end_offset + 1] is the
literal's exact original-source span, quote characters included when
quoted.
"""

import codecs
import re
from collections import defaultdict

from src.io_utils import read_text

MASK_TEXT = "****"      # replaces a quoted literal's inner content
MASK_NUMERIC = "0000"   # replaces an unquoted numeric literal wholesale

# Matches an unquoted numeric literal in any of the shapes this grammar's
# constant_ rule can produce: a plain integer (DECIMAL_LITERAL), a decimal
# with a fractional part (FLOAT_LITERAL, e.g. "123.45" or ".5"), or one
# with an exponent (REAL_LITERAL, e.g. "1.5E10"). Masking always replaces
# any of these with the same fixed MASK_NUMERIC, which is itself a valid
# DECIMAL_LITERAL, so the result can never become invalid SQL regardless
# of which numeric shape the original literal was.
_NUMERIC_RE = re.compile(r"^(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")


def _literal_replacement(span_text):
    """span_text = original_text[start:end + 1] for one finding's span.
    Returns the masked replacement, or None if this span's shape isn't one
    of the two literal shapes sensitive-column comparison detection/
    known-name matching can actually produce. This is
    defense in depth, not the primary safety mechanism: e.g. NULL is a
    legal `constant_` alternative in the vendored grammar that
    as_literal() could in principle return as a finding value (no upstream
    code special-cases it today), so this guard guarantees masking still
    never touches a keyword like that even if it ever reached here,
    without adding any new literal-matching logic of its own -- it only
    ever classifies a span that's already a confirmed finding."""
    if len(span_text) >= 2 and span_text[0] in ("'", '"') and span_text[-1] == span_text[0]:
        q = span_text[0]
        return q + MASK_TEXT + q
    if _NUMERIC_RE.match(span_text):
        return MASK_NUMERIC
    return None


def mask_text(original_text, spans, warn=None):
    """Pure function. original_text: one file's full source text. spans:
    iterable of (start_offset, end_offset) 0-based inclusive-inclusive
    pairs. Returns (masked_text, stats) where stats has keys "masked",
    "skipped_overlap", "skipped_unmaskable". `warn`, if given, is called
    with a one-line message for each skipped span.

    Spans are de-duplicated and sorted, then spliced left-to-right in a
    single pass -- never a repeated text search, so this can't misfire on
    lookalike text elsewhere in the file the way a naive find-and-replace
    could. An overlapping span (possible via the CTE-body-resurfaced-as-
    its-own-statement quirk documented in README's Known Limitations,
    which can cause the same literal to be independently re-visited) is
    skipped rather than corrupting the splice."""
    stats = {"masked": 0, "skipped_overlap": 0, "skipped_unmaskable": 0}
    unique_spans = sorted(set(spans))
    out = []
    cursor = 0
    prev_end = -1
    for start, end in unique_spans:
        if start <= prev_end:
            stats["skipped_overlap"] += 1
            if warn:
                warn("mask: overlapping span ({}, {}) skipped".format(start, end))
            continue
        span_text = original_text[start:end + 1]
        replacement = _literal_replacement(span_text)
        if replacement is None:
            stats["skipped_unmaskable"] += 1
            if warn:
                warn("mask: span ({}, {}) = {!r} doesn't look like a literal, "
                    "not masked".format(start, end, span_text))
            continue
        out.append(original_text[cursor:start])
        out.append(replacement)
        cursor = end + 1
        prev_end = end
        stats["masked"] += 1
    out.append(original_text[cursor:])
    return "".join(out), stats


def _write_encoding_for(path, enc):
    """io_utils.read_text tries "utf-8-sig" first, and that codec silently
    decodes a plain UTF-8 file with no BOM too (it only strips a BOM if
    one is actually present) -- so `enc` alone can't tell whether the
    original file actually had a BOM. Writing back with "utf-8-sig"
    unconditionally would therefore *add* a BOM to a file that never had
    one, breaking the "byte-for-byte identical outside masked spans"
    guarantee. Check the original file's own raw bytes to decide."""
    if enc == "utf-8(replace)":
        return "utf-8"
    if enc == "utf-8-sig":
        try:
            with open(path, "rb") as fh:
                had_bom = fh.read(3) == codecs.BOM_UTF8
        except OSError:
            had_bom = False
        return "utf-8-sig" if had_bom else "utf-8"
    return enc


def write_masked_files(findings, warn=None):
    """findings: hits (see cli.py). For each distinct file among them,
    re-reads the file (via io_utils.read_text -- the same deterministic
    encoding auto-detection used during scanning; re-detecting is safe
    since the file's bytes haven't changed since it was scanned), builds
    the masked text, and overwrites the file in place with it. A file all
    of whose findings get defensively skipped (nothing actually masked)
    is left untouched. Returns the list of paths rewritten."""
    by_file = defaultdict(list)
    for f in findings:
        if f.get("start_offset") is None or f.get("end_offset") is None:
            continue
        by_file[f["file"]].append(f)

    written = []
    for path, file_findings in sorted(by_file.items()):
        try:
            original_text, enc = read_text(path)
        except OSError as e:
            if warn:
                warn("mask: cannot re-read {}: {}".format(path, e))
            continue

        spans = [(f["start_offset"], f["end_offset"]) for f in file_findings]
        masked_text, stats = mask_text(original_text, spans, warn=warn)
        if stats["masked"] == 0:
            continue

        write_encoding = _write_encoding_for(path, enc)
        try:
            with open(path, "w", encoding=write_encoding) as fh:
                fh.write(masked_text)
        except OSError as e:
            if warn:
                warn("mask: cannot write {}: {}".format(path, e))
            continue
        written.append(path)
    return written
