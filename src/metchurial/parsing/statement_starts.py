# -*- coding: utf-8 -*-
"""Statement-boundary inference for files that don't terminate statements
with ';'.

A top-level ';' is DB2 syntax for ending a statement, but it can't be
relied on as *the* delimiter: plenty of real .sql files keep several
standalone queries side by side and are never run as a script -- the
author highlights the query they want and runs the selection, so no
terminator is ever needed. Such a file reaches chunk_ranges() as a single
chunk, which silently fuses N unrelated queries into one statement for
every downstream consumer (the tiered parse, table/JOIN discovery, query
identity, --split-selects).

`subdivide()` recovers the real boundaries. It runs *inside* each
';'-delimited chunk, so a ';' still ends a statement wherever one is
present and a half-punctuated file works either way.

The rule, in full:

    A default-channel token starts a new statement when it is a statement
    keyword (BOUNDARY_KEYWORDS), sits at paren depth 0, is the first
    token on its source line, and the previous default-channel token is
    not one that grammatically demands a query next (SUPPRESS_PREV).

That is all the ordinary file needs -- bare SELECTs, no CTE, no isolation
clause, no ';':

    SELECT ACCT_ID, NM          <- statement 1
    FROM   CUST
    WHERE  STAT = 'A'

    SELECT BAL                  <- statement 2: SELECT, depth 0, line
    FROM   ACCT                    start, prev token is 'A'

FROM/WHERE/GROUP BY/HAVING/ORDER BY/FETCH FIRST/FOR UPDATE/INTO are not
statement keywords, so a normally-formatted multi-line query is never cut
mid-statement.

Two properties make this sound rather than merely heuristic:

1. The lexer has already resolved all quoting. A keyword, ';' or '('
   inside a string literal, a comment, or a "quoted identifier" is part
   of a single STRING_LITERAL / HIDDEN-channel comment / DOUBLE_QUOTE_ID
   token and can never surface as a default-channel token here. So this
   is a pure token-index walk -- no character scanning, no regex.
2. A SELECT statement cannot contain a depth-0 SELECT except after a set
   operator. Every other nested SELECT -- derived table, scalar
   subquery, IN/EXISTS -- is parenthesized, so depth tracking excludes
   it, and the set-operator case is guard G1.

The line-start requirement (rule 3) is the deliberate precision/recall
trade: it eliminates the whole class of false splits from a statement
keyword used mid-line, at the cost of not splitting two queries crammed
onto one physical line. Nobody writes standalone queries that way -- the
workflow this exists for is highlight-a-region-and-run, which is
inherently line-oriented.

The guards below each stop one specific construct from being cut. A
guard only runs when its construct is actually present; a file of plain
SELECTs never reaches any of them.
"""

from __future__ import annotations

from antlr4.Token import Token

from metchurial._generated.Db2Lexer import Db2Lexer

from metchurial.models.statement_boundary import GUARDS, GUARDS_BY_ID, BoundaryGuard
from metchurial.parsing.token_walk import looks_like_name_start, skip_balanced_parens, skip_hidden

__all__ = ["BOUNDARY_KEYWORDS", "SUPPRESS_PREV", "cte_prologue_end", "subdivide"]

# Tokens that can open a statement. Kept deliberately narrow -- a token
# here that also appears mid-statement produces a false split, which is
# strictly worse than a missed one (a missed boundary just reproduces
# today's behavior).
BOUNDARY_KEYWORDS = {
    Db2Lexer.SELECT, Db2Lexer.WITH, Db2Lexer.INSERT, Db2Lexer.UPDATE, Db2Lexer.DELETE,
    Db2Lexer.MERGE, Db2Lexer.CREATE, Db2Lexer.ALTER, Db2Lexer.DROP, Db2Lexer.TRUNCATE,
    Db2Lexer.GRANT, Db2Lexer.REVOKE, Db2Lexer.CALL, Db2Lexer.DECLARE, Db2Lexer.EXPLAIN,
    Db2Lexer.COMMIT, Db2Lexer.ROLLBACK, Db2Lexer.LOCK, Db2Lexer.SET,
}

