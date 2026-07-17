# -*- coding: utf-8 -*-
"""Domain models: plain stdlib dataclasses shared across the scan
pipeline. One module per domain -- SQL structure (tables/joins), detection
findings, metadata references, JOIN relations, query identity, and scan
results. No third-party dependencies, matching the zero-install bundle
contract."""

from src.models.findings import Finding
from src.models.identity import IdentityRow, SimilarityPair
from src.models.references import ColumnUse, FunctionCall, TableUse
from src.models.relations import RelationEdge, RelationRollup
from src.models.results import FileScanResult, TreeScanResult
from src.models.tables import (PLACEHOLDER_SCHEMA, PLACEHOLDER_TABLE, JoinEdge, QueryBlock,
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
