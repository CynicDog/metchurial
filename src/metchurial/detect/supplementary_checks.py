# -*- coding: utf-8 -*-
"""Tier 3 last-resort token-scan fallback for statement_driver.py.

Reached when neither sql_statement() nor a directly- or WHERE/ON-anchored
search_condition() could make any progress at the current position. This
is not a rare edge case: this Db2-specific grammar (antlr/grammars-v4's
sql/db2) has no parser-level path at all for two constructs sensitive-column
comparison detection needs to cover (see extractor_visitor.py's module
docstring for why):

1. A bare '(' before a literal (`ACCT_ID ('0000001')`, a DB2/embedded-SQL
   quirk, likely a dropped IN) -- `expression` requires a real
   `function_invocation`, not a bare identifier immediately followed by a
   parenthesized argument, so this is a hard parse failure, not a
   structural shape the visitor can recognize.
2. A double-quoted literal (`ACCT_ID = "0000079"`) -- `DOUBLE_QUOTE_ID` is
   a real lexer token but is never referenced anywhere in the parser
   grammar, so it can never be consumed by any rule.

Both are caught here instead, by scanning raw tokens directly (so no
digit-boundary/quote-escaping tricks are needed -- token boundaries are
already correct by construction, same as the structural path).
"""

from __future__ import annotations

from typing import Callable, Iterable

from antlr4 import CommonTokenStream
from antlr4.Token import Token

from metchurial._generated.Db2Lexer import Db2Lexer

_LITERAL_TOKEN_TYPES = {
    Db2Lexer.STRING_LITERAL,
    Db2Lexer.DECIMAL_LITERAL,
    Db2Lexer.FLOAT_LITERAL,
    Db2Lexer.REAL_LITERAL,
    Db2Lexer.DOUBLE_QUOTE_ID,  # double-quoted literal: unreachable by any parser rule (see module docstring)
}

_OPERATOR_STARTER_TOKEN_TYPES = {
    Db2Lexer.EQ,
    Db2Lexer.LT,
    Db2Lexer.GT,
    Db2Lexer.LE,
    Db2Lexer.GE,
    Db2Lexer.LTGT,
    Db2Lexer.LEFT_RND_BKT,
    Db2Lexer.IN,
    Db2Lexer.LIKE,
    Db2Lexer.BETWEEN,
    Db2Lexer.NOT,
}

# The only tokens that legitimately follow a leading NOT as the second
# half of one compound operator ("NOT IN", "NOT LIKE", "NOT BETWEEN"),
# not a second, unrelated comparison -- see the "wandered into a new,
# unrelated comparison" guard below, which would otherwise bail out on
# this exact token, right after NOT, every single time (both NOT and
# IN/LIKE/BETWEEN are themselves _OPERATOR_STARTER_TOKEN_TYPES members).
_NOT_COMPOUND_FOLLOWERS = {Db2Lexer.IN, Db2Lexer.LIKE, Db2Lexer.BETWEEN}

# How far past the column token to look for a comparable literal before
# giving up -- bounded so a pathological chunk can't turn this into an
# unbounded scan.
_MAX_LOOKAHEAD = 8


def _default_channel_indices(stream: CommonTokenStream, start: int, limit: int) -> list[int]:
    """Indices of up to `limit` default-channel tokens at or after
    `start`, in order."""
    out = []
    for i in range(start, len(stream.tokens)):
        if len(out) >= limit:
            break
        if stream.tokens[i].channel == Token.DEFAULT_CHANNEL:
            out.append(i)
    return out


