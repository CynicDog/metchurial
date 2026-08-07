# -*- coding: utf-8 -*-
"""Detection finding model: one hardcoded-sensitive-value occurrence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Finding:
    """One sensitive-value finding (comparison detection or known-name
    matching).

    `in_comment` is "Y"/"N" -- whether the literal sits inside a SQL
    comment. `start_offset`/`end_offset` are the literal's 0-based
    inclusive-inclusive character span in the original file text (None
    when the producing path couldn't pin an exact span); masking splices
    exactly this span."""

    severity: str
    file: str
    line: int
    column_name: str
    operator: str
    value: str
    snippet: str
    encoding: str
    in_comment: str
    start_offset: int | None = None
    end_offset: int | None = None
