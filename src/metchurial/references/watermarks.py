# -*- coding: utf-8 -*-
"""Incremental-load watermark extraction (--extract-metadata):
refs_watermarks.tsv, one row per WHERE predicate that filters a column
against a rolling "today minus a window" expression.

A lot of production DB2 SQL (Informatica-generated ETL especially) does
watermark-style incremental loads: the WHERE clause filters on a datetime
special register offset by a duration rather than a hardcoded date, so
the same mapping picks up a rolling slice on every run. This module makes
that corpus-wide auditable -- which column each query treats as its
watermark, and how far back its window reaches.

Shapes recognized, all reduced to the same
`special register (+|-) duration` core with an optional wrapper chain:

1. Direct special-register arithmetic:
       WHERE o.order_date >= CURRENT DATE - 365 DAYS
       WHERE our_month_column = CURRENT DATE - 1 MONTH
   -- range and equality predicates alike; the arithmetic can sit on
   either side of the operator.
2. Format-then-subtract, where the arithmetic is wrapped in one or more
   formatting/encoding calls before comparison:
       WHERE load_month = CHAR(CURRENT DATE - 1 MONTH, ISO)
       WHERE batch_key  = DECIMAL(CHAR(CURRENT DATE - 3 DAYS, USA), 8, 0)
       WHERE part_key   = HEX(CURRENT DATE - 1 MONTH)
3. Weekday-conditional windows, where the offset amount is itself a
   DECODE over DAYOFWEEK (go back 4 days on Monday, 2 on Friday, else 1 --
   the usual "skip the weekend" idiom):
       WHERE txn_date >= CURRENT DATE - DECODE(DAYOFWEEK(CURRENT DATE), 2, 4, 6, 2, 1) DAYS

`pattern` names which of those matched, as two orthogonal facets so new
shapes slot in without renaming the existing tags:

* wrapper facet -- "DIRECT" when the arithmetic is compared as-is, or
  "WRAPPED:<chain>" naming the enclosing calls outermost-first
  ("WRAPPED:HEX", "WRAPPED:DECIMAL>CHAR").
* offset facet -- "+CONDITIONAL" appended when the offset amount is a
  DECODE rather than a literal.

So the five shapes above tag as DIRECT, WRAPPED:CHAR,
WRAPPED:DECIMAL>CHAR, WRAPPED:HEX, and DIRECT+CONDITIONAL.

Scope: WHERE clauses at *any* nesting depth -- a subquery's or CTE body's
own WHERE defines a windowed record set just as much as the outermost
one does. ON and HAVING are excluded (a join condition isn't an
incremental filter, and neither is a post-aggregation one), which is
decided by walking up to the nearest enclosing clause and requiring it to
be a where_clause rather than by nesting depth.

A statement the grammar can't parse whole (fixture 38's XMLTABLE/
XMLELEMENT-heavy modules, say) never produces a where_clause node at all:
the tiered driver (statement_driver.py) recovers it as one or more bare
`search_condition` fragments, and a fragment has no enclosing clause node
to walk up to. Rather than drop those (a corpus of legacy SQL has plenty
of statements no grammar parses whole, and their incremental filters are
exactly as real as anyone else's), scope falls back to a token scan over
the chunk: a predicate counts as a WHERE condition when the nearest
*preceding* clause keyword is a WHERE. That mirrors how the driver's own
Tier 2 resync picks its anchors -- linearly, over the same token stream --
and it's the same positional, token-scan style scoping table_scan.py
already uses where the grammar can't provide structure. It is an
approximation only in the fallback path: a parsed statement is always
scoped structurally off its tree, never this way.

Known gaps, each a shape to extend this with rather than a wrong answer:

1. `case_expression` is a stub rule in the vendored grammar
   (`case_expression : CASE ;` -- Db2Parser.g4:3286), so a CASE-conditional
   window has no parse tree to read at all. DECODE is unaffected: it isn't
   a reserved lexer token, so it parses as an ordinary
   `function_invocation`.
2. A bare `WHERE d = CURRENT DATE` with no arithmetic is deliberately not
   reported -- there's no window to size, which is what this artifact is
   for.
3. An offset amount that isn't an integer literal (a host variable, or a
   DECODE branch returning an expression) leaves `window_size` empty for
   that branch; `window_expression` still carries the raw source text, so
   nothing is silently dropped.
"""

from __future__ import annotations

import bisect
from typing import Any, Callable

