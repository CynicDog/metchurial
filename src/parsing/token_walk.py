# -*- coding: utf-8 -*-
"""Primitive cursor movements over a lexed ``Token`` list, shared by every
token-scan pass (table_scan.py, select_blocks.py)."""

from __future__ import annotations

from antlr4.Token import Token

from Db2Lexer import Db2Lexer


def skip_hidden(tokens: list[Token], i: int, n: int) -> int | None:
    """Index >= i of the next default-channel token, or None past the end."""
    while i < n and tokens[i].channel != Token.DEFAULT_CHANNEL:
        i += 1
    return i if i < n else None


def skip_balanced_parens(tokens: list[Token], open_idx: int) -> int:
    """tokens[open_idx] is a LEFT_RND_BKT. Returns the index right after
    its matching RIGHT_RND_BKT (or len(tokens) if unbalanced, which
    shouldn't happen post-lex but is a safe, non-crashing fallback)."""
    depth = 0
    n = len(tokens)
    i = open_idx
    while i < n:
        t = tokens[i].type
        if t == Db2Lexer.LEFT_RND_BKT:
            depth += 1
        elif t == Db2Lexer.RIGHT_RND_BKT:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n
