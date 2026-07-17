# -*- coding: utf-8 -*-
"""File I/O helpers: multi-encoding text reading plus the load/write pairs
for every line-delimited artifact metchurial maintains across runs
(bad_files.txt, stopwords.txt, known_names.txt).
"""

import os
import sys

# Encodings to try when reading files (common on Windows / Korean environments).
ENCODINGS = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1"]


def read_text(path):
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


def _for_each_line(path, handle_line):
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


def load_bad_files(path):
    """Load a persistent bad_files.txt (see cli.py's skip-list workflow):
    one file path per line, with an optional trailing '# reason' comment
    (same convention as stopwords.txt below). Returns {abspath: reason}
    for every entry -- reason is "" if none was recorded. A missing file
    is the normal first-run state, so this returns an empty dict silently
    rather than warning (unlike load_stopwords/load_known_names below,
    where a missing file is unexpected)."""
    entries = {}
    if not path or not os.path.isfile(path):
        return entries

    def add_entry(line):
        if "#" in line:
            p, reason = line.split("#", 1)
            p, reason = p.strip(), reason.strip()
        else:
            p, reason = line.strip(), ""
        if p:
            entries[os.path.abspath(p)] = reason

    _for_each_line(path, add_entry)
    return entries


def write_bad_files(path, entries):
    """Writes bad_files.txt: one path per line, its reason as a trailing
    '#' comment, sorted for stable diffs across runs. `entries`:
    {path: reason}. Deleting a line lets that file be re-scanned on the
    next run instead of skipped."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("# metchurial bad-files list -- one file per line, reason as a "
               "trailing '#' comment.\n")
        f.write("# A file listed here is skipped entirely on the next run. Delete "
               "its line (after fixing the file) to have it re-scanned.\n")
        for p in sorted(entries):
            reason = entries[p]
            f.write("{}  # {}\n".format(p, reason) if reason else "{}\n".format(p))


def ensure_stopwords_template(path):
    """Write an empty stopwords.txt with a format-explaining header if one
    doesn't exist yet -- same self-maintaining convention as bad_files.txt
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


def _load_word_set(path, missing_label):
    """Load a word-per-line file ('#' comments allowed) into a set.
    Warns to stderr, naming the file as `missing_label`, when it's
    missing."""
    words = set()
    if not path:
        return words
    if not os.path.isfile(path):
        print("[WARN] {} file not found: {}".format(missing_label, path), file=sys.stderr)
        return words

    def add_word(line):
        w = line.split("#", 1)[0].strip()
        if w:
            words.add(w)

    _for_each_line(path, add_word)
    return words


def load_stopwords(path):
    """Load stopword file: one word per line, '#' comments allowed."""
    return _load_word_set(path, "stopword")


def ensure_known_names_template(path):
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


def load_known_names(path):
    """Load known-names file: one word per line, '#' comments allowed."""
    return _load_word_set(path, "known-names")