from antlr4.Token import Token

from metchurial._generated.Db2Lexer import Db2Lexer
from metchurial._generated.Db2Parser import Db2Parser
from metchurial._generated.Db2ParserVisitor import Db2ParserVisitor

from metchurial.models.tables import QueryBlock
from metchurial.models.watermarks import WatermarkUse
from metchurial.parsing.predicates import COMPARISON_OPS, classify_predicate
from metchurial.references import table_scan
from metchurial.tsv import write_refs_tsv

# Duration units the grammar's postfix-duration expression alternative
# accepts (`expression (YEAR | YEARS | MONTH | MONTHS | day_to_seconds |
# MICROSECOND | MICROSECONDS)`, Db2Parser.g4:5202), mapped to the
# canonical singular form window_size normalizes to -- so a corpus-wide
# audit groups `- 1 MONTH` and `- 2 MONTHS` under one unit instead of
# splitting them on how each file happened to be written. The raw
# as-written text is still available in window_expression.
_CANONICAL_UNITS = {
    "YEAR": "YEAR", "YEARS": "YEAR",
    "MONTH": "MONTH", "MONTHS": "MONTH",
    "DAY": "DAY", "DAYS": "DAY",
    "HOUR": "HOUR", "HOURS": "HOUR",
    "MINUTE": "MINUTE", "MINUTES": "MINUTE",
    "SECOND": "SECOND", "SECONDS": "SECOND",
    "MICROSECOND": "MICROSECOND", "MICROSECONDS": "MICROSECOND",
}

# Comparison operators, mirrored for the case where the source wrote the
# window on the left (`CURRENT DATE - 7 DAYS <= load_dt`). Rows always read
# as `watermark_column <operator> window_expression`, so the operator has
# to be flipped, not just copied, when the two sides are swapped.
_MIRRORED_OPS = {"=": "=", "<>": "<>", "<": ">", ">": "<", "<=": ">=", ">=": "<="}

# Function name whose *arguments* carry conditional offset amounts, in
# DECODE(value, match1, result1, match2, result2, ..., default) form.
_CONDITIONAL_FUNCTION = "DECODE"

# Keywords that start a new clause, for the token-scan fallback that
# scopes predicates inside a statement the grammar couldn't parse whole
# (see the module docstring). Only WHERE puts what follows it in scope;
# the rest are here so that reaching one of them means the preceding
# WHERE's clause has ended -- ON and HAVING because they carry their own,
# out-of-scope conditions, and the others because they end a WHERE
# outright. Deliberately linear and depth-blind, the same way the driver's
# own resync anchors are: an inner SELECT/FROM closes the outer WHERE
# (under-reporting a filter written after a scalar subquery, rather than
# risking an ON condition nested inside a WHERE being read as one).
_CLAUSE_KEYWORDS = {
    Db2Lexer.WHERE, Db2Lexer.ON, Db2Lexer.HAVING, Db2Lexer.GROUP, Db2Lexer.ORDER,
    Db2Lexer.FETCH, Db2Lexer.UNION, Db2Lexer.INTERSECT, Db2Lexer.EXCEPT,
    Db2Lexer.SELECT, Db2Lexer.FROM, Db2Lexer.SET, Db2Lexer.VALUES,
    Db2Lexer.USING, Db2Lexer.WHEN,
}


def _slice(text: str, ctx: Any) -> str:
    """Raw source text of a node, sliced by character offset rather than
    reconstructed via getText() (which glues tokens together with no
    whitespace) -- same convention function_visitor.py uses, so
    window_expression reads exactly as written."""
    return text[ctx.start.start:ctx.stop.stop + 1]


def _normalize_ws(text: str) -> str:
    return " ".join(text.split())


def clause_starts(chunk_tokens: list[Token]) -> list[tuple[int, bool]]:
    """Every clause keyword in `chunk_tokens` as (character offset, is a
    WHERE), in source order -- the lookup table the token-scan fallback
    bisects to find which clause governs a given position. Hidden-channel
    tokens are skipped, so a comment between a WHERE and its condition
    can't shift a boundary."""
    return [(token.start, token.type == Db2Lexer.WHERE)
            for token in chunk_tokens
            if token.channel == Token.DEFAULT_CHANNEL and token.type in _CLAUSE_KEYWORDS]


def _governed_by_where(offset: int, starts: list[tuple[int, bool]],
                       offsets: list[int]) -> bool:
    """True iff the nearest clause keyword *before* `offset` is a WHERE."""
    index = bisect.bisect_right(offsets, offset) - 1
    return index >= 0 and starts[index][1]


