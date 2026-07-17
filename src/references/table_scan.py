# -*- coding: utf-8 -*-
"""Token-scan engine for table/alias/JOIN discovery -- the foundation
--extract-metadata's schema/table/column reference extraction and JOIN
relationship extraction both sit on top of. This module never touches the
parser; it only walks the already-lexed `Token` list (statement_driver.py's
`lex_file()` output, one chunk's slice at a time) -- same spirit as
supplementary_checks.py's existing Tier 3 token-scan fallback.

This exists as a *separate* pass from the parser because this module needs
to discover tables/aliases/JOINs regardless of what tier the tiered driver
resolved a given chunk at, and (as of issue #4 / commit 7fea4c8) uniformly
across both comma-joins and ANSI `JOIN ... ON`/`USING` chains -- one
mechanism instead of two. It originally existed to route around a real
parse-tree gap:

1. Schema-qualified names (`SCHEMA.TABLE`, `SCHEMA.TABLE.COLUMN`) don't
   parse at all -- `table_name`/`column_name` are always a single
   unqualified `id_ : ID` (the `ID` token itself contains no dot).
   `SELECT * FROM schema1.table1;` parses with zero syntax errors, but the
   tree only ever captures `table_name=schema1` -- `.table1` is silently
   left unconsumed in the token stream (no error, since `sql_statement()`,
   what the tiered driver actually calls, is never EOF-anchored). This gap
   is still open -- tracked in issue #1.
2. `JOIN ... ON`/`USING` (ANSI join syntax) used to have no parse path at
   all: `joined_table` was defined in the grammar but its only reference
   site was commented out (`//| joined_table`), so `FROM t1 a JOIN t2 b ON
   a.x=b.y` parsed with zero errors but the tree stopped dead after `FROM
   t1 a`, with `t2 b` shredded one token at a time by the tiered driver's
   Tier-3 safety valve. **Fixed** in issue #4 / commit 7fea4c8 -- ANSI
   joins now parse as one clean tree, same as comma-joins always did. This
   module's token-scan discovery of JOIN edges is kept regardless (see
   above), but detection (extractor_visitor.py) and column-level
   extraction (reference_visitor.py) both benefit directly from the fix,
   since they walk the tree itself rather than re-scanning tokens.

CTE names are excluded from the tables this module records (`WITH cte AS
(...) SELECT * FROM cte` must not report `cte` as a real table). A
*separate*, now-fixed issue -- a CTE's body SELECT used to get
independently re-surfaced by the tiered driver as if it were its own
standalone top-level statement (also issue #4 / commit 7fea4c8) -- used to
matter to --split-selects' chunk classification (select_blocks.py); see
that module's docstring for how it's unaffected either way.
"""

from antlr4.Token import Token

from Db2Lexer import Db2Lexer

PLACEHOLDER_SCHEMA = "(no-schema)"
PLACEHOLDER_TABLE = "(no-table)"

_JOIN_QUALIFIER_TYPES = {
    Db2Lexer.INNER: "INNER",
    Db2Lexer.LEFT: "LEFT",
    Db2Lexer.RIGHT: "RIGHT",
    Db2Lexer.FULL: "FULL",
    Db2Lexer.CROSS: "CROSS",
}


class TableRef(object):
    def __init__(self, schema, table, alias, line, start_char, stop_char):
        self.schema = schema
        self.table = table
        self.alias = alias
        self.line = line
        self.start_char = start_char
        self.stop_char = stop_char


class QueryBlock(object):
    """One SELECT's own scope -- [start_char, stop_char) character range,
    its FROM/JOIN/UPDATE/INTO table references, and the alias->TableRef map
    used to resolve a qualified column reference (`a.col1`) back to a real
    schema.table. Scoped per query block (not globally) since a
    correlation name is only valid within the block that declares it."""

    def __init__(self, start_char):
        self.start_char = start_char
        self.stop_char = None
        self.tables = []
        self.alias_map = {}
        # (left_ref, right_ref, join_type, predicate_text) tuples, one per
        # comma/JOIN connector between two successfully-recognized tables
        # in this block's own FROM-clause table list.
        self.join_connectors = []

    def add_table(self, ref):
        self.tables.append(ref)
        self.alias_map[ref.alias] = ref
        # DB2 allows using the real table name as its own qualifier even
        # when an explicit alias is also given -- but an explicit alias
        # always wins the same dict key, so only fill this in if unset.
        self.alias_map.setdefault(ref.table, ref)