def make_token_scan_fallback(
        columns: Iterable[str],
        sink: Callable[[str, str, str, int, int, int], None],
) -> Callable[[CommonTokenStream, int], tuple[int, Callable[[], None] | None]]:
    """columns: iterable of sensitive column names (any case). sink:
    callable(column, operator, value, line, start_offset, end_offset),
    same shape as ExtractorVisitor's -- start_offset/end_offset are the
    literal token's own 0-based inclusive-inclusive character span, so
    callers can locate/replace the exact literal span in the original
    source (e.g. for masking). Returns a `(stream, pos) ->
    (consumed_count, commit_or_None)` callable.

    Splitting "how much would this consume" from "actually emit the
    finding" matters because statement_driver.py races this tier against
    sql_statement()/search_condition() by consumed-token-count *before*
    deciding a winner (see its module docstring for why: a bare-identifier
    "statement" match can otherwise steal the very token this tier needs
    to see, e.g. `ACCT_ID ('0000001')` -- sql_statement() happily accepts
    just "ACCT_ID" as a trivially complete statement and consumes it
    first). If this function emitted immediately, evaluating it as part of
    that race would risk emitting a finding for a tier that then loses the
    race to a different tier. `commit` is a zero-arg callable the driver
    only invokes once it has actually chosen this tier as the winner."""
    upper_columns = {c.upper() for c in columns}

    def fallback(stream: CommonTokenStream,
                 pos: int) -> tuple[int, Callable[[], None] | None]:
        tok = stream.tokens[pos]
        if tok.channel != Token.DEFAULT_CHANNEL:
            return 0, None
        if tok.type == Db2Lexer.DOUBLE_QUOTE_ID:
            name = tok.text[1:-1].upper()
        else:
            name = tok.text.upper()
        if name not in upper_columns:
            return 0, None

        window = _default_channel_indices(stream, pos + 1, _MAX_LOOKAHEAD)
        if not window:
            return 0, None
        if stream.tokens[window[0]].type not in _OPERATOR_STARTER_TOKEN_TYPES:
            return 0, None

        # Track paren balance across the whole window and remember the
        # depth at which the first literal appeared. A literal found
        # *inside* an open '(' (e.g. the bare-'(' quirk, or an IN (...))
        # is only trusted if that paren actually closes somewhere in the
        # window -- otherwise a malformed/truncated fragment left behind
        # in a comment (e.g. "ctrt_no in ('0000099'" with no closing ')'
        # anywhere) would match on proximity alone and produce a false
        # finding.
        #
        # Also stop (untrusted, no match) on an AND/OR or a *second*
        # operator-starter token at depth 0 before any literal --
        # otherwise this window can walk straight through an unrelated
        # second comparison and misattribute its literal to the current
        # column, with a garbled "operator" that's really a concatenation
        # of both comparisons' tokens. E.g. for `a.item_no = b.item_no AND
        # item_flag = 'X'`, if the structural parser fails elsewhere in
        # the same predicate and this fallback gets raced at the bare
        # `item_no` token, an unguarded window would walk past "= B .
        # ITEM_NO AND ITEM_FLAG" and report 'X' as ITEM_NO's own value,
        # with that whole span as the "operator". This fallback's
        # two real, narrow use cases (bare '(' before a literal, a
        # double-quoted literal right after a normal operator) always
        # have their literal immediately or very shortly after the
        # *single* operator run that starts the window -- never across an
        # intervening AND/OR or a second, unrelated comparison.
        #
        # Also reject if a '(' is immediately preceded by anything other
        # than the anchor column token itself or the operator run --
        # otherwise a `(` that actually opens some OTHER construct's own
        # argument/grouping list (most commonly a function call whose name
        # has no function_invocation grammar path, e.g. `RRNO LIKE
        # CONCAT('%', '02291')` -- CONCAT lexes as its own reserved
        # operator-keyword token here, not a plain ID, so it can never
        # parse as function_invocation, and the whole predicate falls back
        # to this tier) would have its first *argument* ('%')
        # misattributed to the outer comparison as if it were the actual
        # right-hand value, purely because the paren it sits inside
        # happens to close before the window ends. A function's return
        # value being compared is never a hardcoded literal -- same as
        # when the structural path parses that call cleanly and correctly
        # reports no finding for it.
        depth = 0
        literal_idx = None
        literal_depth = None
        prev_token = tok  # the anchor column token, immediately before window[0]
        for pos_in_window, idx in enumerate(window):
            candidate = stream.tokens[idx]
            if candidate.type == Db2Lexer.LEFT_RND_BKT:
                if prev_token is not tok and prev_token.type not in _OPERATOR_STARTER_TOKEN_TYPES:
                    return 0, None  # '(' belongs to some other construct's own arg/grouping list
                depth += 1
            elif candidate.type == Db2Lexer.RIGHT_RND_BKT:
                depth -= 1
                if depth < 0:
                    return 0, None  # unbalanced close -- untrustworthy fragment
            elif candidate.type in _LITERAL_TOKEN_TYPES and literal_idx is None:
                literal_idx = idx
                literal_depth = depth
            elif literal_idx is None and depth == 0 and pos_in_window > 0 and (
                candidate.type in (Db2Lexer.AND, Db2Lexer.OR)
                or candidate.type in _OPERATOR_STARTER_TOKEN_TYPES
            ) and not (prev_token.type == Db2Lexer.NOT
                      and candidate.type in _NOT_COMPOUND_FOLLOWERS):
                return 0, None  # wandered into a new, unrelated comparison
            prev_token = candidate

        if literal_idx is None:
            return 0, None
        if literal_depth > 0 and depth > 0:
            return 0, None  # the paren the literal sat inside never closed

        idx = literal_idx
        candidate = stream.tokens[idx]
        operator_tokens = [stream.tokens[i] for i in window if i < idx]
        operator = " ".join(t.text for t in operator_tokens).strip().upper() or "?"
        value = candidate.text
        line = tok.line
        start_offset = candidate.start
        end_offset = candidate.stop

        def commit(name: str = name, operator: str = operator, value: str = value,
                   line: int = line, start_offset: int = start_offset,
                   end_offset: int = end_offset) -> None:
            sink(name, operator, value, line, start_offset, end_offset)

        return (idx - pos) + 1, commit

    return fallback
