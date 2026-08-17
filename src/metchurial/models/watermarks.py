# -*- coding: utf-8 -*-
"""Incremental-load watermark models (--extract-metadata): one row per
WHERE-predicate occurrence that filters a column against a rolling
"today minus a window" expression."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WatermarkUse:
    """One incremental-load filter occurrence: a comparison predicate whose
    non-column side is a datetime special register offset by a duration
    (`CURRENT DATE - 3 DAYS`), optionally wrapped in formatting/encoding
    calls (`CHAR(...)`, `DECIMAL(CHAR(...))`, `HEX(...)`).

    `schema`/`table` are the alias-resolved owner of `watermark_column`
    where resolvable, placeholders otherwise -- same convention
    refs_columns.tsv uses. `watermark_column` is the column name when the
    compared side is a plain column reference, and that side's raw source
    text otherwise (a formatted/derived key like
    `SUBSTR(load_dt, 1, 6)` is still a watermark worth auditing).

    `operator` is the comparison operator connecting the two sides, always
    written left-to-right as `watermark_column <operator> window_expression`
    regardless of which side each sat on in the source. `base` is the
    datetime special register the window is measured from (`CURRENT DATE`,
    `CURRENT TIMESTAMP`, `CURRENT TIME`).

    `window_expression` is the whole date-arithmetic side's raw source
    text, exactly as written. `window_size` is its normalized form -- a
    tuple because one predicate can carry several candidate sizes (a
    `DECODE`-by-weekday window), rendered as one '; '-joined TSV cell by
    tsv._cell, the same convention list-valued columns already use
    elsewhere. Empty when the offset amount isn't an integer literal
    (a host variable, say) and so has no size to normalize.

    `pattern` names the shape that matched, so a reader can tell at a
    glance which detector branch produced the row and filter on it -- see
    references/watermarks.py for the tag vocabulary."""

    schema: str
    table: str
    watermark_column: str
    operator: str
    base: str
    window_expression: str
    window_size: tuple[str, ...]
    pattern: str
    file: str
    line: int
