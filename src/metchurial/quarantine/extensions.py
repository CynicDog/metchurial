# -*- coding: utf-8 -*-
"""Before the scan itself runs, recursively moves every file under the
scan root whose extension isn't in --extensions out into
_quarantine/excluded/ -- so after a run, everything left under root
matches one of --extensions, and every file that didn't is sitting in
excluded_dir instead, still grouped by the folder it came from. Runs
automatically on every scan (see cli.py), not behind an opt-in flag.

Complementary to bad_files.tsv (models/bad_file.py) and
quarantine.bad_files, not a variant of either: a file quarantined here
never even gets opened, since --extensions rules it out before the scan
starts -- bad_files.tsv is strictly for files that *did* match
--extensions and were actually read/lexed/parsed but failed partway
through. Nothing that ends up in excluded_dir can ever appear in
bad_files.tsv, and vice versa.
"""

from __future__ import annotations

import os
import shutil

from metchurial.models.options import extension_suffixes
from metchurial.models.quarantine import QuarantineRow


def unique_dest(path: str) -> str:
    """`path` if it doesn't exist yet; otherwise the same path with a
    numeric suffix inserted before the extension, incremented until one is
    free -- so a second run against a tree that's already partially
    quarantined never silently clobbers an earlier move. Shared with
    quarantine.bad_files, which needs the same guarantee."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    n = 1
    while True:
        candidate = "{}_{}{}".format(base, n, ext)
        if not os.path.exists(candidate):
            return candidate
        n += 1


def quarantine_non_matching(root: str, extensions: tuple[str, ...], excluded_dir: str,
                            exclude_paths: set[str] | None = None) -> list[QuarantineRow]:
    """Recursively walks `root`, moving every file whose extension
    (case-insensitive) isn't in `extensions` into `excluded_dir` (created
    as needed), mirroring each file's path relative to `root` --
    "sub/dir/notes.docx" lands at "<excluded_dir>/sub/dir/notes.docx" --
    so the folder a file was found in stays visible, and two same-named
    files from different folders don't collide.

    `excluded_dir`'s own top-level ancestor (_quarantine/) is never
    descended into even when it sits inside `root` (e.g. root is the
    current directory): otherwise a second run would walk files it
    already quarantined and re-nest them one level deeper each time.
    `exclude_paths` (the scanner's own reserved output files -- summary.md,
    findings.tsv, etc. -- see cli.py) is skipped the same way it is for
    the scan itself, so an artifact like split_manifest.tsv (a
    non-matching extension by default) never gets quarantined out from
    under the tool.

    Returns one QuarantineRow per file actually moved, in os.walk order."""
    exclude_paths = exclude_paths or set()
    # Skip the whole _quarantine/ root, not just excluded_dir itself --
    # bad_files/ is a sibling under the same root and must never be
    # walked back into either.
    abs_quarantine_root = os.path.abspath(os.path.dirname(os.path.normpath(excluded_dir)))
    suffixes = extension_suffixes(extensions)
    moved: list[QuarantineRow] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                      if os.path.abspath(os.path.join(dirpath, d)) != abs_quarantine_root]
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.abspath(full) in exclude_paths:
                continue
            if name.lower().endswith(suffixes):
                continue
            rel = os.path.relpath(full, root)
            dest = unique_dest(os.path.join(excluded_dir, rel))
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            shutil.move(full, dest)
            moved.append(QuarantineRow(original_file=full, quarantined_file=dest))
    return moved
