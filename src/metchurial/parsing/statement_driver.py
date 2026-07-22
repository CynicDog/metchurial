# -*- coding: utf-8 -*-
"""Chunked, tiered-resync statement driver: parses a file's SQL by lexing
it once, splitting into statement-sized chunks, and racing several parse
strategies against each chunk rather than relying on one top-level grammar
rule and ANTLR's default error recovery.

Parsing a whole file with one top-level `db2_file` rule and hoping ANTLR's
default error recovery degrades gracefully is not reliable: DB2 SQL you
find in the wild is often exported/kept as loose fragments, not fully
valid, complete statements. Instead:

1. Lex the whole file once (single source of truth for comment/live-code
   channel boundaries, regardless of what the parser does afterward).
2. Split the default-channel tokens into chunks at top-level ';' (paren
   depth 0). Hidden comment tokens never influence this split, so a stray
   ')' or ';' left inside a malformed comment (see fixtures
   09_paren_list_boundary.sql/13_comment_escape_recovery.sql) can't
   affect chunking by construction.
3. Per chunk, run a tiered resync loop, scoped so a DefaultErrorStrategy
   resync can never escape into a different top-level statement (the
   chunk's own sub-stream has no tokens outside itself to escape into):
     Tier 1: sql_statement(), search_condition(), and the narrow
             token-scan fallback (supplementary_checks.py) are *all*
             tried directly at the current position -- take whichever
             consumes the most tokens (ties broken toward the structural
             parses). Racing all three, rather than treating the
             token-scan as a strict last resort, matters concretely: e.g.
             `ACCT_ID ('0000001')` has no grammar path at all (see
             extractor_visitor.py's docstring), but sql_statement() alone
             *does* accept the bare identifier "ACCT_ID" as a trivially
             complete statement -- if that were tried first and committed
             before the token-scan got a chance to see "ACCT_ID (" as a
             unit, the token-scan would never get the chance, since the
             winning tier's consumed tokens are gone from the remaining
             input. Only racing by actual consumed-token-count reliably
             picks the token-scan in that case (3 tokens: ACCT_ID, (,
             '0000001') over the bogus statement match (1 token: ACCT_ID).
     Tier 2 (only if nothing in Tier 1 made progress): parse from the
             next resync anchor -- search_condition() right after the
             next WHERE/ON/HAVING, or sql_statement() at the next nested
             SELECT, whichever comes first
     Tier 3 (safety valve): skip exactly one token, retry
"""

from __future__ import annotations

import bisect
from typing import Any, Callable

from antlr4 import CommonTokenStream, InputStream
from antlr4.ListTokenSource import ListTokenSource
from antlr4.Token import Token
from antlr4.atn.PredictionMode import PredictionMode
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.ErrorStrategy import BailErrorStrategy
from antlr4.error.Errors import ParseCancellationException

from metchurial._generated.Db2Lexer import Db2Lexer
from metchurial._generated.Db2Parser import Db2Parser
from metchurial.models.options import DEFAULT_MAX_CHUNK_ITERATIONS
from metchurial.models.parse_stats import ParseStats

# Runtime bound, not a termination guarantee: the resync loop always
# advances (Tier 3 skips at least one token per iteration), but each
# iteration can cost up to two full parse attempts, so an enormous
# unparseable chunk (e.g. a huge bulk-insert VALUES list the grammar can't
# make sense of) would otherwise take quadratic time. Tunable via
# --max-chunk-iterations / ScanOptions.max_chunk_iterations; the value
# itself lives with every other scan default in models/options.py.
MAX_ITERATIONS_PER_CHUNK = DEFAULT_MAX_CHUNK_ITERATIONS

_RESYNC_KEYWORDS = (Db2Lexer.WHERE, Db2Lexer.ON, Db2Lexer.HAVING)