def _in_where_clause(ctx: Any, starts: list[tuple[int, bool]], offsets: list[int]) -> bool:
    """True iff `ctx` is a WHERE condition.

    Walks up to the first where/having/ON ancestor rather than testing
    nesting depth: a subquery's own WHERE is in scope no matter how deeply
    it sits, while an ON condition nested *inside* a WHERE's EXISTS
    subquery is not -- only the nearest clause decides.

    Reaching the root with no clause ancestor at all means this tree is a
    bare fragment the driver resynced out of a statement it couldn't parse
    whole, so there is no enclosing clause node to find; the token-scan
    fallback decides instead (see the module docstring)."""
    node = ctx
    while node.parentCtx is not None:
        node = node.parentCtx
        if isinstance(node, Db2Parser.Where_clauseContext):
            return True
        if isinstance(node, (Db2Parser.Having_clauseContext, Db2Parser.Join_conditionContext)):
            return False
    return _governed_by_where(ctx.start.start, starts, offsets)


def _unwrap_parens(expr: Db2Parser.ExpressionContext) -> Db2Parser.ExpressionContext:
    """Peel redundant parentheses off an expression: `('(' expression_list
    ')')` holding exactly one expression is just that expression, so
    `(CURRENT DATE - 7 DAYS)` reaches the same detector as the unbracketed
    form."""
    while True:
        expr_list = expr.expression_list()
        if expr_list is None:
            return expr
        inner = expr_list.expression()
        if len(inner) != 1:
            return expr
        expr = inner[0]


def _duration_unit(expr: Db2Parser.ExpressionContext) -> str | None:
    """The unit token of the grammar's postfix-duration alternative
    (`expression <unit>`), or None if `expr` isn't that alternative.

    ExpressionContext is one generated class covering every alternative
    (same flat shape as PredicateContext -- see parsing/predicates.py), so
    which one matched is recoverable only by probing accessors. DAY/HOUR/
    MINUTE/SECOND units arrive wrapped in a `day_to_seconds` subrule;
    YEAR/MONTH/MICROSECOND are direct token children."""
    day_to_seconds = expr.day_to_seconds()
    if day_to_seconds is not None:
        return day_to_seconds.getText().upper()
    for accessor in ("YEAR", "YEARS", "MONTH", "MONTHS", "MICROSECOND", "MICROSECONDS"):
        token = getattr(expr, accessor)()
        if token is not None:
            return token.getText().upper()
    return None


def _additive_operands(expr: Db2Parser.ExpressionContext,
                       ) -> tuple[Db2Parser.ExpressionContext, str, Db2Parser.ExpressionContext] | None:
    """Split the `expression ('+' | '-') expression` alternative into
    (left, sign, right), or None for any other alternative. Several
    alternatives have two expression children ('**', '*', '/', '%',
    CONCAT), so the operator token itself is what's checked."""
    operands = expr.expression()
    if len(operands) != 2:
        return None
    for accessor, sign in (("MINUS", "-"), ("PLUS", "+")):
        if getattr(expr, accessor)() is not None:
            return operands[0], sign, operands[1]
    return None


def _special_register_text(expr: Db2Parser.ExpressionContext, text: str) -> str | None:
    """`CURRENT DATE` / `CURRENT TIMESTAMP` / `CURRENT TIME` as written
    (whitespace-normalized, upper-cased), or None if `expr` isn't a
    datetime special register."""
    register = expr.special_register()
    if register is None:
        return None
    datetime_register = register.datetime_special_register()
    if datetime_register is None:
        return None
    return _normalize_ws(_slice(text, datetime_register)).upper()


def _integer_literal(expr: Db2Parser.ExpressionContext) -> str | None:
    """An offset amount written as a plain integer literal, or None. The
    lexer gives `1` and `0` their own L_ONE/L_ZERO tokens rather than
    routing them through integer_constant, so this reads the text and
    checks it rather than dispatching on the constant's subrule."""
    if expr.constant_() is None:
        return None
    literal = expr.constant_().getText()
    return literal if literal.isdigit() else None


