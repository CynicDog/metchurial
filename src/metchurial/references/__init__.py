# -*- coding: utf-8 -*-
"""Schema/table/column reference extraction and JOIN relationship
extraction (both driven by --extract-metadata), built on table_scan.py's
shared token-scan engine since the vendored grammar can't structurally
parse schema-qualified names or JOIN...ON at all."""