class _CollectingErrorListener(ErrorListener):
    def __init__(self) -> None:
        self.errors: list[tuple[int, int, str]] = []

    def syntaxError(self, recognizer: Any, offendingSymbol: Any, line: int, column: int, msg: str, e: Any) -> None:
        self.errors.append((line, column, msg))


def lex_file(text: str) -> tuple[list[Token], list[tuple[int, int, str]]]:
    """Lex the whole file once. Returns (all_tokens, lexer_errors)."""
    lexer = Db2Lexer(InputStream(text))
    lexer.removeErrorListeners()
    err = _CollectingErrorListener()
    lexer.addErrorListener(err)
    stream = CommonTokenStream(lexer)
    stream.fill()
    return stream.tokens, err.errors


def chunk_ranges(all_tokens: list[Token]) -> list[tuple[int, int]]:
    """[start, end) index ranges into all_tokens, split at top-level ';'
    (paren depth 0, tracked over default-channel tokens only). Depth is
    clamped at a floor of 0 so a genuinely unmatched ')' left in live code
    (fixture 09_paren_list_boundary.sql line 4) can't drive tracking
    negative and corrupt a later, legitimate IN(...) in the same chunk."""
    ranges = []
    depth = 0
    chunk_start = 0
    n = len(all_tokens)
    for i, tok in enumerate(all_tokens):
        if tok.channel != Token.DEFAULT_CHANNEL:
            continue
        if tok.type == Db2Lexer.LEFT_RND_BKT:
            depth += 1
        elif tok.type == Db2Lexer.RIGHT_RND_BKT:
            depth = max(0, depth - 1)
        elif tok.type == Db2Lexer.SEMI and depth == 0:
            ranges.append((chunk_start, i + 1))
            chunk_start = i + 1
    if chunk_start < n:
        ranges.append((chunk_start, n))
    # drop any range that's EOF-only (or otherwise has no real content)
    return [r for r in ranges if r[1] > r[0] and not _is_eof_only(all_tokens, r)]


def _is_eof_only(all_tokens: list[Token], rng: tuple[int, int]) -> bool:
    start, end = rng
    return all(t.type == Token.EOF for t in all_tokens[start:end])


def _make_chunk_stream(all_tokens: list[Token], start: int, end: int) -> CommonTokenStream:
    """A CommonTokenStream scoped to exactly all_tokens[start:end) (plus
    an auto-synthesized EOF, courtesy of ListTokenSource) -- so a
    DefaultErrorStrategy resync inside this chunk has no tokens outside
    the chunk to escape into."""
    source = ListTokenSource(list(all_tokens[start:end]))
    stream = CommonTokenStream(source)
    stream.fill()
    return stream


def _resync_anchors(stream: CommonTokenStream) -> list[tuple[int, str]]:
    """Every Tier 2 anchor in `stream`, in one linear pass over the whole
    chunk -- precomputed once per chunk rather than re-scanned from the
    current position on every Tier 3 single-token retry. A chunk with few
    or no anchors (e.g. a large multi-row VALUES(...) list, which has no
    WHERE/ON/HAVING/nested-SELECT to anchor on at all) used to make
    _find_next_resync_point rescan all the way to the end of the chunk on
    every one of Tier 3's pos += 1 retries -- O(remaining tokens) repeated
    once per token is O(n^2) in chunk size, the difference between
    milliseconds and minutes on a large bulk INSERT.

    Stored positions already encode each anchor's own offset (a WHERE/ON/
    HAVING keyword's own index + 1, a SELECT's own index unmodified), and
    are appended in strictly non-decreasing order since both offsets are
    monotonic in the token index being scanned -- so the result is
    already sorted by position, ready for bisecting in
    _find_next_resync_point below."""
    anchors = []
    for i, tok in enumerate(stream.tokens):
        if tok.channel != Token.DEFAULT_CHANNEL:
            continue
        if tok.type in _RESYNC_KEYWORDS:
            anchors.append((i + 1, "search_condition"))
        elif tok.type == Db2Lexer.SELECT:
            anchors.append((i, "sql_statement"))
    return anchors