def _decode_result_amounts(expr: Db2Parser.ExpressionContext) -> list[str] | None:
    """Every branch result of a `DECODE(value, match, result, ...,
    default)` offset amount, as integer-literal strings, or None if `expr`
    isn't a DECODE call.

    DECODE's arguments after the tested value pair up as match/result, with
    a trailing odd argument acting as the default result -- so the window
    sizes are the results, at every second argument from index 2 on, plus
    that default. A branch whose result isn't an integer literal is
    skipped (see the module docstring's known gaps); the returned list is
    empty rather than None in that case, which still tags the row
    +CONDITIONAL with no size claimed."""
    invocation = expr.function_invocation()
    if invocation is None or invocation.function_name().getText().upper() != _CONDITIONAL_FUNCTION:
        return None
    arg_list = invocation.arg_list()
    if arg_list is None:
        return []
    arguments = arg_list.argument()
    amounts = []
    for index in range(2, len(arguments), 2):
        amounts.append(arguments[index])
    if len(arguments) % 2 == 0:
        amounts.append(arguments[-1])  # trailing default result
    literals = []
    for argument in amounts:
        argument_expr = argument.expression()
        if argument_expr is None:
            continue
        literal = _integer_literal(_unwrap_parens(argument_expr))
        if literal is not None:
            literals.append(literal)
    return literals


class _Window:
    """One recognized `special register (+|-) duration` core, plus the
    chain of formatting/encoding calls it was found inside."""

    def __init__(self, base: str, sign: str, unit: str,
                 amounts: list[str], conditional: bool, wrappers: list[str]) -> None:
        self.base = base
        self.sign = sign
        self.unit = unit
        self.amounts = amounts
        self.conditional = conditional
        self.wrappers = wrappers

    def sizes(self) -> tuple[str, ...]:
        """Normalized window size(s): sign, amount, canonical singular
        unit. More than one only for a conditional (DECODE) window, whose
        branches are reported as one '; '-joined cell rather than as
        separate rows -- one row per predicate occurrence is the
        convention every refs_*.tsv shares."""
        unit = _CANONICAL_UNITS.get(self.unit, self.unit)
        return tuple("{}{} {}".format(self.sign, amount, unit) for amount in self.amounts)

    def pattern(self) -> str:
        tag = ("WRAPPED:" + ">".join(self.wrappers)) if self.wrappers else "DIRECT"
        return (tag + "+CONDITIONAL") if self.conditional else tag


def _find_window(expr: Db2Parser.ExpressionContext, text: str,
                 wrappers: list[str] | None = None) -> _Window | None:
    """Recognize the window shape in one side of a comparison, descending
    through any wrapping function calls (`CHAR(...)`, `DECIMAL(CHAR(...))`,
    `HEX(...)`) to reach the arithmetic underneath.

    Only a single-argument descent path is followed per wrapper level plus
    the wrapper's own trailing formatting arguments -- i.e. every argument
    is tried, and the first that contains a window wins, so
    `DECIMAL(CHAR(CURRENT DATE - 3 DAYS, USA), 8, 0)` resolves through
    argument 1 of DECIMAL and argument 1 of CHAR."""
    wrappers = wrappers if wrappers is not None else []
    expr = _unwrap_parens(expr)

    unit = _duration_unit(expr)
    if unit is not None and unit in _CANONICAL_UNITS:
        operands = _additive_operands(_unwrap_parens(expr.expression()[0]))
        if operands is not None:
            left, sign, right = operands
            base = _special_register_text(_unwrap_parens(left), text)
            if base is not None:
                amount_expr = _unwrap_parens(right)
                literal = _integer_literal(amount_expr)
                if literal is not None:
                    return _Window(base, sign, unit, [literal], False, wrappers)
                decode_amounts = _decode_result_amounts(amount_expr)
                if decode_amounts is not None:
                    return _Window(base, sign, unit, decode_amounts, True, wrappers)
                return _Window(base, sign, unit, [], False, wrappers)

    invocation = expr.function_invocation()
    if invocation is None:
        return None
    arg_list = invocation.arg_list()
    if arg_list is None:
        return None
    name = invocation.function_name().getText().upper()
    for argument in arg_list.argument():
        argument_expr = argument.expression()
        if argument_expr is None:
            continue
        window = _find_window(argument_expr, text, wrappers + [name])
        if window is not None:
            return window
    return None


