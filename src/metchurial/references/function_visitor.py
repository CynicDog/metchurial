# -*- coding: utf-8 -*-
"""DB2 function-call and predicate-operator usage extraction
(--extract-metadata).

Walks two kinds of node in the parsed tree, both feeding the same
refs_functions.tsv (function/operator name, its operands' raw source text,
file, line):

1. `function_invocation` (`function_name '(' all_distinct? arg_list? ')'`)
   -- ordinary function calls like SUBSTR(...)/UPPER(...) and zero-argument
   calls like NOW().
2. `predicate` -- comparison operators (=, <>, <, >, <=, >=) and the
   common keyword predicates (IN/NOT IN, BETWEEN/NOT BETWEEN, LIKE/NOT
   LIKE, IS [NOT] NULL), classified via src.parsing.predicates.classify_predicate
   (see that module for how the grammar's flat PredicateContext is
   disambiguated).

All source text (argument lists, operands) is sliced straight from the
original file text by character offset, not reconstructed via ANTLR's
getText() (which glues tokens together with no whitespace) -- so it
reads exactly as written. Nested calls/predicates (e.g. inside a
subquery, or SUBSTR(UPPER(col1), 1, 3)) each get their own row, since
visitChildren keeps walking into every subtree.

Known limitations, all consequences of the vendored grammar rather than
this visitor:

1. Common built-in names that are reserved lexer tokens (COUNT, MAX,
   LOWER, CONCAT, LENGTH, VALUE, CHAR, DATE, TIME, TIMESTAMP, DECIMAL,
   INT, INTEGER, REPLACE) parse via `function_name`'s explicit
   alternatives; reserved names with an expression-position grammar role
   of their own (EXISTS, CAST, YEAR/MONTH/DAY/... labeled durations)
   still have no function-call parse path.
2. A schema-qualified call (`myschema.myfunc(x)`) has the same gap as
   schema-qualified table names elsewhere in this tool (see
   table_scan.py's module docstring) -- `function_name` is always a
   single unqualified identifier, so the schema-qualifier and the dot
   aren't consumed by function_invocation at all. Still open, tracked in
   issue #1.
3. Only the common predicate forms above are captured. EXISTS,
   ARRAY_EXISTS, JSON_EXISTS, REGEXP_LIKE, OVERLAPS, `IS [NOT] (TRUE |
   FALSE)`, `IS [NOT] DISTINCT FROM`, cursor `IN (FOUND | OPEN)`, and the
   dynamic-type-check predicates are deliberately out of scope -- rare in
   practice, and each would need its own operand-extraction logic for
   comparatively little value.
"""

from __future__ import annotations

from typing import Any, Callable

from metchurial._generated.Db2Parser import Db2Parser
from metchurial._generated.Db2ParserVisitor import Db2ParserVisitor

from metchurial.parsing.predicates import COMPARISON_OPS, classify_predicate


def _slice(text: str, ctx: Any) -> str:
    return text[ctx.start.start:ctx.stop.stop + 1]


def _predicate_operands(text: str, ctx: Db2Parser.PredicateContext, op: str) -> list[str]:
    exprs = ctx.expression()
    if op in COMPARISON_OPS:
        return [_slice(text, exprs[0]), _slice(text, exprs[1])]
    if op in ("BETWEEN", "NOT BETWEEN"):
        # expression NOT? BETWEEN expression AND expression -- all three
        # come back from the generic expression() accessor, in source
        # order: the tested value, then the lower and upper bounds.
        return [_slice(text, e) for e in exprs]
    if op in ("LIKE", "NOT LIKE"):
        parts = [_slice(text, ctx.me), _slice(text, ctx.pe)]
        if ctx.ee is not None:
            parts.append(_slice(text, ctx.ee))
        return parts
    if op in ("IS NULL", "IS NOT NULL"):
        return [_slice(text, exprs[0])]
    if op in ("IN", "NOT IN"):
        parts = [_slice(text, ctx.e)]
        if ctx.expression_list_in_parentheses() is not None:
            parts.append(_slice(text, ctx.expression_list_in_parentheses()))
        elif ctx.fullselect_in_parentheses() is not None:
            parts.append(_slice(text, ctx.fullselect_in_parentheses()))
        return parts
    return []


class FunctionVisitor(Db2ParserVisitor):
    """text: the file's full source text (operand/argument-list text is
    sliced from it by character offset). sink: callable(name,
    parameters_text, line) -- name is a function name for a call, or an
    operator name (e.g. "=", "IN") for a predicate."""

    def __init__(self, text: str, sink: Callable[[str, str, int], None]) -> None:
        self.text = text
        self.sink = sink

    def visitFunction_invocation(self, ctx: Db2Parser.Function_invocationContext) -> Any:
        name = ctx.function_name().getText().upper()
        arg_list_ctx = ctx.arg_list()
        if arg_list_ctx is not None:
            params = self.text[arg_list_ctx.start.start:arg_list_ctx.stop.stop + 1]
        else:
            params = ""
        self.sink(name, params, ctx.start.line)
        return self.visitChildren(ctx)

    def visitPredicate(self, ctx: Db2Parser.PredicateContext) -> Any:
        op = classify_predicate(ctx)
        if op is not None:
            params = ", ".join(_predicate_operands(self.text, ctx, op))
            self.sink(op, params, ctx.start.line)
        return self.visitChildren(ctx)
