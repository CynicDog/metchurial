# -*- coding: utf-8 -*-
"""Re-scans each hidden comment token's own isolated text for the same
sensitive-column comparison detection constructs the live-code driver looks
for, tagging them in_comment=Y -- commented-out or example code can still
leak real data.

Hidden comment tokens are already cleanly delimited by the lexer (a
comment token's text can never span into or absorb subsequent live code --
see statement_driver.py's module docstring), so each comment is just its
own small, fully isolated re-parse -- no discard-and-resume search needed.
This grammar's block comments, `SQL_COMMENT`, support nesting -- a nested
`/* */` inside the outer one becomes its own hidden token when the
stripped inner text is re-lexed, so `rescan_comments` recurses into each
comment's own inner tokens to catch a finding sitting inside a
comment-within-a-comment too, not just the outermost layer.

Known-name matching is *not* handled here -- it isn't a parsing
concern (see engine.py), so it runs as a single whole-file regex pass over
raw text there, with in_comment derived from the same comment-token spans
this module also uses.
"""

from __future__ import annotations

from typing import Callable

from antlr4.Token import Token

from metchurial._generated.Db2Lexer import Db2Lexer
from metchurial.detect.extractor_visitor import ExtractorVisitor
from metchurial.parsing.statement_driver import MAX_ITERATIONS_PER_CHUNK, parse_file
from metchurial.detect.supplementary_checks import make_token_scan_fallback

_COMMENT_TOKEN_TYPES = (Db2Lexer.LINE_COMMENT, Db2Lexer.SQL_COMMENT)


def comment_tokens(all_tokens: list[Token]) -> list[Token]:
    return [t for t in all_tokens
            if t.channel == Token.HIDDEN_CHANNEL and t.type in _COMMENT_TOKEN_TYPES]


def _strip_comment_markers(token: Token) -> str | None:
    """Return the comment's inner text (markers removed) -- re-lexing the
    raw token text as-is would just re-match the leading '--'/'/*' as
    another comment and swallow everything, producing nothing to parse."""
    text = token.text
    if token.type == Db2Lexer.LINE_COMMENT:
        inner = text[2:]
        for trailing in ("\r\n", "\n", "\r"):
            if inner.endswith(trailing):
                inner = inner[:-len(trailing)]
                break
        return inner
    if token.type == Db2Lexer.SQL_COMMENT:
        inner = text[2:]
        if inner.endswith("*/"):
            inner = inner[:-2]
        return inner
    return None


def rescan_comments(all_tokens: list[Token], columns: list[str],
                     sink: Callable[[str, str, str, int, str, int, int], None],
                     max_iterations_per_chunk: int = MAX_ITERATIONS_PER_CHUNK) -> None:
    """sink: callable(column, operator, value, line, in_comment,
    start_offset, end_offset) -- note the extra in_comment arg vs.
    ExtractorVisitor's own sink shape, since every finding produced here
    is tagged "Y". start_offset/end_offset use the same 0-based
    inclusive-inclusive convention as ExtractorVisitor's sink, translated
    all the way back to whatever coordinate system the *original* caller's
    `all_tokens` used (see base_offset below). `max_iterations_per_chunk`
    is threaded through to each nested parse_file() call so a recursive
    re-scan respects the same runtime cap as the top-level driver."""
    for tok in comment_tokens(all_tokens):
        inner_text = _strip_comment_markers(tok)
        if not inner_text or not inner_text.strip():
            continue
        base_line = tok.line  # this comment's own start line, in whatever
                               # coordinate system `all_tokens` uses (the
                               # original file for a top-level call, or an
                               # enclosing comment's own inner text for a
                               # recursive one -- see nested_sink below)
        # This comment's own inner_text character 0, translated into
        # whatever coordinate system `tok` itself lives in -- both
        # LINE_COMMENT ('--') and SQL_COMMENT ('/*') markers stripped by
        # _strip_comment_markers are exactly 2 characters, so tok.start+2
        # is inner_text's own offset 0 in that outer system. Same role as
        # base_line, just for character offsets instead of line numbers.
        base_offset = tok.start + 2

        def relocated_sink(column: str, operator: str, value: str, rel_line: int,
                           rel_start: int, rel_end: int,
                           _base: int = base_line, _base_offset: int = base_offset) -> None:
            # SQL_COMMENTs can span physical lines; LINE_COMMENTs never do
            # (by construction), so rel_line is always 1 there.
            sink(column, operator, value, _base + (rel_line - 1), "Y",
                _base_offset + rel_start, _base_offset + rel_end)

        visitor = ExtractorVisitor(columns, relocated_sink)
        fallback = make_token_scan_fallback(columns, relocated_sink)
        inner_tokens, _inner_lex_errors = parse_file(
            inner_text, visitor, fallback,
            max_iterations_per_chunk=max_iterations_per_chunk)

        # Recurse for comments nested inside this comment's own text. The
        # nested call's own line numbers/offsets are relative to *this*
        # comment's inner_text (line 1 char 0 = this comment's own first
        # character), so translating them up to whatever coordinate system
        # `sink` expects is the same +base_line-1 / +base_offset shift as
        # above -- composes correctly through arbitrarily many nesting
        # levels since each recursion level closes over its own base_line/
        # base_offset.
        def nested_sink(column: str, operator: str, value: str,
                        line_within_this_comment: int, _in_comment: str,
                        start_within_this_comment: int, end_within_this_comment: int,
                        _base: int = base_line, _base_offset: int = base_offset) -> None:
            sink(column, operator, value, _base + (line_within_this_comment - 1), "Y",
                _base_offset + start_within_this_comment, _base_offset + end_within_this_comment)

        rescan_comments(inner_tokens, columns, nested_sink,
                        max_iterations_per_chunk=max_iterations_per_chunk)
