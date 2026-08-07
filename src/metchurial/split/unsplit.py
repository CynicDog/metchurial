# -*- coding: utf-8 -*-
"""--un-split-selects: reverts a previous --split-selects run using
split_manifest.tsv's own rows -- regroups them by original_file and, for
every group that's still fully intact on disk, concatenates its split
files' current content back together in block_number order, writes that
to original_file, and deletes the split files.

This is a best-effort reconstruction, not a byte-for-byte undo:
split.select_blocks.chunk_source_text strips each block's leading
whitespace when it's first split out, so the exact inter-statement blank
lines/formatting from before the original split can't be recovered -- the
result is fresh, valid SQL semantically equivalent to the pre-split file,
not necessarily identical bytes. A split file may also have been edited
since it was written (e.g. during review) -- reverting always uses each
split file's current on-disk content, not whatever it held at split time.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable
import os

from metchurial.io_utils import read_text
from metchurial.models.split import SplitManifestRow


def revert_splits(rows: list[SplitManifestRow],
                  warn: Callable[[str], None] | None = None,
                  ) -> tuple[list[str], list[SplitManifestRow]]:
    """rows: split_manifest.tsv's own rows (io_utils.load_split_manifest).
    `warn`, if given, is called with a one-line message for each group
    left un-reverted.

    A group is left completely alone -- none of its split files touched,
    all its rows kept for the caller to write back to split_manifest.tsv
    unchanged -- rather than guessing, if any of:
    - it has fewer rows than its own total_blocks (e.g. reverting against
      a manifest from an interrupted or partial run);
    - original_file already exists again (something else recreated it
      since the split -- never overwritten);
    - one of its split_file entries is no longer on disk (deleted or
      moved since the split).

    Returns (reverted_original_files, remaining_rows)."""
    warn = warn or (lambda msg: None)
    groups: dict[str, list[SplitManifestRow]] = defaultdict(list)
    for row in rows:
        groups[row.original_file].append(row)

    reverted: list[str] = []
    remaining: list[SplitManifestRow] = []
    for original_file, group_rows in groups.items():
        group_rows.sort(key=lambda r: r.block_number)
        total = group_rows[0].total_blocks
        if len(group_rows) != total:
            warn("unsplit: {} has {} of {} split file(s) recorded -- skipped".format(
                original_file, len(group_rows), total))
            remaining.extend(group_rows)
            continue
        if os.path.exists(original_file):
            warn("unsplit: {} already exists -- skipped, not overwritten".format(
                original_file))
            remaining.extend(group_rows)
            continue
        missing = [r.split_file for r in group_rows if not os.path.isfile(r.split_file)]
        if missing:
            warn("unsplit: {} missing split file(s) for {}: {} -- skipped".format(
                len(missing), original_file, ", ".join(missing)))
            remaining.extend(group_rows)
            continue

        texts = [read_text(r.split_file)[0] for r in group_rows]
        with open(original_file, "w", encoding="utf-8") as f:
            f.write("\n\n".join(texts))
        for r in group_rows:
            os.remove(r.split_file)
        reverted.append(original_file)

    return reverted, remaining