def _find_next_resync_point(anchor_positions: list[int], anchors: list[tuple[int, str]],
                            from_index: int) -> tuple[int, str] | None:
    """Tier 2 anchor: whichever comes first of the next WHERE/ON/HAVING
    (parse a search_condition right after it) or the next SELECT strictly
    past from_index (parse a sql_statement at it -- a nested SELECT
    inside an otherwise-unparseable statement, e.g. a CTE body whose
    declared name is a reserved word, is recovered whole this way instead
    of being leapfrogged by a farther WHERE/ON jump; SELECT at from_index
    itself is excluded since Tier 1 just proved it doesn't parse).
    `anchor_positions`/`anchors`: _resync_anchors(stream)'s result, plus
    its own positions pulled into a parallel list for bisect. Returns
    (position, rule_name), or None."""
    idx = bisect.bisect_left(anchor_positions, from_index)
    # a SELECT anchor's position is its own token index (no +1 offset
    # the way a WHERE/ON/HAVING anchor has), so an exact match at
    # from_index is the one Tier 1 already just proved doesn't parse --
    # skip it. A WHERE/ON/HAVING anchor can never land on this exact
    # exclusion, since its stored position is already one past its own
    # token index.
    if idx < len(anchors) and anchors[idx] == (from_index, "sql_statement"):
        idx += 1
    return anchors[idx] if idx < len(anchors) else None


def _try_parse(stream: CommonTokenStream, pos: int, rule_name: str) -> tuple[Any, bool]:
    """Seek to pos and attempt one parser rule. Returns (tree_or_None,
    consumed_ok) -- consumed_ok is True only if there were zero errors AND
    the stream actually advanced (a returned context object alone does
    not mean the parse was clean -- ANTLR can silently error-recover
    through a rule and still return *something*).

    predictionMode is pinned to SLL rather than ANTLR's default LL: this
    grammar's flat `predicate` rule (see parsing/predicates.py) has many
    alternatives sharing a long `expression` prefix, so default LL falls
    back to full-context prediction (execATNWithFullContext) at each list
    element to resolve the ambiguity -- fine for a handful of elements,
    but a WHERE col IN (...) with tens of thousands of literals turns
    that into tens of thousands of full-context predictions, the
    difference between single-digit milliseconds and hours for one
    statement. SLL is strictly weaker only at resolving which of several
    *simultaneously valid* alternatives to prefer when the grammar is
    genuinely ambiguous at that point (which alternative wins there makes
    no difference to what gets extracted here); it does not accept input
    LL would reject, and detects genuine syntax errors identically -- see
    ANTLR's own recommended "two-stage parsing" strategy, which this
    mirrors. Any input SLL genuinely can't make sense of still comes back
    as ok=False here, same as any other syntax error, and falls through
    to this module's own Tier 2/Tier 3 resync exactly as before.

    errHandler is likewise pinned to BailErrorStrategy rather than
    ANTLR's default: `ok` is already False on *any* reported error
    (`not err.errors`), so whatever DefaultErrorStrategy's internal
    recover()/consumeUntil() would have gone on to do after the first
    error is guaranteed-discarded work -- for a rule with many small
    internal mismatches (e.g. a multi-row VALUES clause the grammar
    doesn't fully cover per row), that discarded recovery work is
    exactly what turns one syntax error into thousands of token-by-token
    resync attempts, and one file's scan into minutes. BailErrorStrategy
    still reports the error to `err` (DefaultErrorStrategy.reportError
    isn't overridden, only recover()) before raising
    ParseCancellationException, so `ok`'s value is identical either way
    -- only the cost of reaching it changes."""
    stream.seek(pos)
    parser = Db2Parser(stream)
    parser._interp.predictionMode = PredictionMode.SLL
    parser._errHandler = BailErrorStrategy()
    parser.removeErrorListeners()
    err = _CollectingErrorListener()
    parser.addErrorListener(err)
    try:
        tree = getattr(parser, rule_name)()
    except ParseCancellationException:
        return None, False
    ok = not err.errors and stream.index > pos
    return (tree if ok else None), ok