class JoinEdge(object):
    def __init__(self, left, right, join_type, predicate_text, line):
        self.left = left
        self.right = right
        self.join_type = join_type
        self.predicate_text = predicate_text
        self.line = line


def _skip_hidden(tokens, i, n):
    """Index >= i of the next default-channel token, or None past the end."""
    while i < n and tokens[i].channel != Token.DEFAULT_CHANNEL:
        i += 1
    return i if i < n else None


def _skip_balanced_parens(tokens, open_idx):
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


def _last_real_token(tokens):
    for t in reversed(tokens):
        if t.type != Token.EOF:
            return t
    return None


def find_cte_names(tokens):
    """If this chunk opens with `WITH`, walks the CTE list (`table_name
    column_name_list_paren? AS '(' ... ')'`, comma-separated) tracking
    paren depth, collecting each declared CTE name (upper-cased). Returns
    an empty set if the chunk doesn't open with WITH. These names must
    never be recorded as real tables -- a later bare `FROM cte_name` binds
    to the CTE, not a schema object."""
    names = set()
    n = len(tokens)
    i = _skip_hidden(tokens, 0, n)
    if i is None or tokens[i].type != Db2Lexer.WITH:
        return names
    i = _skip_hidden(tokens, i + 1, n)
    while i is not None:
        if tokens[i].type != Db2Lexer.ID:
            break
        names.add(tokens[i].text.upper())
        i = _skip_hidden(tokens, i + 1, n)
        if i is not None and tokens[i].type == Db2Lexer.LEFT_RND_BKT:
            # optional column_name_list_paren before AS
            i = _skip_hidden(tokens, _skip_balanced_parens(tokens, i), n)
        if i is None or tokens[i].type != Db2Lexer.AS:
            break
        i = _skip_hidden(tokens, i + 1, n)
        if i is None or tokens[i].type != Db2Lexer.LEFT_RND_BKT:
            break
        i = _skip_hidden(tokens, _skip_balanced_parens(tokens, i), n)
        if i is not None and tokens[i].type == Db2Lexer.COMMA:
            i = _skip_hidden(tokens, i + 1, n)
            continue
        break
    return names


def _match_join_qualifier(tokens, i):
    """tokens[i] begins a JOIN-family keyword run if it's JOIN itself, or
    one of INNER/LEFT/RIGHT/FULL/CROSS (optionally followed by OUTER, then
    JOIN). Returns the matched join_type string, or None."""
    t = tokens[i].type
    if t == Db2Lexer.JOIN:
        return "JOIN"
    return _JOIN_QUALIFIER_TYPES.get(t)


def _skip_join_keyword_run(tokens, i, n):
    """tokens[i] is where _match_join_qualifier matched. Returns the index
    right after the JOIN keyword itself."""
    if tokens[i].type != Db2Lexer.JOIN:
        i = _skip_hidden(tokens, i + 1, n)  # past the qualifier keyword
        if i is not None and tokens[i].type == Db2Lexer.OUTER:
            i = _skip_hidden(tokens, i + 1, n)
    if i is not None and tokens[i].type == Db2Lexer.JOIN:
        i += 1
    return i


_NO_SPACE_BEFORE = {Db2Lexer.DOT, Db2Lexer.RIGHT_RND_BKT, Db2Lexer.COMMA, Db2Lexer.SEMI}
_NO_SPACE_AFTER = {Db2Lexer.DOT, Db2Lexer.LEFT_RND_BKT}


def _join_token_texts(toks):
    """Joins default-channel token texts back into readable source-like
    text (`a.col1 = b.col2`, not `a . col1 = b . col2`) -- for reporting
    only, not meant to be re-lexed verbatim."""
    out = []
    for idx, t in enumerate(toks):
        if idx > 0:
            prev = toks[idx - 1]
            if t.type not in _NO_SPACE_BEFORE and prev.type not in _NO_SPACE_AFTER:
                out.append(" ")
        out.append(t.text)
    return "".join(out)


