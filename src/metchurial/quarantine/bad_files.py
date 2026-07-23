# -*- coding: utf-8 -*-
"""After the scan itself runs, physically moves every file it flagged bad
this run (models/bad_file.py's BadFileReason, one per tree.bad_files entry
-- see engine.py) out of the scanned tree and into _quarantine/bad_files/,
mirroring its path relative to root the same way quarantine.extensions
does for _quarantine/excluded/. Runs automatically on every scan (see
cli.py), not behind an opt-in flag: a bad file already didn't get scanned
for sensitive content, so leaving it sitting in a tree that's about to be
compressed and shipped outside the company is the one thing this project
can't accept.

A file already recorded as bad on a *previous* run is never re-processed
here: it's excluded from this run's scan entirely (see cli.py's
`previously_bad`/exclude_paths), so tree.bad_files only ever contains
files bad *this* run -- exactly the ones that still need physically
moving.
"""

from __future__ import annotations

import os
import shutil
from typing import Callable

from metchurial.models.bad_file import BadFileReason
from metchurial.quarantine.extensions import unique_dest


def quarantine_bad_files(bad_files: dict[str, BadFileReason], root: str, bad_files_dir: str,
                         warn: Callable[[str], None] | None = None,
                         ) -> dict[str, BadFileReason]:
    """bad_files: {path: BadFileReason} for every file flagged bad *this
    run* (tree.bad_files) -- not the merged previously_bad + this-run set,
    since a previously-bad file was never re-scanned and so was never
    still sitting at its original path to move in the first place.

    For each, moves the file to `bad_files_dir`, mirroring its path
    relative to `root` (falling back to just the basename if it isn't
    actually under `root` -- e.g. an absolute path outside it), and
    returns a new {path: BadFileReason} dict where each reason's
    `quarantined_file` is set to its destination. A file that no longer
    exists at `path` (already moved by something else, or a race) or
    can't be moved (OSError) is left with `quarantined_file` still empty
    and reported via `warn` -- its bad_files.tsv row still records the
    original path and reason, just with no destination to point at."""
    warn = warn or (lambda msg: None)
    updated: dict[str, BadFileReason] = {}
    for path, reason in bad_files.items():
        try:
            rel = os.path.relpath(path, root)
        except ValueError:
            rel = os.path.basename(path)
        if rel.startswith(".."):
            rel = os.path.basename(path)
        dest = unique_dest(os.path.join(bad_files_dir, rel))
        try:
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            shutil.move(path, dest)
        except OSError as e:
            warn("quarantine: cannot move bad file {}: {}".format(path, e))
            updated[path] = reason
            continue
        updated[path] = BadFileReason(
            category=reason.category, item=reason.item, message=reason.message,
            quarantined_file=dest)
    return updated