# Deliberately NOT in BOUNDARY_KEYWORDS, each for a concrete reason:
#   VALUES  -- both a statement and a fullselect ("... UNION VALUES (1)"),
#              and the tail of "INSERT INTO t (a, b)\nVALUES (...)".
#   FETCH   -- "FETCH FIRST n ROWS ONLY" routinely sits on its own line
#              at the end of a SELECT.
#   OPEN / CLOSE / PREPARE / EXECUTE / SAVEPOINT
#           -- rare in the query files this tool scans, and plausible as
#              ordinary column/table names.

# Which guard owns each "previous token means continuation" type, built
# from models/statement_boundary.py's own prev_tokens rather than
# restated here -- so the guard set is data, and a token named there that
# the lexer doesn't define fails loudly at import time instead of
# silently never matching. Currently G1 (set operators) and G2 (a keyword
# that demands a query next).
SUPPRESS_PREV_GUARD: dict[int, BoundaryGuard] = {
    getattr(Db2Lexer, name): guard
    for guard in GUARDS
    for name in guard.prev_tokens
}

# The flat set the rule itself tests against; the map above is only
# consulted to attribute a suppression to the guard that caused it.
SUPPRESS_PREV = frozenset(SUPPRESS_PREV_GUARD)


def cte_prologue_end(tokens: list[Token], with_idx: int, n: int) -> int | None:
    """tokens[with_idx] is WITH. Walks the CTE list that should follow --
    `name [ (col, ...) ] AS ( ... )` repeated over commas -- and returns
    the index of the SELECT that consumes it, or None if the shape
    doesn't validate.

    Returning None is what makes a bare depth-0 WITH safe to ignore
    (guard G5). DB2's isolation clause puts one *inside* a SELECT --
    `SELECT ... WITH UR` / `WITH RS` / `WITH RR` / `WITH CS`
    (Db2Parser.g4 isolation_clause) -- as do `WITH HOLD`, `WITH RETURN`
    and `WITH ORDINALITY`. None of them match `name AS (`, so shape
    validation rejects them without a keyword denylist, and stays correct
    if DB2 grows another `WITH <something>` clause."""
    i = skip_hidden(tokens, with_idx + 1, n)
    while i is not None:
        if tokens[i].type == Db2Lexer.SELECT or not looks_like_name_start(tokens[i]):
            return None
        i = skip_hidden(tokens, i + 1, n)
        if i is not None and tokens[i].type == Db2Lexer.LEFT_RND_BKT:
            # optional column_name_list_paren before AS
            i = skip_hidden(tokens, skip_balanced_parens(tokens, i), n)
        if i is None or tokens[i].type != Db2Lexer.AS:
            return None
        i = skip_hidden(tokens, i + 1, n)
        if i is None or tokens[i].type != Db2Lexer.LEFT_RND_BKT:
            return None
        i = skip_hidden(tokens, skip_balanced_parens(tokens, i), n)
        if i is not None and tokens[i].type == Db2Lexer.COMMA:
            i = skip_hidden(tokens, i + 1, n)
            continue
        break
    if i is None or tokens[i].type != Db2Lexer.SELECT:
        return None
    return i


class _StatementState:
    """What the in-progress statement needs to remember to judge later
    candidates: whether it leads with SELECT (G6, and G3's inverse),
    whether its one free inner SELECT has been spent (G3), and the index
    of the SELECT that closes its own CTE prologue (G4)."""

    __slots__ = ("lead_is_select", "inner_select_used", "cte_select_idx")

    def __init__(self, tokens: list[Token], idx: int, n: int) -> None:
        tok_type = tokens[idx].type
        self.inner_select_used = False
        self.cte_select_idx: int | None = None
        if tok_type == Db2Lexer.SELECT:
            self.lead_is_select = True
        elif tok_type == Db2Lexer.WITH:
            self.cte_select_idx = cte_prologue_end(tokens, idx, n)
            self.lead_is_select = self.cte_select_idx is not None
        else:
            self.lead_is_select = False


