# -*- coding: utf-8 -*-
"""--quarantine: before the scan itself runs, recursively moves every file
under the scan root whose extension isn't in --extensions out into a
separate quarantine directory -- so after a run, everything left under
root matches one of --extensions, and every file that didn't is sitting
in quarantine_dir instead, still grouped by the folder it came from.
"""

from __future__ import annotations

import os
import shutil

from metchurial.models.quarantine import QuarantineRow


def _unique_dest(path: str) -> str:
    """`path` if it doesn't exist yet; otherwise the same path with a
    numeric suffix inserted before the extension, incremented until one is
    free -- so re-running --quarantine against a tree that's already
    partially quarantined never silently clobbers an earlier move."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    n = 1
    while True:
        candidate = "{}_{}{}".format(base, n, ext)
        if not os.path.exists(candidate):
            return candidate
        n += 1


def quarantine_non_matching(root: str, extensions: tuple[str, ...], quarantine_dir: str,
                            exclude_paths: set[str] | None = None) -> list[QuarantineRow]:
    """Recursively walks `root`, moving every file whose extension
    (case-insensitive) isn't in `extensions` into `quarantine_dir`
    (created as needed), mirroring each file's path relative to `root` --
    "sub/dir/notes.docx" lands at "<quarantine_dir>/sub/dir/notes.docx" --
    so the folder a file was found in stays visible, and two same-named
    files from different folders don't collide.

    `quarantine_dir` is never descended into even when it sits inside
    `root` (e.g. root is the current directory): otherwise a second run
    would walk files it already quarantined and re-nest them one level
    deeper each time. `exclude_paths` (the scanner's own reserved output
    files -- summary.md, findings.tsv, etc. -- see cli.py) is skipped the
    same way it is for the scan itself, so an artifact like
    split_manifest.tsv (a non-matching extension by default) never gets
    quarantined out from under the tool.

    Returns one QuarantineRow per file actually moved, in os.walk order."""
    exclude_paths = exclude_paths or set()
    abs_quarantine = os.path.abspath(quarantine_dir)
    suffixes = tuple("." + ext.lower().lstrip(".") for ext in extensions)
    moved: list[QuarantineRow] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                      if os.path.abspath(os.path.join(dirpath, d)) != abs_quarantine]
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.abspath(full) in exclude_paths:
                continue
            if name.lower().endswith(suffixes):
                continue
            rel = os.path.relpath(full, root)
            dest = _unique_dest(os.path.join(quarantine_dir, rel))
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            shutil.move(full, dest)
            moved.append(QuarantineRow(original_file=full, quarantined_file=dest))
    return moved