def _capture_predicate_text(tokens, start_i, n):
    """Raw source text of a JOIN's ON-clause (or any search-condition-
    shaped fragment), from start_i up to (not including) the next WHERE/
    GROUP/ORDER/JOIN-family-keyword/COMMA/SEMI/EOF at the *current* paren
    depth (relative to start_i, clamped at 0 -- same technique
    statement_driver.chunk_ranges() uses for top-level ';' splitting)."""
    depth = 0
    parts = []
    i = start_i
    while i < n:
        t = tokens[i]
        if t.channel != Token.DEFAULT_CHANNEL:
            i += 1
            continue
        if t.type == Db2Lexer.LEFT_RND_BKT:
            depth += 1
        elif t.type == Db2Lexer.RIGHT_RND_BKT:
            if depth == 0:
                break
            depth -= 1
        elif depth == 0 and (
            t.type in (Db2Lexer.WHERE, Db2Lexer.GROUP, Db2Lexer.ORDER,
                      Db2Lexer.SEMI, Token.EOF, Db2Lexer.COMMA)
            or _match_join_qualifier(tokens, i) is not None
        ):
            break
        parts.append(t)
        i += 1
    return _join_token_texts(parts), i


def _capture_using_columns_text(tokens, start_i, n):
    i = _skip_hidden(tokens, start_i, n)
    if i is None or tokens[i].type != Db2Lexer.LEFT_RND_BKT:
        return "", (i if i is not None else n)
    j = _skip_balanced_parens(tokens, i)
    parts = [t for t in tokens[i:j] if t.channel == Token.DEFAULT_CHANNEL]
    return _join_token_texts(parts), j


def _scan_one_table_ref(tokens, i, cte_names, by_start=None):
    """tokens[i] is the first default-channel token of one table-list
    entry. Returns (TableRef_or_None, next_index). None covers two cases:
    a parenthesized derived table/subquery, and a CTE-name reference
    (excluded from being recorded as a real table). Either way
    `next_index` is advanced past whatever this entry (including its own
    optional alias) occupied, so the caller can keep scanning for a
    following comma/JOIN connector.

    A derived table's own inner SELECT is *not* just skipped over: its
    span was already discovered by _discover_blocks' unconditional,
    never-skipping walk (so by_start already has a QueryBlock for it), but
    that inner SELECT's own FROM-clause still needs its *tables* populated
    -- which only happens by recursing _populate_table_lists into this
    derived table's own parens right here. Without this recursive step, a
    table used only inside a derived table (`FROM (SELECT * FROM inner_t)
    t`) would never be discovered, even though its enclosing block would
    exist with an empty table list."""
    n = len(tokens)
    tok = tokens[i]
    if tok.type == Db2Lexer.LEFT_RND_BKT:
        close_idx = _skip_balanced_parens(tokens, i)
        if by_start is not None:
            _populate_table_lists(tokens, by_start, cte_names, start=i, end=close_idx)
        j = _skip_hidden(tokens, close_idx, n)
        if j is not None and tokens[j].type == Db2Lexer.AS:
            j = _skip_hidden(tokens, j + 1, n)
        if j is not None and tokens[j].type == Db2Lexer.ID:
            j += 1
        return None, (j if j is not None else n)
    if tok.type != Db2Lexer.ID:
        return None, i

    line = tok.line
    start_char = tok.start
    part1 = tok.text.upper()
    schema, table, stop_char = PLACEHOLDER_SCHEMA, part1, tok.stop
    j = _skip_hidden(tokens, i + 1, n)
    if j is not None and tokens[j].type == Db2Lexer.DOT:
        j2 = _skip_hidden(tokens, j + 1, n)
        if j2 is not None and tokens[j2].type == Db2Lexer.ID:
            schema, table = part1, tokens[j2].text.upper()
            stop_char = tokens[j2].stop
            j = j2 + 1
            j3 = _skip_hidden(tokens, j, n)
            if j3 is not None and tokens[j3].type == Db2Lexer.DOT:
                j4 = _skip_hidden(tokens, j3 + 1, n)
                if j4 is not None and tokens[j4].type == Db2Lexer.ID:
                    # 3-part catalog.schema.table -- what was tentatively
                    # "table" (the 2nd part) is really the schema; catalog
                    # (part1) is dropped, documented limitation.
                    schema = table
                    table = tokens[j4].text.upper()
                    stop_char = tokens[j4].stop
                    j = j4 + 1
    else:
        j = j if j is not None else n

    is_cte = table in cte_names
    alias = table
    k = _skip_hidden(tokens, j, n)
    if k is not None and tokens[k].type == Db2Lexer.AS:
        k2 = _skip_hidden(tokens, k + 1, n)
        if k2 is not None and tokens[k2].type == Db2Lexer.ID:
            alias = tokens[k2].text.upper()
            j = k2 + 1
        else:
            j = k + 1
    elif k is not None and tokens[k].type == Db2Lexer.ID:
        alias = tokens[k].text.upper()
        j = k + 1

    if is_cte:
        return None, j
    return TableRef(schema, table, alias, line, start_char, stop_char), j


