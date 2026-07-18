# -*- coding: utf-8 -*-
"""Scan result models: everything one file scan (and one whole-tree scan)
produces, as named fields instead of positional tuples."""

from __future__ import annotations

from dataclasses import dataclass, field

from metchurial.models.findings import Finding
from metchurial.models.identity import IdentityRow
from metchurial.models.references import ColumnUse, FunctionCall, TableUse
from metchurial.models.relations import RelationEdge


@dataclass
class FileScanResult:
    """Everything scan_file() produces for one file. `bad_reason` is None
    on a normal scan; otherwise a short human-readable skip reason, with
    every other field empty/zero."""

    findings: list[Finding] = field(default_factory=list)
    name_candidates: list[str] = field(default_factory=list)
    table_uses: list[TableUse] = field(default_factory=list)
    column_uses: list[ColumnUse] = field(default_factory=list)
    relation_edges: list[RelationEdge] = field(default_factory=list)
    select_block_count: int = 0
    function_calls: list[FunctionCall] = field(default_factory=list)
    identity_rows: list[IdentityRow] = field(default_factory=list)
    bad_reason: str | None = None


@dataclass
class TreeScanResult:
    """Everything scan_tree() produces, merged across all scanned files.
    `select_block_counts` maps file path -> standalone SELECT-block count
    (only populated when splitting is on); `bad_files` maps file path ->
    skip reason."""

    findings: list[Finding] = field(default_factory=list)
    name_candidates: list[str] = field(default_factory=list)
    table_uses: list[TableUse] = field(default_factory=list)
    column_uses: list[ColumnUse] = field(default_factory=list)
    relation_edges: list[RelationEdge] = field(default_factory=list)
    select_block_counts: dict[str, int] = field(default_factory=dict)
    function_calls: list[FunctionCall] = field(default_factory=list)
    bad_files: dict[str, str] = field(default_factory=dict)
    identity_rows: list[IdentityRow] = field(default_factory=list)
    file_count: int = 0
