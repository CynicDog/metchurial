# -*- coding: utf-8 -*-
"""Quarantine-manifest model (--quarantine): one row per file moved out of
the scan root because its extension didn't match --extensions -- the
source rows for quarantine_manifest.tsv."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QuarantineRow:
    """One quarantined file. `original_file` no longer exists at that path
    -- it was moved to `quarantined_file` -- see
    quarantine.quarantine_non_matching."""

    original_file: str
    quarantined_file: str