class _WatermarkVisitor(Db2ParserVisitor):
    """Walks committed trees looking for comparison predicates, inside a
    WHERE clause at any depth, whose one side is a windowed datetime
    special-register expression -- see the module docstring for the shapes
    and the scope rule."""

    def __init__(self, text: str, path: str, query_blocks: list[QueryBlock],
                 clause_starts_: list[tuple[int, bool]],
                 sink: Callable[[WatermarkUse], None]) -> None:
        self.text = text
        self.path = path
        self.query_blocks = query_blocks
        self.clause_starts = clause_starts_
        self.clause_offsets = [offset for offset, _is_where in clause_starts_]
        self.sink = sink

    def visitPredicate(self, ctx: Db2Parser.PredicateContext) -> Any:
        op = classify_predicate(ctx)
        if op in COMPARISON_OPS and _in_where_clause(
                ctx, self.clause_starts, self.clause_offsets):
            left, right = ctx.expression()[0], ctx.expression()[1]
            # Right side first: `column >= CURRENT DATE - 7 DAYS` is the
            # overwhelmingly common way round, and only one row is emitted
            # per predicate even in the degenerate case where both sides
            # are windowed.
            for window_side, column_side, operator in ((right, left, op),
                                                       (left, right, _MIRRORED_OPS[op])):
                window = _find_window(window_side, self.text)
                if window is not None:
                    self._emit(window, window_side, column_side, operator, ctx.start.line)
                    break
        return self.visitChildren(ctx)

    def _emit(self, window: _Window, window_side: Db2Parser.ExpressionContext,
              column_side: Db2Parser.ExpressionContext, operator: str, line: int) -> None:
        schema, table, column = self._resolve_column(column_side)
        self.sink(WatermarkUse(
            schema=schema, table=table, watermark_column=column,
            operator=operator, base=window.base,
            window_expression=_normalize_ws(_slice(self.text, window_side)),
            window_size=window.sizes(), pattern=window.pattern(),
            file=self.path, line=line,
        ))

    def _resolve_column(self, expr: Db2Parser.ExpressionContext) -> tuple[str, str, str]:
        """The compared side as (schema, table, column). A table/alias-
        qualified reference resolves to its owning table the same way
        reference_visitor.py does; a bare column keeps the placeholders;
        anything else (a formatted or derived key, e.g.
        `SUBSTR(load_dt, 1, 6)`) reports its raw source text, since a
        watermark on a derived key is still a watermark worth auditing."""
        expr = _unwrap_parens(expr)
        field_reference = expr.field_reference()
        if field_reference is not None:
            qualifier = field_reference.row_variable_name().getText().upper()
            schema, table = table_scan.resolve_qualifier(
                self.query_blocks, expr.start.start, qualifier)
            return schema, table, field_reference.field_name().getText().upper()
        column_name = expr.column_name()
        if column_name is not None:
            return (table_scan.PLACEHOLDER_SCHEMA, table_scan.PLACEHOLDER_TABLE,
                    column_name.getText().upper())
        return (table_scan.PLACEHOLDER_SCHEMA, table_scan.PLACEHOLDER_TABLE,
                _normalize_ws(_slice(self.text, expr)))


def make_watermark_visitor(text: str, path: str, query_blocks: list[QueryBlock],
                           chunk_tokens: list[Token],
                           sink: Callable[[WatermarkUse], None]) -> Db2ParserVisitor:
    """text: the file's full source text (window_expression is sliced from
    it by character offset). path: the file being scanned, stamped onto
    each row. query_blocks: the chunk's own QueryBlocks, for resolving a
    qualified watermark column to its owning table (see
    table_scan.resolve_qualifier). chunk_tokens: the chunk's own token
    slice, backing the token-scan fallback that scopes predicates inside a
    statement the grammar couldn't parse whole (see clause_starts). sink:
    called once per watermark predicate occurrence, not pre-deduplicated --
    same convention as every other extraction visitor's sink."""
    return _WatermarkVisitor(text, path, query_blocks,
                             clause_starts(chunk_tokens), sink)


def write_watermarks_tsv(path: str, rows: list[WatermarkUse]) -> None:
    """One row per watermark predicate occurrence -- same file/line-
    attributed convention as refs_tables.tsv/refs_columns.tsv/
    refs_functions.tsv/refs_relations.tsv, and the same TSV conventions as
    tsv.write_refs_tsv (utf-8-sig, tab-separated, header row always
    written even for an empty `rows` list). A conditional window's several
    candidate sizes render as one '; '-joined window_size cell."""
    write_refs_tsv(path, ["schema", "table", "watermark_column", "operator", "base",
                          "window_expression", "window_size", "pattern", "file", "line"], rows)