def _scan_table_list(tokens, from_index, cte_names, by_start=None):
    """Starting right after a FROM/UPDATE/INTO keyword, scans a comma-
    and/or JOIN-connected list of table references. Returns (entries,
    connectors, next_index): `entries` parallels the source order and may
    contain None for a derived-table/CTE slot (see _scan_one_table_ref);
    `connectors[k]` is (join_type, predicate_text) describing how
    entries[k] connects to entries[k+1] ("COMMA" has no predicate here --
    a comma-join's real predicate lives in the WHERE clause, recovered
    separately as a "WHERE-IMPLICIT" edge, see relations.py)."""
    n = len(tokens)
    entries = []
    connectors = []
    i = _skip_hidden(tokens, from_index, n)
    if i is None:
        return entries, connectors, n
    ref, i = _scan_one_table_ref(tokens, i, cte_names, by_start)
    entries.append(ref)
    while True:
        i = _skip_hidden(tokens, i, n)
        if i is None:
            break
        if tokens[i].type == Db2Lexer.COMMA:
            i = _skip_hidden(tokens, i + 1, n)
            if i is None:
                connectors.append(("COMMA", ""))
                break
            ref, i = _scan_one_table_ref(tokens, i, cte_names, by_start)
            entries.append(ref)
            connectors.append(("COMMA", ""))
            continue
        join_type = _match_join_qualifier(tokens, i)
        if join_type is not None:
            i = _skip_join_keyword_run(tokens, i, n)
            i = _skip_hidden(tokens, i, n) if i is not None else None
            if i is None:
                connectors.append((join_type, ""))
                break
            ref, i = _scan_one_table_ref(tokens, i, cte_names, by_start)
            entries.append(ref)
            predicate = ""
            i2 = _skip_hidden(tokens, i, n)
            if i2 is not None and tokens[i2].type == Db2Lexer.ON:
                predicate, i = _capture_predicate_text(tokens, i2 + 1, n)
            elif i2 is not None and tokens[i2].type == Db2Lexer.USING:
                predicate, i = _capture_using_columns_text(tokens, i2 + 1, n)
            connectors.append((join_type, predicate))
            continue
        break
    # Every `break` above can fire with `i` already None (ran out of
    # tokens via _skip_hidden) -- normalize before returning, since a
    # leaked None assigned straight into a caller's own loop index (e.g.
    # _populate_table_lists' `i = j2`) crashes its `while i < n` check on
    # the very next iteration.
    if i is None:
        i = n
    return entries, connectors, i


def _apply_table_list(qb, entries, connectors):
    for e in entries:
        if e is not None:
            qb.add_table(e)
    for k in range(len(connectors)):
        left, right = entries[k], entries[k + 1]
        if left is not None and right is not None:
            join_type, predicate = connectors[k]
            qb.join_connectors.append((left, right, join_type, predicate))