def parse_chunk(all_tokens: list[Token], start: int, end: int, visitor: Any,
                 token_scan_fallback: Callable[[CommonTokenStream, int], tuple[int, Callable[[], None] | None]],
                 max_iterations: int = MAX_ITERATIONS_PER_CHUNK,
                 extra_visitors: tuple[Any, ...] = (),
                 stats: ParseStats | None = None) -> None:
    """Run the tiered resync loop over one chunk. `visitor` is an
    ExtractorVisitor (or compatible) -- `visitor.visit(tree)` is called
    for every fragment successfully parsed via Tier 1's structural
    candidates. `token_scan_fallback(stream, pos)` implements Tier 1's
    token-scan candidate (see supplementary_checks.py) and returns
    `(consumed_count, commit_or_None)` -- `commit` is only invoked if this
    candidate wins the race (see module docstring for why a plain
    "try structural parses first, fall back to token-scan last" ordering
    is not reliable here). `max_iterations` is the per-chunk runtime cap
    (see MAX_ITERATIONS_PER_CHUNK); exposed as a parameter so callers
    (ultimately --max-chunk-iterations on the CLI) can tune it.
    `extra_visitors` -- additional visitor(s) (e.g. reference_visitor.py's
    ReferenceVisitor) that also get `.visit(tree)` called on every tree
    this chunk's tiered loop successfully commits, alongside `visitor`;
    see parse_file's `pre_chunk_hook` for how these get constructed.
    `stats`, if given, is updated in place with this chunk's iteration
    count and how each iteration resolved -- see --verbose's summary line
    (models/parse_stats.py); a caller not interested in that (e.g.
    comment_rescan.py) simply omits it, at zero cost."""
    stream = _make_chunk_stream(all_tokens, start, end)
    n_tokens = len(stream.tokens)
    pos = 0
    iterations = 0
    resync_anchors = _resync_anchors(stream)
    resync_anchor_positions = [a[0] for a in resync_anchors]
    if stats is not None:
        stats.chunks += 1

    while pos < n_tokens and stream.tokens[pos].type != Token.EOF:
        iterations += 1
        if iterations > max_iterations:
            break
        if stats is not None:
            stats.iterations += 1

        # Normalize pos to the next real (default-channel) token before
        # racing the three candidates. sql_statement()/search_condition()
        # transparently skip past a hidden-channel starting position (ANTLR
        # auto-skips hidden tokens when a rule fetches its next token via
        # LT()/consume()), but token_scan_fallback does not -- it only
        # looks at stream.tokens[pos] directly. Without this normalization,
        # landing pos exactly on a hidden whitespace token (which happens
        # routinely once tokens start getting consumed in non-token-count-1
        # chunks) makes the token-scan candidate report 0 by default even
        # when the very next real token is a sensitive column, letting a
        # bogus short sql_statement() match win the race purely because its
        # competitor never got a fair look.
        while pos < n_tokens and stream.tokens[pos].channel != Token.DEFAULT_CHANNEL:
            pos += 1
        if pos >= n_tokens or stream.tokens[pos].type == Token.EOF:
            break

        # Tier 1: race all three candidates at the current position, take
        # whichever consumes the most tokens. Priority breaks ties (higher
        # wins): search_condition() > sql_statement() > token-scan --
        # structural parses are preferred when equally long, since the
        # token-scan is a narrow last resort by design (see
        # supplementary_checks.py).
        stmt_tree, stmt_ok = _try_parse(stream, pos, "sql_statement")
        stmt_consumed = (stream.index - pos) if stmt_ok else 0

        cond_tree, cond_ok = _try_parse(stream, pos, "search_condition")
        cond_consumed = (stream.index - pos) if cond_ok else 0

        scan_consumed, scan_commit = token_scan_fallback(stream, pos)

        candidates = [
            (cond_consumed, 3, "cond"),
            (stmt_consumed, 2, "stmt"),
            (scan_consumed, 1, "scan"),
        ]
        best_consumed, _priority, best_kind = max(candidates)

        if best_consumed > 0:
            if best_kind == "cond":
                visitor.visit(cond_tree)
                for extra in extra_visitors:
                    extra.visit(cond_tree)
                if stats is not None:
                    stats.tier1_structural += 1
            elif best_kind == "stmt":
                visitor.visit(stmt_tree)
                for extra in extra_visitors:
                    extra.visit(stmt_tree)
                if stats is not None:
                    stats.tier1_structural += 1
            else:
                scan_commit()
                if stats is not None:
                    stats.tier1_token_scan += 1
            pos += best_consumed
            continue

        # Tier 2 (only reached if nothing in Tier 1 made any progress):
        # scan forward for the next resync anchor and parse from it.
        resync = _find_next_resync_point(resync_anchor_positions, resync_anchors, pos)
        if resync is not None:
            resync_at, resync_rule = resync
            tree, ok = _try_parse(stream, resync_at, resync_rule)
            if ok:
                visitor.visit(tree)
                for extra in extra_visitors:
                    extra.visit(tree)
                pos = stream.index
                if stats is not None:
                    stats.tier2_resync += 1
                continue

        # Tier 3: safety valve -- guaranteed progress
        pos += 1
        if stats is not None:
            stats.tier3_skip += 1


