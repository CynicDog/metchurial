# -*- coding: utf-8 -*-
"""Standalone SELECT-block counting and splitting (--split-selects).

A "select block" is one semicolon-delimited top-level chunk (reusing
statement_driver.chunk_ranges()'s top-level-';'-at-paren-depth-0
splitting) that starts with (an optional `WITH <cte-list>` prologue, then)
SELECT. Classification is a cheap, purely token-level pass with no parser
involvement at all, mirroring table_scan.find_cte_names' WITH-list walk
(paren-depth tracking), just checking what follows instead of collecting
names -- so it works identically whether or not the parser can build a
tree for the chunk. A CTE prologue and the SELECT that consumes it are
always the same chunk by construction (a WITH clause contains no
top-level ';').
"""

from __future__ import annotations

import os
import re

from antlr4.Token import Token

from metchurial._generated.Db2Lexer import Db2Lexer

from metchurial.references.table_scan import looks_like_name_start as _looks_like_name_start
from metchurial.parsing.token_walk import skip_balanced_parens as _skip_balanced_parens
from metchurial.parsing.token_walk import skip_hidden as _skip_hidden

_SPLIT_SUFFIX_RE = re.compile(r"-\d{2,}(\.[^.]+)?$")


def classify_chunk(all_tokens: list[Token], start: int, end: int) -> bool:
    """True iff all_tokens[start:end) is a standalone SELECT block: its
    first default-channel token is SELECT, or WITH followed by a CTE list
    (tracking paren depth) that eventually reaches SELECT. Any other
    leading token (INSERT/UPDATE/DELETE/CREATE/..., or a malformed WITH
    that never reaches SELECT) -> False."""
    n = end
    i = _skip_hidden(all_tokens, start, n)
    if i is None:
        return False
    if all_tokens[i].type == Db2Lexer.SELECT:
        return True
    if all_tokens[i].type != Db2Lexer.WITH:
        return False

    i = _skip_hidden(all_tokens, i + 1, n)
    while i is not None:
        if all_tokens[i].type == Db2Lexer.SELECT or not _looks_like_name_start(all_tokens[i]):
            return False
        i = _skip_hidden(all_tokens, i + 1, n)
        if i is not None and all_tokens[i].type == Db2Lexer.LEFT_RND_BKT:
            # optional column_name_list_paren before AS
            i = _skip_hidden(all_tokens, _skip_balanced_parens(all_tokens, i), n)
        if i is None or all_tokens[i].type != Db2Lexer.AS:
            return False
        i = _skip_hidden(all_tokens, i + 1, n)
        if i is None or all_tokens[i].type != Db2Lexer.LEFT_RND_BKT:
            return False
        i = _skip_hidden(all_tokens, _skip_balanced_parens(all_tokens, i), n)
        if i is not None and all_tokens[i].type == Db2Lexer.COMMA:
            i = _skip_hidden(all_tokens, i + 1, n)
            continue
        break
    return i is not None and all_tokens[i].type == Db2Lexer.SELECT


def select_block_ranges(all_tokens: list[Token],
                        ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """ranges: statement_driver.chunk_ranges(all_tokens) (passed in, not
    recomputed). Returns the subsequence classified True, in source
    order -- both the count (len(...)) and, when --split-selects is on,
    the list to materialize as split files."""
    return [r for r in ranges if classify_chunk(all_tokens, r[0], r[1])]


def chunk_source_text(text: str, all_tokens: list[Token], start: int, end: int) -> str:
    """text[first_real.start : last_real.stop + 1], where first_real/
    last_real are the first/last non-EOF tokens in all_tokens[start:end)
    -- guards the degenerate EOF token start/stop in the last chunk range
    (EOF's own start/stop don't correspond to real source positions).
    Includes the chunk's own leading WITH-prologue and trailing ';' by
    construction, since that's exactly what chunk_ranges() already
    delimits. Leading whitespace is stripped -- chunk_ranges() starts a
    new chunk's range right after the previous chunk's ';', so its first
    token is typically the newline/whitespace trailing that ';', not
    meaningful content."""
    real = [t for t in all_tokens[start:end] if t.type != Token.EOF]
    if not real:
        return ""
    return text[real[0].start:real[-1].stop + 1].lstrip("\r\n \t")


def looks_like_split_output(filename: str) -> bool:
    """True if `filename`'s stem already ends in -NN (2+ digits) right
    before the extension (or at the very end, if there's no extension) --
    i.e. this file is itself a previously-written split-select output.
    Used to refuse to re-split an already-split file on a later re-scan of
    the same tree."""
    return _SPLIT_SUFFIX_RE.search(os.path.basename(filename)) is not None


def write_split_files(path: str, text: str, all_tokens: list[Token],
                      ranges: list[tuple[int, int]]) -> list[str]:
    """path: the original file's path. For each range in `ranges`
    (already filtered to standalone SELECT blocks via select_block_ranges,
    in source order), writes "<stem>-NN<ext>" (zero-padded to at least 2
    digits) alongside the original, containing exactly that range's
    chunk_source_text(...). Leaves the original file completely untouched.
    No-op (returns []) if there's nothing to split apart -- zero blocks, or
    exactly one (a lone SELECT block has nowhere else to go: writing a
    "-01<ext>" copy would just duplicate the original under a new name) --
    or if looks_like_split_output(path) is True."""
    if len(ranges) <= 1 or looks_like_split_output(path):
        return []
    stem, ext = os.path.splitext(path)
    width = max(2, len(str(len(ranges))))
    written = []
    for i, (start, end) in enumerate(ranges, 1):
        out_path = "{0}-{1:0{2}d}{3}".format(stem, i, width, ext)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(chunk_source_text(text, all_tokens, start, end))
        written.append(out_path)
    return written
