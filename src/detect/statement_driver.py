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
     Tier 2 (only if nothing in Tier 1 made progress): search_condition()
             right after the next WHERE/ON
     Tier 3 (safety valve): skip exactly one token, retry
"""

from antlr4 import CommonTokenStream, InputStream
from antlr4.ListTokenSource import ListTokenSource
from antlr4.Token import Token
from antlr4.error.ErrorListener import ErrorListener

from Db2Lexer import Db2Lexer
from Db2Parser import Db2Parser

# Safety valve cap: max loop iterations per chunk, so a pathological chunk
# (e.g. a huge bulk-insert VALUES list the grammar can't make sense of)
# can't spin the resync loop indefinitely.
MAX_ITERATIONS_PER_CHUNK = 200000

# No HAVING token exists in this grammar (checked: not defined in
# Db2Lexer.g4) -- WHERE/ON are the only resync anchors available.
_RESYNC_KEYWORDS = (Db2Lexer.WHERE, Db2Lexer.ON)


class _CollectingErrorListener(ErrorListener):
    def __init__(self):
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append((line, column, msg))


def lex_file(text):
    """Lex the whole file once. Returns (all_tokens, lexer_errors)."""
    lexer = Db2Lexer(InputStream(text))
    lexer.removeErrorListeners()
    err = _CollectingErrorListener()
    lexer.addErrorListener(err)
    stream = CommonTokenStream(lexer)
    stream.fill()
    return stream.tokens, err.errors


def chunk_ranges(all_tokens):
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


def _is_eof_only(all_tokens, rng):
    start, end = rng
    return all(t.type == Token.EOF for t in all_tokens[start:end])


def _make_chunk_stream(all_tokens, start, end):
    """A CommonTokenStream scoped to exactly all_tokens[start:end) (plus
    an auto-synthesized EOF, courtesy of ListTokenSource) -- so a
    DefaultErrorStrategy resync inside this chunk has no tokens outside
    the chunk to escape into."""
    source = ListTokenSource(list(all_tokens[start:end]))
    stream = CommonTokenStream(source)
    stream.fill()
    return stream


def _find_next_resync_point(stream, from_index):
    """Tier 2: index right after the next WHERE/ON at or after from_index
    on the default channel, or None."""
    for i in range(from_index, len(stream.tokens)):
        tok = stream.tokens[i]
        if tok.channel != Token.DEFAULT_CHANNEL:
            continue
        if tok.type in _RESYNC_KEYWORDS:
            return i + 1
    return None


def _try_parse(stream, pos, rule_name):
    """Seek to pos and attempt one parser rule. Returns (tree_or_None,
    consumed_ok) -- consumed_ok is True only if there were zero errors AND
    the stream actually advanced (a returned context object alone does
    not mean the parse was clean -- ANTLR can silently error-recover
    through a rule and still return *something*)."""
    stream.seek(pos)
    parser = Db2Parser(stream)
    parser.removeErrorListeners()
    err = _CollectingErrorListener()
    parser.addErrorListener(err)
    tree = getattr(parser, rule_name)()
    ok = not err.errors and stream.index > pos
    return (tree if ok else None), ok


def parse_chunk(all_tokens, start, end, visitor, token_scan_fallback,
                 max_iterations=MAX_ITERATIONS_PER_CHUNK, extra_visitors=()):
    """Run the tiered resync loop over one chunk. `visitor` is an
    ExtractorVisitor (or compatible) -- `visitor.visit(tree)` is called
    for every fragment successfully parsed via Tier 1's structural
    candidates. `token_scan_fallback(stream, pos)` implements Tier 1's
    token-scan candidate (see supplementary_checks.py) and returns
    `(consumed_count, commit_or_None)` -- `commit` is only invoked if this
    candidate wins the race (see module docstring for why a plain
    "try structural parses first, fall back to token-scan last" ordering
    is not reliable here). `max_iterations` is the per-chunk safety-valve
    cap (see MAX_ITERATIONS_PER_CHUNK); exposed as a parameter so callers
    (ultimately --max-chunk-iterations on the CLI) can tune it.
    `extra_visitors` -- additional visitor(s) (e.g. reference_visitor.py's
    ReferenceVisitor) that also get `.visit(tree)` called on every tree
    this chunk's tiered loop successfully commits, alongside `visitor`;
    see parse_file's `pre_chunk_hook` for how these get constructed."""
    stream = _make_chunk_stream(all_tokens, start, end)
    n_tokens = len(stream.tokens)
    pos = 0
    iterations = 0

    while pos < n_tokens and stream.tokens[pos].type != Token.EOF:
        iterations += 1
        if iterations > max_iterations:
            break

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
            elif best_kind == "stmt":
                visitor.visit(stmt_tree)
                for extra in extra_visitors:
                    extra.visit(stmt_tree)
            else:
                scan_commit()
            pos += best_consumed
            continue

        # Tier 2 (only reached if nothing in Tier 1 made any progress):
        # scan forward for the next WHERE/ON and try search_condition()
        # from right after it.
        resync_at = _find_next_resync_point(stream, pos)
        if resync_at is not None:
            tree, ok = _try_parse(stream, resync_at, "search_condition")
            if ok:
                visitor.visit(tree)
                for extra in extra_visitors:
                    extra.visit(tree)
                pos = stream.index
                continue

        # Tier 3: safety valve -- guaranteed progress
        pos += 1


def parse_file(text, visitor, token_scan_fallback,
               max_iterations_per_chunk=MAX_ITERATIONS_PER_CHUNK,
               pre_chunk_hook=None):
    """Top-level entry point: lex once, split into chunks, run the tiered
    driver over each. Returns (all_tokens, lexer_errors) so callers (e.g.
    scan.py for in_comment findings) can reuse the same token stream for
    comment-token inspection without re-lexing.
    `pre_chunk_hook(all_tokens, start, end) -> tuple_of_extra_visitors`,
    if given, is called once per chunk *before* that chunk's tiered loop
    runs, using the same already-lexed `all_tokens`/chunk range (no
    re-lexing) -- lets a caller do its own tree-free token-scan work (e.g.
    table_scan.py's scan_query_blocks) and construct a visitor that closes
    over that chunk's just-computed state (e.g. reference_visitor.py's
    ReferenceVisitor) to be run alongside `visitor` for this chunk only.
    comment_rescan.py's own parse_file() calls don't pass this, so
    reference/relation extraction inside comments is out of scope, a
    known limitation."""
    all_tokens, lexer_errors = lex_file(text)
    for start, end in chunk_ranges(all_tokens):
        extra_visitors = pre_chunk_hook(all_tokens, start, end) if pre_chunk_hook else ()
        parse_chunk(all_tokens, start, end, visitor, token_scan_fallback,
                    max_iterations=max_iterations_per_chunk,
                    extra_visitors=extra_visitors)
    return all_tokens, lexer_errors