def subdivide(tokens: list[Token], start: int, end: int,
              guard_hits: dict[str, int] | None = None) -> list[tuple[int, int]]:
    """[start, end) is one ';'-delimited chunk. Returns the sub-ranges it
    actually contains, in source order -- [(start, end)] unchanged when no
    boundary is inferred, which is the common case for a punctuated file.

    `guard_hits`, if given, is incremented per guard_id (and under
    "line-start") every time a candidate keyword was stopped from
    becoming a boundary -- what --verbose reports, and the evidence for
    which guards are actually load-bearing on a real corpus rather than
    theoretical.

    A committed range ends at the last default-channel token of the
    statement it closes (+1), *not* at the boundary token's own index.
    That leaves the intervening whitespace and comments at the head of the
    following range -- exactly where a ';' leaves them today -- so a
    `-- 2. account lookup` header line above a query travels with that
    query into its split file, and comment_rescan.py's attribution is
    unchanged."""
    first = skip_hidden(tokens, start, end)
    if first is None:
        return [(start, end)]

    ranges: list[tuple[int, int]] = []
    cur = start
    state = _StatementState(tokens, first, end)
    depth = 0
    prev_idx = first
    last_default_idx = first

    i = skip_hidden(tokens, first + 1, end)
    while i is not None:
        tok = tokens[i]
        tok_type = tok.type
        if tok_type == Db2Lexer.LEFT_RND_BKT:
            depth += 1
        elif tok_type == Db2Lexer.RIGHT_RND_BKT:
            # Clamped at 0 for the same reason chunk_ranges clamps: a
            # genuinely unmatched ')' left in live code (fixture
            # 09_paren_list_boundary.sql) must not drive tracking
            # negative and mask every later boundary.
            depth = max(0, depth - 1)

        if depth == 0 and tok_type in BOUNDARY_KEYWORDS:
            stopped_by = _suppressing_guard(tokens, i, end, prev_idx, state)
            if stopped_by is None:
                ranges.append((cur, last_default_idx + 1))
                cur = last_default_idx + 1
                state = _StatementState(tokens, i, end)
            else:
                if guard_hits is not None:
                    key = (stopped_by if isinstance(stopped_by, str)
                           else stopped_by.guard_id)
                    guard_hits[key] = guard_hits.get(key, 0) + 1
                if i == state.cte_select_idx:
                    # G4: this SELECT closed our own CTE prologue; spent.
                    state.cte_select_idx = None

        if tok_type != Token.EOF:
            last_default_idx = i
        prev_idx = i
        i = skip_hidden(tokens, i + 1, end)

    ranges.append((cur, end))
    return ranges


_LINE_START_RULE = "line-start"


def _suppressing_guard(tokens: list[Token], i: int, end: int, prev_idx: int,
                       state: _StatementState) -> BoundaryGuard | str | None:
    """For a candidate already known to be a BOUNDARY_KEYWORDS token at
    paren depth 0: returns None if it really does start a new statement,
    otherwise what stopped it -- the BoundaryGuard responsible, or the
    string _LINE_START_RULE for the positive rule's own line-start
    requirement, which is a condition of the rule rather than a guard and
    so is reported separately."""
    tok_type = tokens[i].type

    # G4 -- the SELECT that closes the current statement's own CTE
    # prologue is part of that statement, not a new one. Checked before
    # everything else since it's the one case where the candidate is
    # already spoken for.
    if i == state.cte_select_idx:
        return GUARDS_BY_ID["G4"]

    # Rule: must be the first default-channel token on its line.
    if tokens[i].line == tokens[prev_idx].line:
        return _LINE_START_RULE

    # G1 / G2 -- the previous token demands a query next.
    guard = SUPPRESS_PREV_GUARD.get(tokens[prev_idx].type)
    if guard is not None:
        return guard

    # G3 -- a non-SELECT statement gets one free depth-0 SELECT, which is
    # its body: "INSERT INTO t" / "SELECT ...", "CREATE TABLE t AS" /
    # "SELECT ...". A *second* one is a genuine new statement, so
    # "INSERT ... SELECT" followed by a bare query still splits.
    if tok_type == Db2Lexer.SELECT and not state.lead_is_select:
        if not state.inner_select_used:
            state.inner_select_used = True
            return GUARDS_BY_ID["G3"]
        return None

    # G5 -- a depth-0 WITH is only a statement start if it's really a CTE
    # list; "SELECT ... WITH UR" and friends are not.
    if tok_type == Db2Lexer.WITH:
        return None if cte_prologue_end(tokens, i, end) is not None else GUARDS_BY_ID["G5"]

    # G6 -- SET is a statement ("SET CURRENT SCHEMA ...") but also the
    # second line of "UPDATE t" / "SET col = 1". Only trust it when the
    # statement in progress is a SELECT, which can't contain one.
    if tok_type == Db2Lexer.SET:
        return None if state.lead_is_select else GUARDS_BY_ID["G6"]

    return None