def _discover_blocks(tokens):
    """Pass A: an unconditional walk over *every* token (never skips
    anything -- this is what guarantees a nested SELECT inside a derived
    table, IN(...)/EXISTS(...), or CTE body is always found, regardless of
    what Pass B's table-list scanning does or doesn't skip past). Pushes a
    new QueryBlock on each SELECT, tracks paren depth (clamped at 0) to
    know which block is innermost, and closes/finalizes a block either
    when its enclosing paren closes (covers CTE bodies and subqueries
    alike -- both are just "a SELECT one or more parens deeper than its
    sibling") or when a new SELECT appears at the same-or-shallower depth
    (covers UNION/INTERSECT/EXCEPT siblings, whose FROM-clause aliases
    don't carry over to each other).

    Also pushes one implicit chunk-level block up front (unless the
    chunk's very first real token already is SELECT, which would
    immediately close it anyway) so a non-SELECT statement (UPDATE/DELETE/
    a bare INSERT INTO ... VALUES) still has *some* block for its own
    target table + WHERE/SET-clause qualifier resolution to attach to."""
    n = len(tokens)
    depth = 0
    open_blocks = []  # stack of (QueryBlock, opening_depth)
    finished = []

    first_idx = _skip_hidden(tokens, 0, n)
    if first_idx is not None and tokens[first_idx].type != Db2Lexer.SELECT:
        open_blocks.append((QueryBlock(tokens[first_idx].start), 0))

    i = 0
    while i < n:
        tok = tokens[i]
        if tok.channel != Token.DEFAULT_CHANNEL:
            i += 1
            continue
        ttype = tok.type
        if ttype == Db2Lexer.SELECT:
            while open_blocks and open_blocks[-1][1] >= depth:
                qb, _ = open_blocks.pop()
                qb.stop_char = tok.start
                finished.append(qb)
            open_blocks.append((QueryBlock(tok.start), depth))
        elif ttype == Db2Lexer.LEFT_RND_BKT:
            depth += 1
        elif ttype == Db2Lexer.RIGHT_RND_BKT:
            depth = max(0, depth - 1)
            while open_blocks and open_blocks[-1][1] > depth:
                qb, _ = open_blocks.pop()
                qb.stop_char = tok.start
                finished.append(qb)
        i += 1

    last_real = _last_real_token(tokens)
    end_char = (last_real.stop + 1) if last_real is not None else 0
    while open_blocks:
        qb, _ = open_blocks.pop()
        qb.stop_char = end_char
        finished.append(qb)

    return finished


def _populate_table_lists(tokens, by_start, cte_names, start=0, end=None):
    """Pass B: attaches FROM/UPDATE/INTO-discovered tables to the already-
    discovered (Pass A) QueryBlock that's current at each point. Unlike
    Pass A, this pass *is* free to skip a derived table's parens (via
    _scan_one_table_ref/_scan_table_list) for the purpose of continuing to
    look for a following comma/JOIN sibling in the *same* table list --
    that skip doesn't lose anything, because _scan_one_table_ref
    recursively re-invokes this same function scoped to exactly that
    derived table's own parens (using the same `by_start` map Pass A
    already built), so its inner SELECT's table list still gets
    populated. Called once for the whole chunk (start=0, end=None) and
    then recursively, once per derived table encountered, scoped to just
    that derived table's own token range."""
    n = len(tokens) if end is None else end
    depth = 0
    open_blocks = []  # stack of (QueryBlock, opening_depth), local to this call

    if start == 0:
        # Mirror _discover_blocks' implicit chunk-level block push exactly
        # (same condition, same start_char key) so a non-SELECT statement's
        # target table has something to attach to here too -- Pass A
        # created the object, this just needs to know it's already open.
        first_idx = _skip_hidden(tokens, 0, n)
        if first_idx is not None and tokens[first_idx].type != Db2Lexer.SELECT:
            qb = by_start.get(tokens[first_idx].start)
            if qb is not None:
                open_blocks.append((qb, 0))

    i = start
    while i < n:
        tok = tokens[i]
        if tok.channel != Token.DEFAULT_CHANNEL:
            i += 1
            continue
        ttype = tok.type
        if ttype == Db2Lexer.SELECT:
            while open_blocks and open_blocks[-1][1] >= depth:
                open_blocks.pop()
            qb = by_start.get(tok.start)
            if qb is not None:
                open_blocks.append((qb, depth))
            i += 1
        elif ttype == Db2Lexer.LEFT_RND_BKT:
            depth += 1
            i += 1
        elif ttype == Db2Lexer.RIGHT_RND_BKT:
            depth = max(0, depth - 1)
            while open_blocks and open_blocks[-1][1] > depth:
                open_blocks.pop()
            i += 1
        elif ttype in (Db2Lexer.FROM, Db2Lexer.UPDATE, Db2Lexer.INTO) and open_blocks:
            j = _skip_hidden(tokens, i + 1, n)
            if j is None:
                i += 1
                continue
            entries, connectors, j2 = _scan_table_list(tokens, j, cte_names, by_start)
            _apply_table_list(open_blocks[-1][0], entries, connectors)
            i = j2
        else:
            i += 1


