# -*- coding: utf-8 -*-
"""File I/O helpers: multi-encoding text reading plus the load/write pairs
for every persistent artifact metchurial maintains across runs
(bad_files.tsv, stopwords.txt, known_names.txt).
"""

from __future__ import annotations

import os
import sys
from typing import Callable

from metchurial.models.bad_file import BadFileReason
from metchurial.tsv import _clean

# Encodings to try when reading files (common on Windows / Korean environments).
ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1"]

# bad_files.tsv column order -- keep in sync with load_bad_files/write_bad_files.
_BAD_FILES_HEADER = ["path", "category", "item", "message"]


def read_text(path: str) -> tuple[str, str]:
    """Read a file's text, trying each of ENCODINGS in order and falling
    back to lossy UTF-8 decoding if none of them fit cleanly. Returns
    (text, encoding_used)."""
    for enc in ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(), enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(), "utf-8(replace)"


def _for_each_line(path: str, handle_line: Callable[[str], None]) -> None:
    """Call handle_line(line) for each line of `path`, trying ENCODINGS in
    order until one decodes the whole file cleanly. Lines decoded before a
    mid-file decode failure have already been handled; a file no encoding
    fits is processed as far as each attempt got."""
    for enc in ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as f:
                for line in f:
                    handle_line(line)
            return
        except (UnicodeDecodeError, UnicodeError):
            continue


def load_bad_files(path: str) -> dict[str, BadFileReason]:
    """Load a persistent bad_files.tsv (see cli.py's skip-list workflow):
    one file per row -- path, category, item, message, tab-separated,
    fixed header row first (same conventions as tsv.write_refs_tsv).
    Returns {abspath: BadFileReason} for every entry. A missing file is
    the normal first-run state, so this returns an empty dict silently
    rather than warning (unlike load_stopwords/load_known_names below,
    where a missing file is unexpected)."""
    entries: dict[str, BadFileReason] = {}
    if not path or not os.path.isfile(path):
        return entries

    seen_header = False

    def add_entry(line: str) -> None:
        nonlocal seen_header
        line = line.rstrip("\r\n")
        if not line:
            return
        if not seen_header:
            seen_header = True
            return
        parts = line.split("\t")
        p = parts[0].strip()
        if not p:
            return
        category = parts[1] if len(parts) > 1 else ""
        item = parts[2] if len(parts) > 2 else ""
        message = parts[3] if len(parts) > 3 else ""
        entries[os.path.abspath(p)] = BadFileReason(category=category, item=item, message=message)

    _for_each_line(path, add_entry)
    return entries


def write_bad_files(path: str, entries: dict[str, BadFileReason]) -> None:
    """Writes bad_files.tsv: one row per file -- path, category, item,
    message, tab-separated, sorted by path for stable diffs across runs,
    same conventions as tsv.write_refs_tsv (utf-8-sig, header row always
    written, embedded tabs/newlines stripped from every cell). `entries`:
    {path: BadFileReason}. Deleting a data row (keeping the header) lets
    that file be re-scanned on the next run instead of skipped."""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write("\t".join(_BAD_FILES_HEADER) + "\n")
        for p in sorted(entries):
            reason = entries[p]
            f.write("\t".join(_clean(v) for v in
                              (p, reason.category, reason.item, reason.message)) + "\n")


def ensure_stopwords_template(path: str) -> None:
    """Write an empty stopwords.txt with a format-explaining header if one
    doesn't exist yet -- same self-maintaining convention as bad_files.tsv
    (write_bad_files above), so a fresh checkout gets a stopwords.txt to
    edit in place instead of needing one hand-created first."""
    if os.path.isfile(path):
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write("# metchurial stopwords list -- one word per line, '#' comment "
               "allowed (everything after '#' on a line is ignored).\n")
        f.write("# A word here has been reviewed and confirmed NOT a sensitive "
               "name -- it's excluded from strings.txt on every future run. "
               "See strings.txt for candidates to triage.\n")


def _load_word_set(path: str, missing_label: str) -> set[str]:
    """Load a word-per-line file ('#' comments allowed) into a set.
    Warns to stderr, naming the file as `missing_label`, when it's
    missing."""
    words = set()
    if not path:
        return words
    if not os.path.isfile(path):
        print("[WARN] {} file not found: {}".format(missing_label, path), file=sys.stderr)
        return words

    def add_word(line: str) -> None:
        w = line.split("#", 1)[0].strip()
        if w:
            words.add(w)

    _for_each_line(path, add_word)
    return words


def load_stopwords(path: str) -> set[str]:
    """Load stopword file: one word per line, '#' comments allowed."""
    return _load_word_set(path, "stopword")


def ensure_known_names_template(path: str) -> None:
    """Write an empty known_names.txt with a format-explaining header if one
    doesn't exist yet -- same self-maintaining convention as stopwords.txt
    above."""
    if os.path.isfile(path):
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write("# metchurial known-names list -- one word per line, '#' comment "
               "allowed (everything after '#' on a line is ignored).\n")
        f.write("# A word here has been reviewed and confirmed a real sensitive "
               "name -- every matching literal is flagged as a finding on every "
               "future run, regardless of which column it's compared to. See "
               "strings.txt for candidates to triage.\n")


def load_known_names(path: str) -> set[str]:
    """Load known-names file: one word per line, '#' comments allowed."""
    return _load_word_set(path, "known-names")
