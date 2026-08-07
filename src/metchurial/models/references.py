# -*- coding: utf-8 -*-
"""Metadata reference models (--extract-metadata): one row per syntactic
occurrence -- deduplication happens at the report layer, not here."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TableUse:
    """One schema.table reference occurrence."""

    schema: str
    table: str
    file: str
    line: int


@dataclass
class ColumnUse:
    """One column reference occurrence, alias-resolved to its owning
    schema.table where possible (placeholders otherwise)."""

    schema: str
    table: str
    column: str
    file: str
    line: int


@dataclass
class FunctionCall:
    """One function-call or predicate-operator usage site. `function`
    holds either a function name (SUBSTR, UPPER, ...) or an operator name
    (=, IN, BETWEEN, ...); `parameters` the operands' raw source text."""

    function: str
    parameters: str
    file: str
    line: int