def scan_query_blocks(tokens):
    """Discovers every query block in a chunk's tokens
    (all_tokens[start:end] from statement_driver.chunk_ranges()) and
    populates each with its own FROM/JOIN/UPDATE/INTO table references and
    alias map -- see _discover_blocks (Pass A) and _populate_table_lists
    (Pass B) for why this needs to be two coordinated passes rather than
    one. Returns list[QueryBlock] (order doesn't matter -- callers use
    resolve_qualifier for containment lookups, not iteration order)."""
    cte_names = find_cte_names(tokens)
    blocks = _discover_blocks(tokens)
    by_start = {qb.start_char: qb for qb in blocks}
    _populate_table_lists(tokens, by_start, cte_names)
    return blocks


def scan_join_edges(query_blocks):
    """Flattens every QueryBlock's own join_connectors (already built while
    scanning that block's FROM-clause table list) into JoinEdge objects."""
    edges = []
    for qb in query_blocks:
        for left, right, join_type, predicate in qb.join_connectors:
            edges.append(JoinEdge(left, right, join_type, predicate, left.line))
    return edges


def resolve_qualifier(query_blocks, char_offset, qualifier):
    """qualifier: upper-cased alias text (a field_reference's
    row_variable_name), or None for a bare, unqualified column_name.
    Finds the innermost (smallest enclosing [start_char, stop_char)) block
    containing char_offset and resolves qualifier against its alias_map.
    Uses character offsets, not token indices -- token indices get
    reassigned per-CommonTokenStream/ListTokenSource, but Token.start/.stop
    character offsets never change once the lexer sets them (verified in
    vendor/antlr4-python3-runtime/antlr4/Token.py), so they're the only
    safe cross-stream key for matching a tree-walk finding back to this
    token-scan-computed scope. `char_offset` itself is guarded against
    None too -- a heavily error-recovered tree (e.g. from a file with a
    lot of non-SQL noise) can hand back a context whose own token
    position didn't resolve to a real offset."""
    if qualifier is None or char_offset is None:
        return PLACEHOLDER_SCHEMA, PLACEHOLDER_TABLE
    best = None
    for qb in query_blocks:
        if qb.stop_char is None:
            continue
        if qb.start_char <= char_offset <= qb.stop_char:
            span = qb.stop_char - qb.start_char
            if best is None or span < best[0]:
                best = (span, qb)
    if best is None:
        return PLACEHOLDER_SCHEMA, PLACEHOLDER_TABLE
    ref = best[1].alias_map.get(qualifier.upper())
    if ref is None:
        return PLACEHOLDER_SCHEMA, PLACEHOLDER_TABLE
    return ref.schema, ref.table


def iter_table_refs(query_blocks):
    """Flattens every QueryBlock's tables for --extract-metadata's
    schema.table extraction."""
    return [ref for qb in query_blocks for ref in qb.tables]


def extract_table_refs_only(text):
    """Cheap, tree-free convenience wrapper for anywhere that wants table
    refs without paying for a full tiered parse: lexes once, chunks, and
    runs scan_query_blocks/iter_table_refs per chunk. Never invokes
    sql_statement()/search_condition() -- table-reference extraction
    never needed a real parse. Returns a flat list of (schema, table,
    line) tuples."""
    from src.detect.statement_driver import lex_file, chunk_ranges

    all_tokens, _lexer_errors = lex_file(text)
    out = []
    for start, end in chunk_ranges(all_tokens):
        blocks = scan_query_blocks(all_tokens[start:end])
        for ref in iter_table_refs(blocks):
            out.append((ref.schema, ref.table, ref.line))
    return out
