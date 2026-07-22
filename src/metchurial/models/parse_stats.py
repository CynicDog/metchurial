# -*- coding: utf-8 -*-
"""Per-file ANTLR processing stats: not a profile, just enough for
--verbose's one-line-per-file summary to say where a slow file's time
went, without the volume of a real profiler dump."""

from __future__ import annotations

from dataclasses import dataclass


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
    a summary, not an exhaustive accounting. `elapsed_seconds`: wall-clock
    time for the whole scan_file() call, set by engine.py, not
    statement_driver.py, since it covers lexing/detection/extraction too,
    not just the tiered parse."""

    chunks: int = 0
    iterations: int = 0
    tier1_structural: int = 0
    tier1_token_scan: int = 0
    tier2_resync: int = 0
    tier3_skip: int = 0
    elapsed_seconds: float = 0.0
