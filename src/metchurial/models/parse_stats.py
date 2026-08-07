# -*- coding: utf-8 -*-
"""Per-file ANTLR processing stats: not a profile, just enough for
--verbose's one-line-per-file summary to say where a slow file's time
went, without the volume of a real profiler dump."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParseStats:
    """`chunks`: statement-sized chunks the file was split into
    (statement_driver.chunk_ranges). `iterations`: total tiered-loop
    iterations summed across every chunk. `tier1_structural`/
    `tier1_token_scan`/`tier2_resync`/`tier3_skip`: how those iterations
    were resolved -- a direct sql_statement()/search_condition() or
    token-scan hit, a Tier 2 resync-anchor jump, or a Tier 3 single-token
    skip (see parsing/statement_driver.py's module docstring for what
    each tier means). Covers only the top-level live-code parse, not
    comment_rescan.py's own nested parse_file() calls over comment text --
    a summary, not an exhaustive accounting. `inferred_boundaries`: how
    many of those chunks came from parsing/statement_starts.py inferring a
    statement start rather than from a real top-level ';' -- 0 for a
    conventionally punctuated file, and the number to look at when a
    split looks wrong. `guard_hits`: how many times each boundary guard
    (models/statement_boundary.py, keyed by its guard_id, plus
    "line-start" for the positive rule's own line requirement) stopped a
    candidate keyword from becoming a boundary -- the evidence for which
    guards are load-bearing on a real corpus rather than theoretical.
    `elapsed_seconds`: wall-clock time for the whole
    scan_file() call, set by engine.py, not statement_driver.py, since it
    covers lexing/detection/extraction too, not just the tiered parse."""

    chunks: int = 0
    iterations: int = 0
    tier1_structural: int = 0
    tier1_token_scan: int = 0
    tier2_resync: int = 0
    tier3_skip: int = 0
    inferred_boundaries: int = 0
    guard_hits: dict[str, int] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
