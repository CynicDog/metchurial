# -*- coding: utf-8 -*-
"""BadFileReason: why one file was skipped instead of scanned. Shared by
bad_file_check.py's cheap pre-check and engine.py's own two other safety
nets (an unreadable file, an unexpected crash mid-scan), so bad_files.tsv
(io_utils.py) always has the same columns to report regardless of which
of the three actually skipped the file.

Every file that reaches scan_file() already matched --extensions --
engine.py's _matching_files filters the tree by extension before any file
is ever opened, so a BadFileReason is never about extension, only about
what happened once the scan actually tried to read/lex/parse the file.
Contrast with quarantine.extensions.quarantine_non_matching (runs
automatically on every scan, moving files into _quarantine/excluded/): a
quarantined-by-extension file's extension never matched --extensions in
the first place, so it's moved out and never reaches this code at all --
bad_files.tsv is strictly the files that *did* match and got a real
attempt but failed partway through. Once flagged bad, a file is always
physically moved to _quarantine/bad_files/ too (see
quarantine.bad_files.quarantine_bad_files) -- `quarantined_file` records
where it landed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BadFileReason:
    """`category` is a short machine-stable slug ("repeated-char-run",
    "lexer-error-ratio", "unreadable", "crash") -- one TSV column callers
    can group/filter on without parsing prose. `item` is the actual
    offending value that tripped it (e.g. the matched divider text, or a
    preview of the literal characters the lexer couldn't recognize) --
    empty string where there isn't one, e.g. an unreadable file. `message`
    is the full human-readable sentence, unchanged from what used to be
    the plain string every caller already printed/interpolated -- __str__
    returning it keeps every existing '{}'.format(bad_reason)-style call
    site working without modification. `quarantined_file` is where this
    file was physically moved to once flagged bad -- empty until
    quarantine_bad_files actually moves it (never re-populated for an
    entry carried over unchanged from a previous run's bad_files.tsv)."""

    category: str
    item: str
    message: str
    quarantined_file: str = ""

    def __str__(self) -> str:
        return self.message
