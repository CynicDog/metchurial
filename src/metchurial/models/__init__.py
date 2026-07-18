# -*- coding: utf-8 -*-
"""Domain models: plain stdlib dataclasses shared across the scan
pipeline. One module per domain -- SQL structure (tables/joins), detection
findings, metadata references, JOIN relations, query identity, and scan
results. No third-party dependencies, matching the zero-install bundle
contract."""

from metchurial.models.findings import Finding
from metchurial.models.identity import IdentityRow, SimilarityPair
from metchurial.models.references import ColumnUse, FunctionCall, TableUse
from metchurial.models.relations import RelationEdge, RelationRollup
from metchurial.models.results import FileScanResult, TreeScanResult
from metchurial.models.tables import (PLACEHOLDER_SCHEMA, PLACEHOLDER_TABLE, JoinEdge, QueryBlock,
                               TableRef)

__all__ = [
    "PLACEHOLDER_SCHEMA", "PLACEHOLDER_TABLE",
    "TableRef", "QueryBlock", "JoinEdge",
    "Finding",
    "TableUse", "ColumnUse", "FunctionCall",
    "RelationEdge", "RelationRollup",
    "IdentityRow", "SimilarityPair",
    "FileScanResult", "TreeScanResult",
]