def parse_file(text: str, visitor: Any,
               token_scan_fallback: Callable[[CommonTokenStream, int], tuple[int, Callable[[], None] | None]],
               max_iterations_per_chunk: int = MAX_ITERATIONS_PER_CHUNK,
               pre_chunk_hook: Callable[[list[Token], int, int], tuple[Any, ...]] | None = None,
               lexed: tuple[list[Token], list[tuple[int, int, str]]] | None = None,
               stats: ParseStats | None = None,
               ) -> tuple[list[Token], list[tuple[int, int, str]]]:
    """Top-level entry point: lex once, split into chunks, run the tiered
    driver over each. Returns (all_tokens, lexer_errors) so callers (e.g.
    engine.py for in_comment findings) can reuse the same token stream for
    comment-token inspection without re-lexing.
    `lexed`, if given, is a prior lex_file(text) result -- an
    (all_tokens, lexer_errors) tuple for this same `text` -- and skips the
    internal lex (lexing is deterministic and nothing here mutates the
    token list, so the result is identical either way).
    `pre_chunk_hook(all_tokens, start, end) -> tuple_of_extra_visitors`,
    if given, is called once per chunk *before* that chunk's tiered loop
    runs, using the same already-lexed `all_tokens`/chunk range (no
    re-lexing) -- lets a caller do its own tree-free token-scan work (e.g.
    table_scan.py's scan_query_blocks) and construct a visitor that closes
    over that chunk's just-computed state (e.g. reference_visitor.py's
    ReferenceVisitor) to be run alongside `visitor` for this chunk only.
    comment_rescan.py's own parse_file() calls don't pass this, so
    reference/relation extraction inside comments is out of scope, a
    known limitation. `stats`, if given, accumulates across every chunk
    in the file -- see parse_chunk."""
    all_tokens, lexer_errors = lexed if lexed is not None else lex_file(text)
    for start, end in chunk_ranges(all_tokens):
        extra_visitors = pre_chunk_hook(all_tokens, start, end) if pre_chunk_hook else ()
        parse_chunk(all_tokens, start, end, visitor, token_scan_fallback,
                    max_iterations=max_iterations_per_chunk,
                    extra_visitors=extra_visitors, stats=stats)
    return all_tokens, lexer_errors
