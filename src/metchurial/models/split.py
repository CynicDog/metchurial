# -*- coding: utf-8 -*-
"""Split-manifest model (--split-selects): one row per SELECT block written
out of an original file -- the source rows for split_manifest.tsv, which
records exactly which split files each deleted original became."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SplitManifestRow:
    """One split-select output file. `original_file` was deleted once all
    `total_blocks` split files were written -- see
    split.select_blocks.write_split_files."""

    original_file: str
    split_file: str
    block_number: int
    total_blocks: int
