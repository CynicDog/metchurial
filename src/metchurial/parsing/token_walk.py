# -*- coding: utf-8 -*-
"""Primitive cursor movements and name-shape tests over a lexed ``Token``
list, shared by every token-scan pass (table_scan.py, select_blocks.py,
statement_starts.py).

The name-shape helpers live here rather than in references/table_scan.py,
where they grew, so that parsing/ (the lower layer) can use them without
importing from references/ (the higher one) -- statement_starts.py needs
looks_like_name_start to validate a CTE prologue."""

from __future__ import annotations

from antlr4.Token import Token

from metchurial._generated.Db2Lexer import Db2Lexer


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


# Tokens that can never be the next segment of a dotted schema/catalog-
# qualified name -- everything else immediately after a '.' in a table-
# reference position is treated as an identifier-like segment (see
# looks_like_name_segment), not just plain ID. Real DB2 system catalog
# views collide with reserved keywords constantly and there's no way to
# whitelist them all individually (SYSCAT.TABLES, SYSCAT.COLUMNS,
# SYSCAT.INDEXES -- TABLES/COLUMNS/INDEXES are each their own lexer
# token, not ID) -- this is the structural signal (position right after
# a '.') doing the work instead of a keyword list.
NOT_A_NAME_SEGMENT = {
    Db2Lexer.COMMA, Db2Lexer.LEFT_RND_BKT, Db2Lexer.RIGHT_RND_BKT, Db2Lexer.SEMI,
    Db2Lexer.WHERE, Db2Lexer.ON, Db2Lexer.USING, Db2Lexer.AS, Db2Lexer.DOT,
    Db2Lexer.JOIN, Db2Lexer.INNER, Db2Lexer.LEFT, Db2Lexer.RIGHT, Db2Lexer.FULL, Db2Lexer.CROSS,
}

# Literal token shapes -- never a name, at any position. DOUBLE_QUOTE_ID is
# deliberately not here: a delimited identifier ("MyTable") is a real name,
# just a quoted one -- looks_like_name_segment already treats it as one for
# a dotted continuation (schema."Table"), so looks_like_name_start does too
# for consistency (see name_text for the matching quote-stripping).
NAME_LITERAL_TOKEN_TYPES = {
    Db2Lexer.STRING_LITERAL, Db2Lexer.CHAR_LITERAL, Db2Lexer.DECIMAL_LITERAL,
    Db2Lexer.FLOAT_LITERAL, Db2Lexer.REAL_LITERAL,
}


def looks_like_name_segment(token: Token) -> bool:
    return token.type not in NOT_A_NAME_SEGMENT


def looks_like_name_start(token: Token) -> bool:
    """True if `token` can open a table/CTE name. The position itself is
    the structural signal (right after FROM/UPDATE/INTO/COMMA/JOIN, or
    right after WITH / a CTE-list comma) -- the same reserved-keyword-
    collision argument as looks_like_name_segment: real table and CTE
    names routinely collide with the grammar's reserved words (BASE,
    ORDER, ...) and lex as their own token types, not plain ID, so a
    type whitelist would silently drop them."""
    return (token.type not in NOT_A_NAME_SEGMENT
            and token.type not in NAME_LITERAL_TOKEN_TYPES
            and token.type != Token.EOF)


def name_text(token: Token) -> str:
    """Upper-cased identifier text for a name-shaped token: token.text.upper()
    for any ordinary identifier, same as every call site used to compute
    inline before this helper existed -- except a delimited (double-quoted)
    identifier, whose surrounding '"' characters are stripped first, so
    "MyTable" normalizes to MYTABLE like any other reference to the same
    object instead of carrying literal quote characters into every
    downstream table/column/alias name."""
    text = token.text
    if token.type == Db2Lexer.DOUBLE_QUOTE_ID and len(text) >= 2:
        text = text[1:-1]
    return text.upper()
