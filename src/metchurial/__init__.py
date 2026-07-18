# -*- coding: utf-8 -*-
"""metchurial: an ANTLR-backed engine that turns DB2 SQL source into
structured, queryable metadata -- with hardcoded-sensitive-value detection
as one built-in analysis.

The one-call entry point::

    import metchurial

    result = metchurial.scan("/sql/root", metchurial.ScanOptions.metadata())
    for row in result.identity_rows:
        print(row.core_id, row.file, row.line)

`scan()` returns a TreeScanResult of typed rows (findings, table/column/
function references, JOIN edges, query-identity rows); writing report
artifacts is the CLI's job (metchurial.cli), not the library's. Use
`scan_file()` for a single file, `scan_tree()` if you want the same
signature `scan()` wraps. The generated Db2 lexer/parser lives in the
private `metchurial._generated` subpackage; importing this package has no
side effects (no sys.path mutation).
"""

from __future__ import annotations

from metchurial.engine import ProgressFn, scan_file, scan_tree
from metchurial.models.findings import Finding
from metchurial.models.identity import IdentityRow, SimilarityPair
from metchurial.models.options import (DEFAULT_EXTENSIONS, DEFAULT_MAX_CHUNK_ITERATIONS,
                                       DEFAULT_SENSITIVE_COLUMNS, ScanOptions)
from metchurial.models.references import ColumnUse, FunctionCall, TableUse
from metchurial.models.relations import RelationEdge, RelationRollup
from metchurial.models.results import FileScanResult, TreeScanResult

__version__ = "0.1.0"

__all__ = [
    "scan", "scan_file", "scan_tree",
    "ScanOptions", "ProgressFn",
    "DEFAULT_SENSITIVE_COLUMNS", "DEFAULT_EXTENSIONS", "DEFAULT_MAX_CHUNK_ITERATIONS",
    "Finding",
    "TableUse", "ColumnUse", "FunctionCall",
    "RelationEdge", "RelationRollup",
    "IdentityRow", "SimilarityPair",
    "FileScanResult", "TreeScanResult",
    "__version__",
]


def scan(root: str, options: ScanOptions | None = None, *,
         exclude_paths: set[str] | None = None,
         progress: ProgressFn | None = None) -> TreeScanResult:
    """Scan every SQL file under `root` and return the merged
    TreeScanResult -- a thin, importable name for engine.scan_tree(),
    so the common case reads as ``metchurial.scan(root, options)``.
    See scan_tree's docstring for the parameter details."""
    return scan_tree(root, options, exclude_paths=exclude_paths, progress=progress)
