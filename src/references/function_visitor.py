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
   LIKE, IS [NOT] NULL). `predicate` is a single grammar rule with many
   alternatives sharing one flat generated context class (no per-
   alternative subclasses), so `classify_predicate` inspects which
   optional accessor is actually populated to tell them apart -- see it
   for the disambiguation details (e.g. `IN()`/`NOT()` are shared with
   the rare `... IN NOT? DISTINCT FROM ...` and cursor `IN NOT? (FOUND |
   OPEN)` alternatives, so those are explicitly excluded rather than
   misclassified as an ordinary IN).

All source text (argument lists, operands) is sliced straight from the
original file text by character offset, not reconstructed via ANTLR's
getText() (which glues tokens together with no whitespace) -- so it
reads exactly as written. Nested calls/predicates (e.g. inside a
subquery, or SUBSTR(UPPER(col1), 1, 3)) each get their own row, since
visitChildren keeps walking into every subtree.

Known limitations, all consequences of the vendored grammar rather than
this visitor (a zero-argument call like `NOW()` used to be one too --
**fixed** in issue #4 / commit 7fea4c8, which made `arg_list` optional):

1. COUNT, MAX, and LOWER are reserved keywords in vendor/grammars-v4's
   Db2Parser.g4 -- distinct lexer tokens, not the plain `ID` that
   `function_name : id_` requires -- and have no other expression/function
   rule anywhere in the grammar (confirmed empirically: `SELECT
   COUNT(col1) FROM t1;` fails to parse via function_invocation at all,
   a "no viable alternative at input 'SELECT COUNT'" syntax error, which
   pushes that whole statement chunk into the tiered driver's coarser
   resync tiers). Every other function name tested (SUBSTR, UPPER,
   COALESCE, SUM, AVG, MIN, ...) lexes as plain ID and parses normally.
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

from Db2Parser import Db2Parser
from Db2ParserVisitor import Db2ParserVisitor

_COMPARISON_OPS = frozenset(("=", "<>", "<", ">", "<=", ">="))


def _slice(text, ctx):
    return text[ctx.start.start:ctx.stop.stop + 1]


def classify_predicate(ctx):
    """Returns an operator name string for the predicate alternatives this
    visitor supports, or None for anything else (see module docstring's
    Known Limitation 4). Public: also reused by query_identity.py's
    _PredicateFactVisitor for the same shape-classification, kept here
    rather than duplicated since it only inspects `ctx`, no dependency on
    this module's own text-slicing convention."""
    exprs = ctx.expression()
    op_ctx = ctx.comparison_operator()
    if op_ctx is not None and len(exprs) == 2 and ctx.some_any_all() is None:
        return op_ctx.getText()
    if ctx.BETWEEN() is not None:
        return "NOT BETWEEN" if ctx.NOT() is not None else "BETWEEN"
    if ctx.LIKE() is not None:
        return "NOT LIKE" if ctx.NOT() is not None else "LIKE"
    if ctx.NULL_() is not None:
        return "IS NOT NULL" if ctx.NOT() is not None else "IS NULL"
    if (ctx.IN() is not None and ctx.DISTINCT() is None
            and ctx.FOUND() is None and ctx.OPEN() is None
            and ctx.cursor_variable_name() is None):
        return "NOT IN" if ctx.NOT() is not None else "IN"
    return None


def _predicate_operands(text, ctx, op):
    exprs = ctx.expression()
    if op in _COMPARISON_OPS:
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

    def __init__(self, text, sink):
        self.text = text
        self.sink = sink

    def visitFunction_invocation(self, ctx: Db2Parser.Function_invocationContext):
        name = ctx.function_name().getText().upper()
        arg_list_ctx = ctx.arg_list()
        if arg_list_ctx is not None:
            params = self.text[arg_list_ctx.start.start:arg_list_ctx.stop.stop + 1]
        else:
            params = ""
        self.sink(name, params, ctx.start.line)
        return self.visitChildren(ctx)

    def visitPredicate(self, ctx: Db2Parser.PredicateContext):
        op = classify_predicate(ctx)
        if op is not None:
            params = ", ".join(_predicate_operands(self.text, ctx, op))
            self.sink(op, params, ctx.start.line)
        return self.visitChildren(ctx)
