# -*- coding: utf-8 -*-
"""Walks a successfully-parsed Db2 SQL fragment (a sql_statement or a bare
search_condition, produced by statement_driver.py's tiered resync loop)
and emits (column, operator, value, line) tuples for each
sensitive-column comparison detection finding.

Grammar notes (see docs/PROVENANCE.md):

- All of =, <>, <, >, <=, >=, IN, BETWEEN, LIKE are alternatives of a
  single, unlabeled `predicate` rule (antlr/grammars-v4's sql/db2 grammar),
  so the generated PredicateContext class merges 20+ alternatives into one
  set of accessors -- which alt actually fired is determined by checking
  which accessor methods are non-None (src.parsing.predicates.classify_predicate),
  not by dispatching on subclass. Pinned by tests/test_grammar_smoke.py
  against the real generated parser.
- `expression`'s leaf alternatives (`column_name`, `constant_`) are direct
  children of ExpressionContext, with no multi-level passthrough chain to
  collapse through. as_column()/as_literal() below inspect the operand
  ExpressionContext directly, after unwrapping any redundant
  parenthesization (`'(' expression_list ')'` wrapping exactly one inner
  expression, e.g. `ACCT_ID IN (('0000001'))`) via _unwrap_parens -- a
  parenthesized single item parses as its own nested ExpressionContext,
  not as a plain Constant_Context/Column_nameContext directly.
- Subquery scoping needs no special-case code: every predicate node
  determines its own column purely from its own operands (no shared
  "current column" state), so recursing into a subquery via the normal
  visitChildren() traversal naturally can't leak the outer IN's column
  into the subquery's own comparisons, and vice versa
  (fixture 10_subquery_in_list.sql).
- This grammar has *no* parser-level path at all for two constructs:
    1. A bare `(` before a literal (`ACCT_ID ('0000001')`) -- there is no
       function-call-shaped fallback here (`expression` requires a real
       `function_invocation`, not a bare identifier immediately followed
       by a parenthesized argument); this is a hard parse failure.
    2. A double-quoted literal (`ACCT_ID = "0000079"`) -- `DOUBLE_QUOTE_ID`
       is a real lexer token but is never referenced anywhere in the
       parser grammar, so it has nowhere to be consumed at all.
  Both are handled entirely by supplementary_checks.py's Tier 3 token-scan
  fallback instead of anything in this file -- there is no visitor hook
  for either, by necessity, not by choice.
- Reported comparison operators are the raw source text, not algebraically
  normalized for the reversed ('literal' op COLUMN) case: a reversed
  '0000123' = ACCT_ID match reports operator "=", not flipped (pinned by
  tests/test_scan.py).
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from metchurial._generated.Db2Parser import Db2Parser
from metchurial._generated.Db2ParserVisitor import Db2ParserVisitor

from metchurial.parsing.predicates import COMPARISON_OPS, classify_predicate

# sink(column, operator, value, line, start_offset, end_offset)
FindingSink = Callable[[str, str, str, int, int, int], None]


def _unwrap_parens(ctx: Any) -> Any:
    """A redundant `'(' expression_list ')'` wrapping exactly one inner
    expression -- e.g. `('0000001')` as an IN-list item, or a subquery
    wrapped in an extra parens layer -- parses as its own ExpressionContext
    (LEFT_RND_BKT + expression_list + RIGHT_RND_BKT children), not as a
    direct passthrough to the inner item. Unwrap repeatedly so multiply-
    nested redundant parens (`(('0000001'))`) resolve too."""
    while (isinstance(ctx, Db2Parser.ExpressionContext)
           and ctx.expression_list() is not None
           and ctx.column_name() is None
           and ctx.constant_() is None):
        items = ctx.expression_list().expression()
        if len(items) != 1:
            return ctx  # a real multi-item tuple, e.g. (a, b) -- not a wrapper
        ctx = items[0]
    return ctx


def as_column(ctx: Any, columns: set[str]) -> str | None:
    """columns: set of upper-cased sensitive column names. Returns the
    upper-cased column name if `ctx` (an ExpressionContext) is a bare
    reference to one of them, else None. Checks both `column_name` (a
    bare, unqualified reference) and `field_reference` (`row_variable_name
    '.' field_name` -- the grammar's *separate* rule for a table/alias-
    qualified reference like `a.ACCT_ID`; column_name itself is never
    dotted), so an alias-qualified comparison is matched the same as an
    unqualified one."""
    ctx = _unwrap_parens(ctx)
    if not isinstance(ctx, Db2Parser.ExpressionContext):
        return None
    col_ctx = ctx.column_name()
    if col_ctx is not None:
        name = col_ctx.id_().getText().upper()
        return name if name in columns else None
    fref_ctx = ctx.field_reference()
    if fref_ctx is not None:
        name = fref_ctx.field_name().getText().upper()
        return name if name in columns else None
    return None


def as_literal(ctx: Any) -> tuple[str, tuple[int, int]] | None:
    """Returns (value, (start_offset, end_offset)) -- the literal's raw
    source text (quotes included) plus its exact 0-based
    inclusive-inclusive character span in the original source -- if `ctx`
    (an ExpressionContext) resolves to a hardcoded constant, else None. A
    bare unquoted identifier (e.g. OTHER_COL) is never a literal. The span
    is read straight off the literal token's own start/stop (same
    convention as function_visitor.py's _slice), not reconstructed from
    getText(), so a caller can later splice/replace exactly this span in
    the original file text without disturbing anything else (e.g. for
    masking)."""
    ctx = _unwrap_parens(ctx)
    if not isinstance(ctx, Db2Parser.ExpressionContext):
        return None
    const_ctx = ctx.constant_()
    if const_ctx is None:
        return None
    return const_ctx.getText(), (const_ctx.start.start, const_ctx.stop.stop)


class ExtractorVisitor(Db2ParserVisitor):

    def __init__(self, columns: Iterable[str], sink: FindingSink) -> None:
        """columns: iterable of sensitive column names (any case).
        sink: callable(column, operator, value, line, start_offset,
        end_offset) invoked once per raw finding candidate. Blank-literal
        filtering and severity/file/snippet assembly happen in engine.py,
        not here."""
        self.columns = {c.upper() for c in columns}
        self.sink = sink

    def _emit(self, column: str, operator: str, value: str, anchor_token: Any,
              span: tuple[int, int]) -> None:
        self.sink(column, operator, value, anchor_token.line, span[0], span[1])

    def visitPredicate(self, ctx: Db2Parser.PredicateContext) -> Any:
        op = classify_predicate(ctx)
        exprs = ctx.expression()

        if op in COMPARISON_OPS:
            self._handle_comparison(exprs[0], exprs[1], op)
        elif op in ("BETWEEN", "NOT BETWEEN") and len(exprs) == 3:
            self._handle_between(exprs, ctx, op)
        elif op in ("IN", "NOT IN") and len(exprs) >= 1:
            self._handle_in(exprs, ctx, op)
        elif op in ("LIKE", "NOT LIKE") and len(exprs) >= 2:
            self._handle_like(exprs, ctx, op)

        return self.visitChildren(ctx)

    def _handle_comparison(self, left: Any, right: Any, operator: str) -> None:
        left_col = as_column(left, self.columns)
        right_col = as_column(right, self.columns)
        left_lit = as_literal(left)
        right_lit = as_literal(right)
        if left_col and right_lit is not None:
            right_val, right_span = right_lit
            self._emit(left_col, operator, right_val, left.start, right_span)
        elif right_col and left_lit is not None:
            left_val, left_span = left_lit
            self._emit(right_col, operator, left_val, left.start, left_span)

    def _handle_between(self, exprs: list[Any], ctx: Db2Parser.PredicateContext,
                        operator: str) -> None:
        col = as_column(exprs[0], self.columns)
        if not col:
            return
        for value_ctx in (exprs[1], exprs[2]):
            lit = as_literal(value_ctx)
            if lit is not None:
                val, span = lit
                self._emit(col, operator, val, ctx.start, span)

    def _handle_in(self, exprs: list[Any], ctx: Db2Parser.PredicateContext,
                   operator: str) -> None:
        col = as_column(exprs[0], self.columns)
        if not col:
            return
        if ctx.fullselect_in_parentheses() is not None:
            return  # scoping: subquery's own literals are independently
                     # visited via visitChildren(), never attributed here
        parens = ctx.expression_list_in_parentheses()
        if parens is not None:
            for item in parens.expression_list().expression():
                lit = as_literal(item)
                if lit is not None:
                    val, span = lit
                    self._emit(col, operator, val, ctx.start, span)
            return
        if len(exprs) == 2:
            # bare `col IN value` (no parens) -- e.g. a collection
            # membership test; report it only if the value is a literal
            lit = as_literal(exprs[1])
            if lit is not None:
                val, span = lit
                self._emit(col, operator, val, ctx.start, span)

    def _handle_like(self, exprs: list[Any], ctx: Db2Parser.PredicateContext,
                     operator: str) -> None:
        col = as_column(exprs[0], self.columns)
        if not col:
            return
        lit = as_literal(exprs[1])
        if lit is not None:
            val, span = lit
            self._emit(col, operator, val, ctx.start, span)
