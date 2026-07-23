# -*- coding: utf-8 -*-
"""Quarantine-manifest model: one row per file moved out of the scan root
because its extension didn't match --extensions (quarantine.extensions,
runs automatically on every scan) -- the source rows for
quarantine_manifest.tsv."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QuarantineRow:
    """One quarantined file. `original_file` no longer exists at that path
    -- it was moved to `quarantined_file` -- see
    quarantine.extensions.quarantine_non_matching."""

    original_file: str
    quarantined_file: str
